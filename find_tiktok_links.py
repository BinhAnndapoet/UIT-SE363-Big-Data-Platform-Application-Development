# find_tiktok_links_v3.py
import os
import time
import random
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

COOKIES_FILE = "cookies.txt"
OUTPUT_XLSX = "tiktok_links.xlsx"
OUTPUT_CSV = "tiktok_links.csv"

# --- Hashtags ---
RISKY_HASHTAGS = [
    "sexy", "gaixinh", "scandal", "nhaycam", "hotgirl", "bikini",
    "body", "dance", "leak", "phim", "dating"
]

SAFE_HASHTAGS = [
    "travel", "food", "sport", "funny", "music", "dog", "cat", "study",
    "tech", "fashion", "art", "lifehack", "game", "review", "nature"
]


def load_cookies_from_txt(driver, cookie_file):
    if not os.path.exists(cookie_file):
        print(f"⚠️ File {cookie_file} không tồn tại. Hãy export cookies.txt sau khi đăng nhập TikTok.")
        return
    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                cookie = {
                    "domain": parts[0],
                    "name": parts[5],
                    "value": parts[6],
                    "path": parts[2],
                    "secure": parts[3].upper() == "TRUE"
                }
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
    print("✅ Đã nạp cookie từ file cookies.txt.")


def init_driver(headless=False):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1200,800")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.tiktok.com")
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver


def is_logged_in(driver):
    driver.get("https://www.tiktok.com")
    time.sleep(3)
    html = driver.page_source
    return "Upload video" in html or "/logout" in html or "avatar" in html


def scroll_and_collect_links(driver, limit=100):
    seen = set()
    for _ in range(12):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(random.uniform(1, 2))
        links = [a.get_attribute("href") for a in driver.find_elements(By.TAG_NAME, "a")]
        for l in links:
            if l and "tiktok.com/@" in l:
                seen.add(l)
        if len(seen) >= limit:
            break
    return list(seen)


def collect_hashtag_links(driver, hashtags, label, limit_per_tag=100):
    collected = []
    for tag in tqdm(hashtags, desc=f"Phase ({label})"):
        print(f"\n[{label}] Đang quét hashtag: #{tag}")
        url = f"https://www.tiktok.com/tag/{tag}"
        driver.get(url)
        time.sleep(3)
        links = scroll_and_collect_links(driver, limit=limit_per_tag)
        for l in links:
            collected.append({"hashtag": tag, "link": l, "label": label})
        print(f"-> Thu được {len(links)} link từ #{tag}")
    return collected


def main():
    driver = init_driver(headless=False)
    time.sleep(2)
    load_cookies_from_txt(driver, COOKIES_FILE)
    driver.refresh()
    time.sleep(3)

    if not is_logged_in(driver):
        print("⚠️ Cảnh báo: Cookie không hợp lệ hoặc chưa đăng nhập TikTok.")
        driver.quit()
        return
    print("✅ Đã đăng nhập thành công.")

    # --- Giai đoạn 1: harmful ---
    print("\n--- GIAI ĐOẠN 1: Thu thập harmful hashtag ---")
    harmful_data = collect_hashtag_links(driver, RISKY_HASHTAGS, label="harmful", limit_per_tag=50)

    # --- Giai đoạn 2: not harmful ---
    print("\n--- GIAI ĐOẠN 2: Thu thập not_harmful hashtag ---")
    safe_data = collect_hashtag_links(driver, SAFE_HASHTAGS, label="not_harmful", limit_per_tag=40)

    # --- Gộp dữ liệu ---
    all_data = harmful_data + safe_data
    df = pd.DataFrame(all_data)

    # Cắt gọn đúng tỷ lệ yêu cầu
    df_harmful = df[df["label"] == "harmful"].sample(n=450, replace=True, random_state=42)
    df_safe = df[df["label"] == "not_harmful"].sample(n=550, replace=True, random_state=42)
    df_final = pd.concat([df_harmful, df_safe], ignore_index=True)
    df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

    # --- Xuất file ---
    df_final.to_excel(OUTPUT_XLSX, index=False)
    df_final.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"\n✅ Đã lưu {len(df_final)} dòng vào:")
    print(f"   - {OUTPUT_XLSX}")
    print(f"   - {OUTPUT_CSV}")
    print(f"   (450 harmful + 550 not_harmful)")

    driver.quit()


if __name__ == "__main__":
    main()
