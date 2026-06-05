import requests
from bs4 import BeautifulSoup
import os

# --- Configuration via Environment Variables (For Security) ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") # e.g., "@cu_eng_results"
STATE_FILE = "announced_results.txt"
URL = "http://www.results.eng.cu.edu.eg/"

def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
        response = requests.post(api_url, json=payload)
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Failed to send message: {e}")

def load_announced_results():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_announced_result(result_key):
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{result_key}\n")

def check_all_results(announced_set):
    try:
        response = requests.get(URL, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr')
        
        year_columns = {
            1: "الفرقة الأولي",
            2: "الفرقة الثانية",
            3: "الفرقة الثالثة",
            4: "الفرقة الرابعة"
        }
        
        new_releases = []

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
                
            dept_name = cells[0].get_text(strip=True)
            if "الفرقة" in dept_name or "القسم" in dept_name:
                continue
            
            for year_idx in range(1, min(5, len(cells))):
                cell = cells[year_idx]
                checkbox = cell.find('input', {'type': 'checkbox'})
                
                if checkbox:
                    year_name = year_columns.get(year_idx, f"الفرقة {year_idx}")
                    identifier = f"{dept_name} - {year_name}"
                    
                    if identifier not in announced_set:
                        new_releases.append((dept_name, year_name))
                        announced_set.add(identifier)
                        save_announced_result(identifier)
                        
        return new_releases
    except Exception as e:
        print(f"Error scanning site: {e}")
        return []

def main():
    print("Running scheduled results scan...")
    announced_set = load_announced_results()
    
    # If the history file doesn't exist yet, create an empty one
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write("")
            
    new_updates = check_all_results(announced_set)
    
    if new_updates:
        for dept, year in new_updates:
            msg = (
                f"📢 <b>نتيجة جديدة ظهرت الآن!</b>\n\n"
                f"🏢 <b>القسم:</b> {dept}\n"
                f"🎓 <b>السنة الدراسية:</b> {year}\n\n"
                f"🔗 رابط النتيجة: {URL}"
            )
            print(f"Posting update to channel: {dept} - {year}")
            send_telegram_message(msg)
    else:
        print("Scan complete. No new results found.")

if __name__ == "__main__":
    main()