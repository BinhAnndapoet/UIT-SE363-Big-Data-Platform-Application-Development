#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
find_tiktok_links_vietnam_local_gui.py
Phiên bản: Chạy trực tiếp trên Ubuntu GUI (Không qua SSH/Tailscale)
"""

import os
import time
import random
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException


# --- Exception tùy chỉnh ---
class CaptchaException(Exception):
    pass


# ---------------- CONFIG ----------------
SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
DATA_DIR = os.path.join(SCRIPT_DIR, "data_viet")
CRAWL_DIR = os.path.join(DATA_DIR, "crawl")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CRAWL_DIR, exist_ok=True)

print(f"Thư mục script (ROOT_DIR): {SCRIPT_DIR}")
COOKIES_FILE = os.path.join(SCRIPT_DIR, "cookies.txt")
OUTPUT_XLSX = os.path.join(CRAWL_DIR, "tiktok_links_full_viet.xlsx")
OUTPUT_CSV = os.path.join(CRAWL_DIR, "tiktok_links_viet.csv")
FAILED_TAGS_FILE = os.path.join(CRAWL_DIR, "failed_hashtags.txt")

# ---------------- BỘ TỪ KHÓA (FULL) ----------------
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
    "giang_hồ",
    "biến_căng",
    "check_var",
    "hỗn_chiến",
    "baoluchocduong",
    "tài_xỉu",
    "xoc_dia",
    "no_hu",
    "bắn_cá",
    "soi_kèo",
    "cho_vay",
    "bốc_bát_họ",
    "kiem_tien_online",
    "lừa_đảo",
    "app_vay_tien",
    "nhóm_kéo_tài_xỉu",
    "bay_lắc",
    "dân_chơi",
    "trà_đá_vỉa_hè",
    "nhậu_nhẹt",
    "say_ruou",
    "hut_thuoc",
    "vape_vietnam",
    "pod_chill",
    "gọi_vong",
    "xem_boi",
    "bùa_ngải",
    "kumathong",
    "tam_linh",
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
    "canh_dep",
    "hoc_tieng_anh",
    "kien_thuc",
    "meo_vat",
    "sach_hay",
    "lich_su_viet_nam",
    "phat_trien_ban_than",
    "dai_hoc",
    "sinh_vien",
    "hai_huoc",
    "vui_ve",
    "gia_dinh",
    "thu_cung",
    "meo_con",
    "cho_cung",
    "nhac_hay_moi_ngay",
    "trend_tiktok_vietnam",
]


# ---------------- FUNCTIONS ----------------
def load_cookies_from_txt(driver, cookie_file):
    if not os.path.exists(cookie_file):
        print(f"⚠️ File {cookie_file} không tồn tại.")
        return
    print(f"Đang nạp cookies từ {cookie_file}...")
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    cookie = {
                        "domain": parts[0],
                        "httpOnly": parts[1].upper() == "TRUE",
                        "path": parts[2],
                        "secure": parts[3].upper() == "TRUE",
                        "name": parts[5],
                        "value": parts[6],
                    }
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass
        print(f"✅ Đã nạp cookies xong.")
    except Exception as e:
        print(f"Lỗi nạp cookie: {e}")


def check_and_wait_for_captcha(driver):
    captcha_selectors = [
        "captcha-verify-image",
        "#captcha-verify-container",
        "iframe[src*='captcha']",
    ]
    found_captcha = False
    for sel in captcha_selectors:
        try:
            if "iframe" in sel:
                if driver.find_elements(By.CSS_SELECTOR, sel):
                    found_captcha = True
            elif "#" in sel:
                if driver.find_elements(By.CSS_SELECTOR, sel):
                    found_captcha = True
            else:
                if driver.find_elements(By.ID, sel):
                    found_captcha = True
        except:
            pass
        if found_captcha:
            break

    if found_captcha:
        print("\n" + "!" * 50)
        print("⚠️  PHÁT HIỆN CAPTCHA!")
        print("👉 Hãy giải Captcha trên cửa sổ Chrome đang mở.")
        print("👉 Sau đó quay lại đây bấm ENTER.")
        print("!" * 50 + "\n")
        # Âm thanh cảnh báo (trên Ubuntu terminal có thể nghe tiếng beep)
        print("\007")
        input(">> Đã giải xong? Bấm Enter để tiếp tục <<")
        time.sleep(3)
        check_and_wait_for_captcha(driver)


def init_driver(headless=False):
    # --- CẤU HÌNH CHO UBUNTU LOCAL GUI ---
    # Đã xóa phần hard-code IP Tailscale. Hệ điều hành tự quản lý DISPLAY.

    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Trên máy local có GPU, có thể bỏ disable-gpu nếu muốn mượt hơn,
    # nhưng để nguyên cho ổn định crawl cũng được.
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--lang=vi")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # --- CẤU HÌNH ĐƯỜNG DẪN CHROME ---
    # Đảm bảo bạn đã cài google-chrome-stable
    system_chrome_path = "/usr/bin/google-chrome"
    if os.path.exists(system_chrome_path):
        options.binary_location = system_chrome_path
    else:
        # Fallback nếu dùng chromium hoặc đường dẫn khác
        possible_paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser"]
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                options.binary_location = path
                found = True
                break
        if not found:
            print(f"❌ LỖI: Không tìm thấy Google Chrome tại {system_chrome_path}")
            print("👉 Hãy cài đặt: sudo apt install google-chrome-stable")
            return None

    if headless:
        options.add_argument("--headless=new")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Driver: {e}")
        return None

    driver.set_page_load_timeout(30)

    # Fake Geolocation VN (Quan trọng để ra content Việt)
    params = {"latitude": 10.7769, "longitude": 106.7009, "accuracy": 100}
    try:
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)
    except:
        pass

    try:
        driver.get("https://www.tiktok.com")
        stealth(
            driver,
            languages=["vi-VN", "vi"],
            vendor="Google Inc.",
            platform="Linux x86_64",  # Cập nhật cho đúng hệ điều hành Ubuntu
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except:
        pass
    return driver


def scroll_and_collect_links(driver, limit=100):
    seen = set()
    last_height = 0
    action_counter = 0
    no_new_content_strikes = 0
    max_scrolls = 25

    for _ in range(max_scrolls):
        check_and_wait_for_captcha(driver)
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(random.uniform(2.5, 4.0))

        action_counter += 1
        if action_counter % 3 == 0:
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(
                    random.randint(-50, 50), random.randint(-50, 50)
                ).perform()
            except:
                pass

        try:
            elements = driver.find_elements(By.TAG_NAME, "a")
            for elem in elements:
                l = elem.get_attribute("href")
                if l and "/video/" in l and l not in seen:
                    seen.add(l)
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if abs(new_height - last_height) < 100:
            no_new_content_strikes += 1
        else:
            no_new_content_strikes = 0
        last_height = new_height
        if no_new_content_strikes >= 3 or len(seen) >= limit:
            break
    return list(seen)


def collect_hashtag_links(
    driver, hashtags, label, output_list, failed_list, limit_per_tag=100
):
    for tag in tqdm(hashtags, desc=f"Phase ({label})", unit="tag"):
        print(f"\n[{label}] Quét: #{tag}")
        try:
            driver.get(f"https://www.tiktok.com/tag/{tag}")
            time.sleep(random.uniform(4, 7))
            check_and_wait_for_captcha(driver)
            links = scroll_and_collect_links(driver, limit=limit_per_tag)

            if not links:
                failed_list.append(tag)
                print(f"⚠️ Không có link cho #{tag}")

            for l in links:
                output_list.append({"hashtag": tag, "link": l, "label": label})

            print(f"-> {len(links)} links")
            time.sleep(random.uniform(5, 8))
        except Exception as e:
            print(f"Lỗi #{tag}: {e}")
            failed_list.append(tag)
            continue


def main():
    try:
        os.makedirs(CRAWL_DIR, exist_ok=True)
    except:
        pass

    df_existing = pd.DataFrame()
    if os.path.exists(OUTPUT_XLSX):
        try:
            df_existing = pd.read_excel(OUTPUT_XLSX)
        except:
            pass

    # --- KHỞI ĐỘNG DRIVER ---
    print("🚀 Đang khởi động Chrome trên Ubuntu Local...")
    driver = init_driver(headless=False)  # False = Hiện trình duyệt
    if driver is None:
        return

    time.sleep(2)
    load_cookies_from_txt(driver, COOKIES_FILE)
    driver.refresh()

    done_harmful = set()
    done_safe = set()
    if not df_existing.empty and "hashtag" in df_existing.columns:
        done_harmful = set(df_existing[df_existing["label"] == "harmful"]["hashtag"])
        done_safe = set(df_existing[df_existing["label"] == "not_harmful"]["hashtag"])

    remaining_risky = [t for t in RISKY_HASHTAGS if t not in done_harmful]
    remaining_safe = [t for t in SAFE_HASHTAGS if t not in done_safe]

    harmful_data_new = []
    safe_data_new = []
    failed_tags = []

    try:
        if remaining_risky:
            collect_hashtag_links(
                driver, remaining_risky, "harmful", harmful_data_new, failed_tags
            )
        if remaining_safe:
            collect_hashtag_links(
                driver, remaining_safe, "not_harmful", safe_data_new, failed_tags
            )
    except KeyboardInterrupt:
        print("\n⚠️ User Stopped.")
    finally:
        print("\n--- Saving ---")
        df_new = pd.DataFrame(harmful_data_new + safe_data_new)
        if not df_new.empty:
            all_df = pd.concat([df_existing, df_new], ignore_index=True)
            all_df = all_df.drop_duplicates(subset=["link"], keep="last")
            try:
                all_df.to_excel(OUTPUT_XLSX, index=False)
                all_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
                print(f"💾 Saved {len(all_df)} rows.")
            except Exception as e:
                print(f"Lỗi lưu file: {e}")

        if failed_tags:
            with open(FAILED_TAGS_FILE, "a", encoding="utf-8") as f:
                f.write("\n".join(failed_tags) + "\n")

        driver.quit()


if __name__ == "__main__":
    main()
