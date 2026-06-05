import os
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STATE_FILE = "announced_results.txt"
URL = "http://www.results.eng.cu.edu.eg/"

def send_telegram_message(text):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(api_url, json=payload)

async def main():
    print("بدء عملية الفحص باستخدام متصفح حقيقي...")
    
    # تحميل الذاكرة السابقة
    previous_results = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous_results = set(line.strip() for line in f if line.strip())

    # فتح المتصفح
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(URL, timeout=60000, wait_until="networkidle")
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"فشل تحميل الصفحة: {e}")
            return
        finally:
            await browser.close()

    rows = soup.find_all('tr')
    current_visible_results = set()
    new_releases = []
    
    # تحليل البيانات
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

    # التبليغ
    if new_releases:
        print(f"تم العثور على {len(new_releases)} نتائج جديدة!")
        for res in new_releases:
            send_telegram_message(f"📢 <b>نتيجة جديدة:</b>\n{res}\n\n🔗 {URL}")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            for item in sorted(current_visible_results): f.write(f"{item}\n")
    else:
        print("لا توجد نتائج جديدة.")

if __name__ == "__main__":
    asyncio.run(main())
