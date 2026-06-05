import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "announced_results.txt"
URL = "http://www.results.eng.cu.edu.eg/"

def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(api_url, json=payload)

def main():
    print("Starting stealth scan...")
    # These headers make the request look like a real Chrome browser on Windows
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Referer": "http://www.google.com/"
    }
    
    try:
        # Direct request with stealth headers
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    rows = soup.find_all('tr')
    # [Rest of your extraction logic remains the same]
    previous_results = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_results = set(line.strip() for line in f if line.strip())

    current_visible_results = set()
    new_releases = []
    year_columns = {1: "الفرقة الأولي", 2: "الفرقة الثانية", 3: "الفرقة الثالثة", 4: "الفرقة الرابعة"}
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < 2: continue
        dept_name = cells[0].get_text(strip=True)
        if "الفرقة" in dept_name or "القسم" in dept_name: continue
        
        for year_idx in range(1, min(5, len(cells))):
            if cells[year_idx].find('input', {'type': 'checkbox'}):
                identifier = f"{dept_name} - {year_columns.get(year_idx, 'الفرقة ' + str(year_idx))}"
                current_visible_results.add(identifier)
                if identifier not in previous_results:
                    new_releases.append(identifier)

    if new_releases:
        for res in new_releases:
            send_telegram_message(f"📢 <b>New Result:</b>\n{res}\n\n🔗 {URL}")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            for item in sorted(current_visible_results): f.write(f"{item}\n")
    else:
        print("Scan complete. No new results found.")

if __name__ == "__main__":
    main()
