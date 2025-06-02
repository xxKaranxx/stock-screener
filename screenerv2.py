import time
import json
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# 🔧 Replace with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = "7980669720:AAGzcJfCGAYo3Bship6JBxDjyDgrqTriilw"
TELEGRAM_CHAT_ID = "1943787028"
LAST_DATA_FILE = "last_data.json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def scrape_chartink_stocks(url, category_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    stock_data = []

    try:
        driver.get(url)
        time.sleep(3)

        run_scan_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Run Scan') or contains(@class, 'run-scan') or contains(@id, 'run-scan')]"))
        )
        driver.execute_script("arguments[0].click();", run_scan_button)
        time.sleep(5)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "DataTables_Table_0"))
        )
        rows = driver.find_elements(By.CSS_SELECTOR, "#DataTables_Table_0 tbody tr")

        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) >= 7:
                data = {
                    'col2': cells[1].text.strip(),
                    'col5': cells[4].text.strip(),
                    'col6': cells[5].text.strip(),
                    'col7': cells[6].text.strip()
                }
                stock_data.append(data)

        return stock_data

    except Exception as e:
        print(f"Error scraping {category_name}: {str(e)}")
        return []

    finally:
        driver.quit()

def load_last_data():
    if os.path.exists(LAST_DATA_FILE):
        with open(LAST_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_current_data(data):
    with open(LAST_DATA_FILE, "w") as f:
        json.dump(data, f)

def detect_changes(old_data, new_data):
    return json.dumps(old_data, sort_keys=True) != json.dumps(new_data, sort_keys=True)

def shorten_volume(value):
    try:
        num = float(value.replace(',', '').replace('%', '').strip())
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.0f}K"
        else:
            return str(int(num))
    except:
        return value

def format_telegram_message(changes):
    lines = ["📊 *Stock Screener Update*"]

    for category, entries in changes.items():
        lines.append(f"\n🔹 *{category}* ({len(entries)} stocks)")

        if not entries:
            lines.append("_No results found_")
            continue

        lines.append("`Symbol     | Price   | %Chg   | Volume `")
        lines.append("`-----------|---------|--------|--------`")

        for e in entries:
            sym = e['col2'][:10].ljust(10)
            price = e['col5'].rjust(7)
            change = e['col6'].rjust(6)
            volume = shorten_volume(e['col7']).rjust(6)
            lines.append(f"`{sym} | {price} | {change} | {volume} `")

    return "\n".join(lines)

def main():
    urls = {
        "Intraday-95%": "https://chartink.com/screener/copy-nks-best-buy-stocks-for-intraday-2",
        "Intraday-100%": "https://chartink.com/screener/copy-morning-scanner-for-buy-nr7-based-breakout-8"
    }

    print("Checking stock screeners for updates...")

    current_data = {}
    for category, url in urls.items():
        data = scrape_chartink_stocks(url, category)
        current_data[category] = data

    last_data = load_last_data()

    if detect_changes(last_data, current_data):
        print("🔔 Change detected! Sending Telegram update.")
        message = format_telegram_message(current_data)
        send_telegram_message(message)
        save_current_data(current_data)
    else:
        print("No change detected.")

if __name__ == "__main__":
    main()
