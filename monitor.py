import requests
from bs4 import BeautifulSoup
import os

# --- Configuration via Environment Variables ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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

def save_all_announced_results(announced_set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for item in sorted(announced_set):
            f.write(f"{item}\n")

def main():
    print("Running smart results monitor...")
    
    # 1. Load historical memory
    previous_results = load_announced_results()
    
    # 2. Scrape the website (Updated with Headers and 60s Timeout)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        print("Connecting to the university portal...")
        response = requests.get(URL, headers=headers, timeout=60)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr')
    except Exception as e:
        print(f"Error fetching or parsing the website: {e}")
        return

    year_columns = {
        1: "الفرقة الأولي",
        2: "الفرقة الثانية",
        3: "الفرقة الثالثة",
        4: "الفرقة الرابعة"
    }
    
    current_visible_results = set()
    new_releases = []

    # 3. Parse the table structure
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
                current_visible_results.add(identifier)
                
                if identifier not in previous_results:
                    new_releases.append((dept_name, year_name))

    # --- CRITICAL LOGIC CHECKS ---

    # CONDITION 1: Portal Reset Detected
    if len(current_visible_results) == 0 and len(previous_results) > 0:
        print("Portal reset detected! All checkboxes were removed by the faculty.")
        reset_msg = (
            "🔄 <b>تم تحديث صفحة النتائج</b>\n\n"
            "❌ تم مسح علامات نتائج الترم السابق من المنصة.\n"
            "⏳ الموقع الآن جاهز وفي انتظار رفع نتائج الترم الحالي. بالتوفيق للجميع! \n\n"
            f"🔗 تابع هنا: {URL}"
        )
        send_telegram_message(reset_msg)
        
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return

    # CONDITION 2: New Results Found (or initial setup test run)
    if new_releases:
        if len(previous_results) == 0:
            print(f"Initial run test: Found {len(new_releases)} existing results. Sending summary batch...")
            
            batch_size = 15
            for i in range(0, len(new_releases), batch_size):
                batch = new_releases[i:i+batch_size]
                summary_lines = [f"• {dept} ({year})" for dept, year in batch]
                
                msg = (
                    f"🚀 <b>تم تحديث صفحة النتائج</b>\n"
                    f"النتائج المتوفرة حالياً على الموقع:\n\n"
                    + "\n".join(summary_lines) +
                    f"\n\n🔗 رابط المنصة: {URL}"
                )
                send_telegram_message(msg)
        else:
            print(f"Found {len(new_releases)} brand new results!")
            for dept, year in new_releases:
                msg = (
                    f"📢 <b>تم تحديث صفحة النتائج</b>\n\n"
                    f"🏢 <b>القسم:</b> {dept}\n"
                    f"🎓 <b>السنة الدراسية:</b> {year}\n\n"
                    f"🔗 رابط النتيجة: {URL}"
                )
                send_telegram_message(msg)

        save_all_announced_results(current_visible_results)
    else:
        print("Scan complete. No changes on the portal.")

if __name__ == "__main__":
    main()
