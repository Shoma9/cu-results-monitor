import os
import requests
from bs4 import BeautifulSoup

# Setup
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "announced_results.txt"
TARGET_URL = "http://www.results.eng.cu.edu.eg/"

# ZenRows API settings for firewall bypass
ZENROWS_API_KEY = "8f03104e76d915442e0539f170f7cf4a3055452d"
ZENROWS_URL = f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}&url={TARGET_URL}&js_render=true&premium_proxy=true"

def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(api_url, json=payload)

def main():
    print("Starting secure bypass scan...")
    try:
        # Fetching via proxy
        response = requests.get(ZENROWS_URL, timeout=90)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Bypass failed: {e}")
        return

    # Load history
    previous_results = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_results = set(line.strip() for line in f if line.strip())

    current_visible_results = set()
    new_releases = []
    year_columns = {1: "الفرقة الأولي", 2: "الفرقة الثانية", 3: "الفرقة الثالثة", 4: "الفرقة الرابعة"}
    
    # Parse table
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 2: continue
        dept_name = cells[0].get_text(strip=True)
        if "الفرقة" in dept_name or "القسم" in dept_name: continue
        
        for year_idx in range(1, min(5, len(cells))):
            if cells[year_idx].find('input', {'type': 'checkbox'}):
                identifier = f"{dept_name} - {year_columns.get(year_idx, f'الفرقة {year_idx}')}"
                current_visible_results.add(identifier)
                if identifier not in previous_results:
                    new_releases.append(identifier)

    # Notify and Save
    if new_releases:
        print(f"Found {len(new_releases)} new results!")
        for res in new_releases:
            send_telegram_message(f"📢 <b>New Result Announced:</b>\n{res}\n\n🔗 {TARGET_URL}")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            for item in sorted(current_visible_results): f.write(f"{item}\n")
    else:
        print("Scan complete. No new results found.")

if __name__ == "__main__":
    main()
