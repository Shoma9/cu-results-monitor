import requests
from bs4 import BeautifulSoup
import os
import time
import random

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

def fetch_with_proxy(proxy_format, headers):
    # إضافة رقم عشوائي لكسر الـ Cache وإجبار البروكسي على جلب نسخة جديدة
    cache_buster = f"?nocache={random.randint(10000, 99999)}"
    target_url = URL + cache_buster
    proxy_url = proxy_format.replace("TARGET_URL", target_url)
    
    response = requests.get(proxy_url, headers=headers, timeout=60)
    response.raise_for_status() 
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.find_all('tr')
    
    if len(rows) < 2:
        raise ValueError(f"Fetched page but found no data tables. (Found {len(rows)} rows)")
    
    print(f"Successfully fetched {len(rows)} rows using proxy!")
    return rows

def main():
    print("Running smart results monitor...")
    previous_results = load_announced_results()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    rows = []
    
    # 3 مسارات بديلة لتخطي جدار الكلية
    proxies = [
        "https://api.allorigins.win/raw?url=TARGET_URL",
        "https://api.codetabs.com/v1/proxy?quest=TARGET_URL",
        "https://corsproxy.io/?TARGET_URL"
    ]
    
    success = False
    for i, proxy in enumerate(proxies):
        print(f"Attempting bypass route {i+1}...")
        try:
            rows = fetch_with_proxy(proxy, headers)
            success = True
            break
        except Exception as e:
            print(f"Route {i+1} failed: {e}")
            
    if not success:
        print("All proxy routes failed. The university site might be completely down or heavily blocking.")
        return

    year_columns = {
        1: "الفرقة الأولي",
        2: "الفرقة الثانية",
        3: "الفرقة الثالثة",
        4: "الفرقة الرابعة"
    }
    
    current_visible_results = set()
    new_releases = []

    # Parse the table structure
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

    # سجل دقيق لما يراه السكربت
    print(f"Found {len(current_visible_results)} total checkboxes on the current page.")

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
