import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "announced_results.txt"
# تم تحديث الرابط لاستخدام ScraperAPI المجاني
SCRAPER_API_KEY = "4223d70638541e4d6a455a297e681c2d"
TARGET_URL = "http://www.results.eng.cu.edu.eg/"
API_URL = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={TARGET_URL}"

def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(api_url, json=payload)

def main():
    print("جاري الفحص عبر خدمة ScraperAPI...")
    try:
        response = requests.get(API_URL, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"فشل الاتصال عبر API: {e}")
        return

    rows = soup.find_all('tr')
    previous_results = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_results = set(line.strip() for line in f if line.strip())

    current_visible_results = set()
    new_releases = []
    
    # تحليل الجدول (نفس المنطق القوي السابق)
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
        print(f"تم العثور على {len(new_releases)} نتائج جديدة!")
        for res in new_releases:
            send_telegram_message(f"📢 <b>نتيجة جديدة:</b>\n{res}\n\n🔗 {TARGET_URL}")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            for item in sorted(current_visible_results): f.write(f"{item}\n")
    else:
        print("الفحص اكتمل. لا توجد نتائج جديدة.")

if __name__ == "__main__":
    main()
