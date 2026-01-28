# -*- coding: utf-8 -*-
"""
crawler_links.py
Phiên bản: Full Data (Link + Caption/Text)
"""

import os
import time
import random
import csv
import json
import gzip
import sys
import psycopg2
import itertools
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

# webdriver_manager imported conditionally in init_driver() for fallback only
import config

# --- CONFIG DB ---
DB_CONFIG = {
    "dbname": "tiktok_safety_db",
    "user": "user",
    "password": "password",
    "host": "postgres",
    "port": "5432",
}

COOKIES_FILE = "/opt/project/streaming/ingestion/cookies.txt"
OUTPUT_CSV = config.INPUT_CSV_PATH

# --- DANH SÁCH HASHTAG (FULL) ---
RISKY_HASHTAGS = [
    "gaixinh",
    "gái_xinh_tiktok",
    "nhay_sexy",
    "khoe_body",
    "bikini_vietnam",
    "sugarbaby",
    "sgbb",
    "phong_the",
    "chuyen_nguoi_lon",
    "danh_nhau",
    "đánh_ghen",
    "boc_phot",
    "bóc_phốt",
    "drama_showbiz",
    "xăm_trổ",
    "chửi_bậy",
]

SAFE_HASHTAGS = [
    "review_an_uong",
    "mon_ngon_moi_ngay",
    "com_nha",
    "pho_viet_nam",
    "streetfood_vietnam",
    "cafe_vietnam",
    "an_cung_tiktok",
    "nauan",
    "du_lich_viet_nam",
    "vietnam_travel",
    "hanoi",
    "saigon",
    "dalat",
    "hoc_tieng_anh",
    "kien_thuc",
    "meo_vat",
    "sach_hay",
    "thu_cung",
]


def log_to_db(message, level="INFO"):
    print(f"[{level}] {message}", flush=True)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO system_logs (dag_id, task_name, log_level, message) VALUES (%s, %s, %s, %s)",
            ("1_TIKTOK_ETL_COLLECTOR", "crawler_api", level, message),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def init_driver():
    log_to_db("🔧 Khởi tạo Browser (Non-Headless API Mode)...")
    options = Options()

    # Giữ Non-Headless để TikTok trả JSON
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--blink-settings=imagesEnabled=false")  # Tắt ảnh cho nhẹ

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        seleniumwire_options = {"disable_encoding": True}
        # Use system chromedriver instead of webdriver-manager (avoids path issues in Docker)
        chromedriver_path = "/usr/local/bin/chromedriver"
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            log_to_db(f"✅ Using system chromedriver: {chromedriver_path}", "INFO")
        else:
            # Fallback to webdriver-manager for local development
            from webdriver_manager.chrome import ChromeDriverManager

            service = Service(ChromeDriverManager().install())
            log_to_db("⚠️ Using webdriver-manager (fallback)", "WARNING")
        driver = webdriver.Chrome(
            service=service, options=options, seleniumwire_options=seleniumwire_options
        )
        stealth(
            driver,
            languages=["vi-VN", "vi", "en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        return driver
    except Exception as e:
        log_to_db(f"❌ Lỗi Driver: {e}", "ERROR")
        return None


def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        log_to_db("⚠️ KHÔNG TÌM THẤY COOKIES!", "ERROR")
        return False

    log_to_db("🍪 Đang nạp cookies...")
    try:
        driver.get("https://www.tiktok.com/")
        time.sleep(3)
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if line.strip().startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    try:
                        driver.add_cookie(
                            {
                                "domain": ".tiktok.com",
                                "name": parts[5],
                                "value": parts[6],
                                "path": "/",
                            }
                        )
                        count += 1
                    except:
                        pass
        log_to_db(f"✅ Đã nạp {count} cookies.", "INFO")
        driver.refresh()
        time.sleep(5)
        return True
    except Exception as e:
        log_to_db(f"❌ Lỗi cookie: {e}", "ERROR")
        return False


def warmup_session(driver):
    log_to_db("🔥 Warm-up session...", "INFO")
    try:
        driver.execute_script("window.scrollBy(0, 500)")
        time.sleep(random.uniform(2, 4))
        driver.get("https://www.tiktok.com/search?q=trending")
        time.sleep(random.uniform(3, 5))
        log_to_db("✅ Warm-up hoàn tất.", "INFO")
    except:
        pass


def save_csv(tag, videos, label):
    """
    videos: list of dict {'link': str, 'desc': str}
    """
    try:
        mode = "a" if os.path.exists(OUTPUT_CSV) else "w"
        # Dùng utf-8-sig để Excel đọc được tiếng Việt
        with open(OUTPUT_CSV, mode=mode, newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Ghi header nếu file mới
            if mode == "w":
                writer.writerow(["hashtag", "link", "description", "label"])

            for v in videos:
                # Làm sạch description (xóa xuống dòng để tránh vỡ CSV)
                clean_desc = v["desc"].replace("\n", " ").replace("\r", " ")
                writer.writerow([tag, v["link"], clean_desc, label])
    except Exception as e:
        log_to_db(f"Lỗi ghi CSV: {e}", "ERROR")


def intercept_api_data(driver, tag, label):
    log_to_db(f"📡 Đang lắng nghe API cho #{tag}...", "INFO")
    del driver.requests

    try:
        driver.get(f"https://www.tiktok.com/tag/{tag}")
    except:
        return  # Bỏ qua nếu load lỗi

    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(random.uniform(2, 4))

    found_videos = []  # Chứa dict {'link':..., 'desc':...}

    log_to_db("⏳ Đang đợi phản hồi từ API...", "INFO")
    start_wait = time.time()

    while time.time() - start_wait < 15:
        for request in driver.requests:
            if request.response and "item_list" in request.url:
                try:
                    body = request.response.body
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except:
                        continue

                    if "itemList" in data:
                        for item in data["itemList"]:
                            vid_id = item.get("id")
                            author = item.get("author", {})
                            author_id = author.get("uniqueId")

                            # [MỚI] Lấy caption text
                            desc = item.get("desc", "")

                            if vid_id and author_id:
                                full_link = f"https://www.tiktok.com/@{author_id}/video/{vid_id}"

                                # Lưu cả link và description
                                found_videos.append({"link": full_link, "desc": desc})
                except Exception:
                    pass

        # Lọc trùng lặp dựa trên link
        unique_videos = {v["link"]: v for v in found_videos}.values()

        if len(unique_videos) > 5:
            break
        time.sleep(1)

    unique_list = list({v["link"]: v for v in found_videos}.values())

    if unique_list:
        save_csv(tag, unique_list, label)
        log_to_db(
            f"🎉 TỔNG KẾT: Lấy được {len(unique_list)} video (có Text) cho #{tag}",
            "INFO",
        )
    else:
        log_to_db(f"⚠️ Không bắt được API nào cho #{tag}.", "WARN")


def main():
    try:
        os.makedirs(config.CRAWL_DIR, exist_ok=True)
    except:
        pass

    driver = init_driver()
    if not driver:
        sys.exit(1)

    if load_cookies(driver):
        warmup_session(driver)
        log_to_db("🚀 Bắt đầu chiến dịch Streaming...", "INFO")
        start_time = time.time()
        count = 0

        for r, s in itertools.zip_longest(RISKY_HASHTAGS, SAFE_HASHTAGS):
            if r:
                intercept_api_data(driver, r, "harmful")
                time.sleep(random.uniform(8, 12))
                count += 1
            if s:
                intercept_api_data(driver, s, "safe")
                time.sleep(random.uniform(8, 12))
                count += 1

            # Restart sau 45 phút
            if time.time() - start_time > 2700:
                log_to_db("♻️ Restart Browser...", "INFO")
                driver.quit()
                time.sleep(5)
                driver = init_driver()
                load_cookies(driver)
                warmup_session(driver)
                start_time = time.time()

            if count % 4 == 0:
                log_to_db("☕ Nghỉ 15s...", "INFO")
                time.sleep(15)

    driver.quit()
    log_to_db("🏁 Hoàn tất phiên làm việc.", "INFO")


if __name__ == "__main__":
    main()
