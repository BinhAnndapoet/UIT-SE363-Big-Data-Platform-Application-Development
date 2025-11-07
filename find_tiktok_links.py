#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
find_tiktok_links_v3_10.py

Nâng cấp từ v3.9:
- FIX 4 (Bị CAPTCHA): Script vẫn bị dính CAPTCHA xoay hình.
- GIẢI PHÁP 1: Thêm cơ chế nhận diện CAPTCHA. Nếu thấy,
  script sẽ tự động "ngủ" 5 phút (300s) rồi bỏ qua tag đó.
- GIẢI PHÁP 2: Tăng đáng kể thời gian nghỉ giữa các hashtag
  (từ 3-7s lên 15-45s) để giảm Rate Limiting.

YÊU CẦU:
- Đặt cookies.txt (Netscape cookie file, export từ Chrome khi đã login) trong cùng thư mục
- Cài dependencies:
  pip install selenium webdriver-manager selenium-stealth pandas tqdm openpyxl
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


# ---------------- CONFIG ----------------
# --- NÂNG CẤP (v3.11): Tự động tìm đường dẫn ---
# Lấy đường dẫn tuyệt đối của file script này
SCRIPT_PATH = os.path.realpath(__file__)
# Lấy thư mục chứa file script (vd: .../-UIT-_SE363-Big-Data-Platform-Application-Development)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
# Tạo đường dẫn đến thư mục data/crawl
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CRAWL_DIR = os.path.join(DATA_DIR, "crawl")

print(f"Thư mục script (ROOT_DIR): {SCRIPT_DIR}")
print(f"Thư mục lưu data (CRAWL_DIR): {CRAWL_DIR}")

# --- Cập nhật đường dẫn file ---
COOKIES_FILE = os.path.join(SCRIPT_DIR, "cookies.txt") # cookies.txt vẫn ở thư mục gốc
OUTPUT_XLSX = os.path.join(CRAWL_DIR, "tiktok_links_full.xlsx")
OUTPUT_CSV = os.path.join(CRAWL_DIR, "tiktok_links.csv")
CAPTCHA_SLEEP_SECONDS = 120 # Ngủ 2 phút nếu bị CAPTCHA

# --- Harmful Hashtags (Cập nhật v3.7 - Loại bỏ tag cấm, thêm tiếng lóng) ---
RISKY_HASHTAGS = [
    # 1. Nội dung nhạy cảm / Gợi dục (Sexual / Suggestive)
    # (Đây là các tag "vùng xám" hiệu quả, có nhiều video)
    "sexy", "bikini", "body", "nhaycam", "18plus", "gáixinh", "gai18", 
    "lingerie", "kiss", "flirt", "seductive",
    
    # 2. Bạo lực / Tội phạm / Chất kích thích (Violence / Crime / Drugs)
    # (Đã bỏ tag cấm như drugs, ma_túy, gun, knife)
    # Thay bằng tiếng lóng và các từ lách luật:
    "bạo_lực", "đánh_nhau", "phóng_lợn", # Bạo lực (tiếng lóng)
    "gianghomang", "đòi_nợ", "tín_dụng_đen", # Tội phạm / XHĐen
    "bay_lắc", "podchill", # Chất kích thích (tiếng lóng)
    "smoking", "rượu", # Các tag này rộng nhưng vẫn có rủi ro
    
    # 3. Tiêu cực / Lừa đảo / Tin giả (Toxic / Scam / Fake)
    # (Đây là các tag "vùng xám" rất tốt)
    "lừa_đảo", "chửi", "toxic", "bóc_phốt", "drama", "chửi_thề", "fakenews", "scandal",
    
    # 4. Văn hóa nhạy cảm / Mê tín
    # (Đã bỏ tag quá rộng như 'tâm linh', 'phong thủy')
    "mê_tín_dị_đoan", "bói_toán", "xem_bói", "bói_bài", "hầu_đồng", "gọi_hồn", 
    
    # 5. Thử thách / Giải trí tiêu cực (Risky Entertainment)
    "reactiondrama", "troll", "shockcontent", "weirdchallenge", "darkhumor", "thuthach"
]

# --- Not harmful Hashtags (đã phân loại rõ) ---
# (List này đã rất tốt và SFW, giữ nguyên)
SAFE_HASHTAGS = [
    # 1. Sở thích & Giải trí (Hobbies & Entertainment)
    "travel", "food", "sport", "funny", "music", "game", "review", "nature", 
    "diy", "makeup", "car", "comedy", "art", "plant", "garden", "travelvlog", 
    "reviewphim", "ancungtiktok", "thethao",
    
    # 2. Động vật (Pets)
    "dog", "cat", "pet", "thucung", # Sửa 'thuycung' thành 'thucung' cho chính xác
    
    # 3. Giáo dục & Phát triển (Education & Development)
    "study", "tech", "lifehack", "learning", "motivation", "book", "education", 
    "healthy", "recipe", "coding", "science", "reading", "inspiration", "selfcare", 
    "quotes", "sachhay", "congnghe", "hocvanchia", "nauan",
    
    # 4. Đời sống & Xã hội (Lifestyle & Social)
    "fashion", "fitness", "family", "meditation", "volunteer", "environment", "giadinh"
]


# ---------------- FUNCTIONS ----------------
def load_cookies_from_txt(driver, cookie_file):
    """Đọc file Netscape cookies.txt và nạp vào driver."""
    # ... (Không thay đổi) ...
    if not os.path.exists(cookie_file):
        print(f"⚠️ File {cookie_file} không tồn tại. Hãy export cookies.txt sau khi đăng nhập TikTok.")
        return
    
    print(f"Đang nạp cookies từ {cookie_file}...")
    count = 0
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
                    cookie["expiry"] = int(parts[4])
                except (ValueError, IndexError):
                    pass 

                try:
                    driver.add_cookie(cookie)
                    count += 1
                except Exception:
                    pass
    print(f"✅ Đã nạp {count} cookie.")


def init_driver(headless=False):
    """Khởi tạo Chrome Driver với selenium-stealth."""
    # ... (Không thay đổi) ...
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--mute-audio")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if headless:
        print("Chạy ở chế độ Headless...")
        options.add_argument("--headless=new")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        print(f"Lỗi khi khởi tạo WebDriver: {e}")
        print("Thử cập nhật Chrome hoặc chromedriver.")
        return None

    # --- FIX 3 (v3.9) ---
    # Đặt giới hạn thời gian tải trang là 20 giây
    driver.set_page_load_timeout(20)

    try:
        # Tải trang ban đầu (cũng áp dụng timeout 20s)
        driver.get("https://www.tiktok.com") 
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except TimeoutException:
        print("Cảnh báo: Tải trang ban đầu (tiktok.com) mất quá 20 giây.")
        driver.execute_script("window.stop();") # Ngừng tải
    except Exception as e:
        print(f"Cảnh báo: Không thể áp dụng selenium-stealth: {e}")
        
    return driver


def is_logged_in(driver):
    """Kiểm tra đăng nhập bằng cách tìm các dấu hiệu của user đã login."""
    # ... (Không thay đổi) ...
    print("Đang kiểm tra trạng thái đăng nhập...")
    
    # --- FIX 3 (v3.9) ---
    # Bắt lỗi nếu trang 'foryou' tải quá 20 giây
    try:
        driver.get("https://www.tiktok.com/foryou")
    except (TimeoutException, WebDriverException):
        print("Cảnh báo: Tải trang 'foryou' quá 20 giây. Tiếp tục kiểm tra...")
        # Cố gắng dừng việc tải trang và tiếp tục
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass

    # Vẫn chờ 3-5s để các element (nếu có) render
    time.sleep(3 + random.uniform(1, 2))
    
    try:
        avatar_selectors = [
            "[data-e2e='header-avatar']", 
            "img[data-e2e='nav-avatar']", 
            "header [type='button'] img[src*='avatar']"
        ]
        for selector in avatar_selectors:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                print("-> Đã tìm thấy Avatar (Đã đăng nhập).")
                return True
                
        html = driver.page_source
        if "Upload" in html or "/logout" in html or "View profile" in html:
             print("-> Đã tìm thấy text 'Upload/Logout' (Đã đăng nhập).")
             return True
             
    except Exception as e:
        print(f"Lỗi khi kiểm tra đăng nhập: {e}")
        
    print("-> Không tìm thấy dấu hiệu đăng nhập (Chưa đăng nhập).")
    return False


def scroll_and_collect_links(driver, limit=100):
    """Cuộn trang và thu thập các link có chứa 'tiktok.com/@' (link profile/video)."""
    # ... (Không thay đổi) ...
    seen = set()
    last_height = 0
    action_counter = 0
    no_new_content_strikes = 0
    
    for _ in range(30): 
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(random.uniform(2.0, 3.5))

        action_counter += 1
        if action_counter % 3 == 0: 
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(random.randint(-100, 100), random.randint(-80, 80)).perform()
                time.sleep(random.uniform(0.5, 1.3))
            except Exception:
                pass

        links_this_scroll = 0
        try:
            links = [a.get_attribute("href") for a in driver.find_elements(By.TAG_NAME, "a")]
            for l in links:
                if l and "tiktok.com/@" in l and l not in seen:
                    seen.add(l)
                    links_this_scroll += 1
        except Exception:
            pass 

        new_height = driver.execute_script("return document.body.scrollHeight")
        if abs(new_height - last_height) < 100: 
            no_new_content_strikes += 1
        else:
            no_new_content_strikes = 0
            
        last_height = new_height
        
        if no_new_content_strikes >= 3:
            print("-> Không có nội dung mới, dừng cuộn.")
            break
        if len(seen) >= limit:
            break
            
    return list(seen)


# --- SỬA LỖI (v3.8) ---
# Thêm tham số 'output_list'
def collect_hashtag_links(driver, hashtags, label, output_list, limit_per_tag=120):
    """
    Quét từng hashtag, cuộn và thu thập link.
    FIX 4: Thêm nhận diện CAPTCHA và Tăng thời gian nghỉ.
    """
    
    for tag in tqdm(hashtags, desc=f"Phase ({label})", unit="tag"):
        print(f"\n[{label}] Đang quét hashtag: #{tag}")
        url = f"https://www.tiktok.com/tag/{tag}"
        try:
            try:
                driver.get(url)
            except (TimeoutException, WebDriverException):
                print(f"Cảnh báo: Tải trang #{tag} quá 20 giây. Tiếp tục...")
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass

            # Giảm thời gian chờ
            time.sleep(random.uniform(5, 8)) # Giảm từ 6-10s xuống 5-8s

            # --- FIX 4 (v3.10): KIỂM TRA CAPTCHA ---
            # Selector ID của hình ảnh CAPTCHA xoay
            captcha_selector = "captcha-verify-image" 
            try:
                if driver.find_elements(By.ID, captcha_selector):
                    print(f"-> ⛔️ Bị CAPTCHA! Tạm dừng {CAPTCHA_SLEEP_SECONDS} giây...")
                    
                    # --- NÂNG CẤP (v3.12): Thêm tqdm cho thời gian nghỉ ---
                    # time.sleep(CAPTCHA_SLEEP_SECONDS) # <-- Bỏ dòng này
                    # Thêm vòng lặp tqdm:
                    for _ in tqdm(range(CAPTCHA_SLEEP_SECONDS), desc="Bị CAPTCHA, đang chờ", unit="s", leave=True):
                        time.sleep(1)
                    # --------------------------------------------------

                    print(f"-> Đã nghỉ xong. Bỏ qua hashtag #{tag} và thử lại sau.")
                    # Nạp lại trang chủ để "reset" trạng thái
                    driver.get("https://www.tiktok.com/foryou")
                    time.sleep(5)
                    continue # Bỏ qua tag này, sang tag tiếp theo
            except Exception:
                pass # Bỏ qua nếu không tìm thấy
            # ----------------------------------------

            try:
                actions = ActionChains(driver)
                for _ in range(random.randint(1, 3)):
                    actions.move_by_offset(random.randint(50, 400), random.randint(50, 400)).perform()
                    time.sleep(random.uniform(0.4, 1.0))
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(random.uniform(0.8, 1.5))
                driver.execute_script("window.scrollBy(0, -200);")
                time.sleep(random.uniform(0.5, 1.2))
            except Exception:
                pass

            links = scroll_and_collect_links(driver, limit=limit_per_tag)
            
            links_found_this_tag = 0
            for l in links:
                output_list.append({"hashtag": tag, "link": l, "label": label})
                links_found_this_tag += 1
                
            print(f"-> Thu được {links_found_this_tag} link từ #{tag}")
            
            # --- FIX 4 (v3.10): TĂNG THỜI GIAN NGHỈ ---
            # Nghỉ ngơi "như người thật" trước khi sang hashtag mới
            
            # --- NÂNG CẤP (v3.13): Giảm thời gian nghỉ ---
            sleep_time = random.uniform(7.0, 20.0) # <-- Giảm từ (15.0, 45.0) xuống (7.0, 20.0)
            
            # --- NÂNG CẤP (v3.12): Thêm tqdm cho thời gian nghỉ ---
            # print(f"-> Tạm nghỉ {sleep_time:.1f} giây...") # <-- Bỏ dòng này
            # time.sleep(sleep_time) # <-- Bỏ dòng này
            
            sleep_int = int(sleep_time)
            print(f"-> Tạm nghỉ {sleep_int} giây (chống bot)...")
            # Thêm vòng lặp tqdm (để `leave=False` cho sạch log)
            for _ in tqdm(range(sleep_int), desc="Nghỉ giữa các tag", unit="s", leave=False):
                time.sleep(1)
            # --------------------------------------------------
            
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi xử lý #{tag}: {e}")
            try:
                driver.quit()
                driver = init_driver(headless=False) 
                load_cookies_from_txt(driver, COOKIES_FILE)
            except Exception as e2:
                print(f"Không thể khởi động lại driver: {e2}. Bỏ qua hashtag này.")
                continue
            continue
    # Không cần return nữa, vì đã thêm trực tiếp vào output_list


# ---------------- MAIN ----------------
def main():
    # --- NÂNG CẤP (v3.11): Tạo thư mục data/crawl nếu chưa có ---
    try:
        os.makedirs(CRAWL_DIR, exist_ok=True)
        print(f"Đã đảm bảo thư mục {CRAWL_DIR} tồn tại.")
    except Exception as e:
        print(f"LỖI: Không thể tạo thư mục {CRAWL_DIR}: {e}")
        print("Vui lòng kiểm tra quyền (permission) hoặc tạo thủ công.")
        return
    # --------------------------------------------------

    driver = init_driver(headless=False) # Đặt True nếu chạy trên server
    if driver is None:
        return
        
    time.sleep(2)
    load_cookies_from_txt(driver, COOKIES_FILE)
    driver.refresh()
    
    if not is_logged_in(driver):
        print("⚠️ Cảnh báo: Cookie không hợp lệ hoặc chưa đăng nhập TikTok.")
        print("Script sẽ chạy ở chế độ Guest, có thể bị chặn hoặc không có dữ liệu.")
    else:
        print("✅ Đã đăng nhập thành công.")

    # --- NÂNG CẤP: Tải dữ liệu cũ (nếu có) ---
    df_existing = pd.DataFrame()
    if os.path.exists(OUTPUT_XLSX):
        try:
            print(f"\n--- GIAI ĐOẠN 0: Đang tải dữ liệu cũ từ {OUTPUT_XLSX} ---")
            df_existing = pd.read_excel(OUTPUT_XLSX)
            print(f"-> Đã tải {len(df_existing)} link từ file cũ.")
        except Exception as e:
            print(f"Lỗi khi đọc file Excel cũ, bắt đầu crawl mới: {e}")
            df_existing = pd.DataFrame() # Bắt đầu mới nếu file lỗi

    # --- SỬA LỖI (v3.8) ---
    # Khởi tạo list cho dữ liệu MỚI (để truyền vào hàm)
    harmful_data_new = []
    safe_data_new = []

    try:
        # --- Giai đoạn 1: harmful ---
        print("\n--- GIAI ĐOẠN 1: Thu thập harmful hashtag ---")
        # Truyền list `harmful_data_new` vào
        collect_hashtag_links(driver, RISKY_HASHTAGS, label="harmful", 
                              output_list=harmful_data_new, limit_per_tag=random.randint(90, 150)) # Thêm random

        # --- Giai đoạn 2: not harmful ---
        print("\n--- GIAI ĐOẠN 2: Thu thập not_harmful hashtag ---")
        # Truyền list `safe_data_new` vào
        collect_hashtag_links(driver, SAFE_HASHTAGS, label="not_harmful", 
                              output_list=safe_data_new, limit_per_tag=random.randint(90, 150)) # Thêm random

    except KeyboardInterrupt:
        print("\n⚠️ Đã dừng bởi người dùng (Ctrl+C). Đang xử lý dữ liệu thu được...")
    except Exception as e:
        print(f"Lỗi không mong muốn xảy ra trong quá trình crawl: {e}")
    
    # --- NÂNG CẤP: Logic lưu file an toàn (luôn chạy) ---
    finally:
        print("\n--- GIAI ĐOẠN 3: Gộp và lưu dữ liệu ---")
        
        # --- SỬA LỖI (v3.8) ---
        # 1. Gộp dữ liệu MỚI (từ 2 list đã được append)
        df_new = pd.DataFrame(harmful_data_new + safe_data_new)
        print(f"Thu được {len(df_new)} link MỚI trong phiên này.") # <-- Sẽ hiển thị đúng

        # 2. Kiểm tra nếu không có gì để lưu
        if df_existing.empty and df_new.empty:
            print("Không có dữ liệu nào (cũ hay mới) để lưu. Kết thúc.")
            if driver:
                driver.quit()
            return
            
        # 3. Gộp CŨ và MỚI
        all_df = pd.concat([df_existing, df_new], ignore_index=True)
        
        if 'link' not in all_df.columns:
             print("Lỗi: Không tìm thấy cột 'link' trong dữ liệu. Bỏ qua lưu.")
        else:
            pre_dedup_count = len(all_df)
            # Chống trùng lặp, giữ link cuối cùng (mới nhất nếu có trùng)
            all_df = all_df.drop_duplicates(subset=['link'], keep='last').reset_index(drop=True)
            post_dedup_count = len(all_df)
            print(f"Đã gộp dữ liệu. Tổng cộng: {post_dedup_count} link (đã xoá {pre_dedup_count - post_dedup_count} trùng lặp).")

            # 4. Xuất full dữ liệu
            try:
                all_df.to_excel(OUTPUT_XLSX, index=False)
                print(f"💾 Đã lưu toàn bộ {len(all_df)} dòng vào {OUTPUT_XLSX}")
            except Exception as e:
                print(f"LỖI khi lưu Excel: {e}")
                print("Thử lưu file backup...")
                all_df.to_excel("tiktok_links_BACKUP.xlsx", index=False)


            # 5. Random chọn 1000 mẫu (từ TỔNG dữ liệu)
            df_harmful_total = all_df[all_df["label"] == "harmful"]
            df_safe_total = all_df[all_df["label"] == "not_harmful"]
            
            n_harmful = min(1500, len(df_harmful_total))
            n_safe = min(2500, len(df_safe_total))
            
            if n_harmful > 0 or n_safe > 0:
                df_harmful_sample = df_harmful_total.sample(n=n_harmful, replace=False, random_state=42)
                df_safe_sample = df_safe_total.sample(n=n_safe, replace=False, random_state=42)
                
                df_final = pd.concat([df_harmful_sample, df_safe_sample], ignore_index=True)
                df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

                df_final.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
                print(f"✅ Đã lưu file CSV mẫu ({len(df_final)} dòng): {OUTPUT_CSV}")
                print(f"   ({n_harmful} harmful + {n_safe} not_harmful)")
            else:
                print("Không có dữ liệu để tạo file sample CSV.")

        print("Đóng driver...")
        if driver:
            try:
                driver.quit()
            except Exception:
                pass # Bỏ qua nếu driver đã tắt


if __name__ == "__main__":
    main()