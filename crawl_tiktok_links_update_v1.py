#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
find_tiktok_links_v3_15.py 
(Lưu ý: Dù docstring là v3.15, code này chứa logic của v3.16)

Nâng cấp từ v3.13 (dựa trên code của bạn):
- FIX 5 (CAPTCHA "dính"): Khi bị CAPTCHA, việc reset (tải foryou) là không đủ,
  vì session đã bị "đánh dấu".
- GIẢI PHÁP: Thêm logic "Auto-Restart" (vòng lặp while trong main).
  1. Khi phát hiện CAPTCHA, script sẽ `raise CaptchaException`.
  2. Khối `finally` (luôn chạy) sẽ LƯU TOÀN BỘ tiến trình.
  3. Khối `except CaptchaException` sẽ TẮT driver, nghỉ 30s.
  4. Vòng lặp `while` sẽ chạy lại.
  5. Script TẢI LẠI file Excel, tự động tìm các tag chưa crawl và CHẠY TIẾP.
- NÂNG CẤP (v3.16): Thêm check_for_captcha() vào VÒNG LẶP CUỘN
  (scroll_and_collect_links) để bắt CAPTCHA nhanh hơn.
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

# --- NÂNG CẤP (v3.15): Exception tùy chỉnh ---
class CaptchaException(Exception):
    """Exception đặc biệt khi bị dính CAPTCHA."""
    pass
# ------------------------------------------


# ---------------- CONFIG ----------------
# --- NÂNG CẤP (v3.11): Tự động tìm đường dẫn ---
# (Lấy từ code của bạn)
SCRIPT_PATH = os.path.realpath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CRAWL_DIR = os.path.join(DATA_DIR, "crawl")

print(f"Thư mục script (ROOT_DIR): {SCRIPT_DIR}")
print(f"Thư mục lưu data (CRAWL_DIR): {CRAWL_DIR}")

# --- Cập nhật đường dẫn file ---
COOKIES_FILE = os.path.join(SCRIPT_DIR, "cookies.txt") 
OUTPUT_XLSX = os.path.join(CRAWL_DIR, "tiktok_links_full.xlsx")
OUTPUT_CSV = os.path.join(CRAWL_DIR, "tiktok_links.csv")
# CAPTCHA_SLEEP_SECONDS = 120 # Sẽ không dùng sleep nữa, mà restart

# --- Harmful Hashtags (Lấy từ code của bạn) ---
RISKY_HASHTAGS = [
    # 1. Nội dung nhạy cảm / Gợi dục (Sexual / Suggestive)
    "sexy", "bikini", "body", "nhaycam", "18plus", "gáixinh", "gai18", 
    "lingerie", "kiss", "flirt", "seductive",
    
    # 2. Bạo lực / Tội phạm / Chất kích thích (Violence / Crime / Drugs)
    "bạo_lực", "đánh_nhau", "phóng_lợn", "fight", "streetfight", # Bạo lực (Thêm TA)
    "gianghomang", "đòi_nợ", "tín_dụng_đen", 
    "bay_lắc", "podchill", "drunk", "alcohol", # Chất kích thích (Thêm TA)
    "smoking", "rượu", "vape", "trippy", # (Thêm TA)
    
    # 3. Tiêu cực / Lừa đảo / Tin giả (Toxic / Scam / Fake)
    "lừa_đảo", "chửi", "toxic", "bóc_phốt", "drama", "chửi_thề", "fakenews", "scandal",
    "scam", "bullying", # (Thêm TA)
    
    # 4. Văn hóa nhạy cảm / Mê tín
    "mê_tín_dị_đoan", "bói_toán", "xem_bói", "bói_bài", "hầu_đồng", "gọi_hồn", 
    "tarotreading", "fortuneteller", "psychic", "ghosthunting", "superstition", # (Thêm TA)
    
    # 5. Thử thách / Giải trí tiêu cực (Risky Entertainment)
    "reactiondrama", "troll", "shockcontent", "weirdchallenge", "darkhumor", "thuthach",
    "prankgonewrong" # (Thêm TA)
]

# --- Not harmful Hashtags (Lấy từ code của bạn) ---
SAFE_HASHTAGS = [
    # 1. Sở thích & Giải trí (Hobbies & Entertainment)
    "travel", "food", "sport", "funny", "music", "game", "review", "nature", 
    "diy", "makeup", "car", "comedy", "art", "plant", "garden", "travelvlog", 
    "reviewphim", "ancungtiktok", "thethao",
    
    # 2. Động vật (Pets)
    "dog", "cat", "pet", "thuycung", 
    
    # 3. Giáo dục & Phát triển (Education & Development)
    "study", "tech", "lifehack", "learning", "motivation", "book", "education", 
    "healthy", "recipe", "coding", "science", "reading", "inspiration", "selfcare", 
    "quotes", "sachhay", "congnghe", "nauan",
    
    # 4. Đời sống & Xã hội (Lifestyle & Social)
    "fashion", "fitness", "family", "meditation", "volunteer", "environment", "giadinh"
]


# ---------------- FUNCTIONS ----------------
def load_cookies_from_txt(driver, cookie_file):
    """Đọc file Netscape cookies.txt và nạp vào driver."""
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


# --- NÂNG CẤP (v3.16): Hàm kiểm tra CAPTCHA chuyên dụng ---
def check_for_captcha(driver):
    """
    Kiểm tra sự xuất hiện của CAPTCHA (ID, iframe, container).
    Nếu tìm thấy, ném ra CaptchaException.
    """
    try:
        # Cách 1: Kiểm tra ID (selector cũ)
        captcha_id = "captcha-verify-image"
        if driver.find_elements(By.ID, captcha_id):
            raise CaptchaException(f"Phát hiện CAPTCHA (ID: {captcha_id})")

        # Cách 2: Kiểm tra iframe (rất phổ biến)
        # TikTok thường load CAPTCHA trong một iframe có 'src' chứa 'captcha'
        captcha_iframe = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='captcha']")
        if captcha_iframe:
            raise CaptchaException("Phát hiện CAPTCHA (iframe)")
        
        # Cách 3: Kiểm tra container (selector dự phòng)
        captcha_container = driver.find_elements(By.ID, "captcha-verify-container")
        if captcha_container:
                raise CaptchaException("Phát hiện CAPTCHA (container)")

    except CaptchaException as e:
        raise e # Ném lại để hàm gọi bắt được
    except Exception:
        pass # Bỏ qua các lỗi khác (vd: element không tồn tại)
# ----------------------------------------------------


def init_driver(headless=False):
    """Khởi tạo Chrome Driver với selenium-stealth."""
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

    driver.set_page_load_timeout(20)

    try:
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
        driver.execute_script("window.stop();") 
    except Exception as e:
        print(f"Cảnh báo: Không thể áp dụng selenium-stealth: {e}")
        
    return driver


def is_logged_in(driver):
    """Kiểm tra đăng nhập bằng cách tìm các dấu hiệu của user đã login."""
    print("Đang kiểm tra trạng thái đăng nhập...")
    
    try:
        driver.get("https://www.tiktok.com/foryou")
    except (TimeoutException, WebDriverException):
        print("Cảnh báo: Tải trang 'foryou' quá 20 giây. Tiếp tục kiểm tra...")
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass

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
    seen = set()
    last_height = 0
    action_counter = 0
    no_new_content_strikes = 0
    
    for _ in range(30):
        # --- NÂNG CẤP (v3.16): Kiểm tra CAPTCHA mỗi khi cuộn ---
        check_for_captcha(driver)
        # ----------------------------------------------------

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


def collect_hashtag_links(driver, hashtags, label, output_list, limit_per_tag=120):
    """
    Quét từng hashtag, cuộn và thu thập link.
    FIX 5: Ném ra CaptchaException thay vì sleep.
    """
    
    # Bọc `hashtags` bằng `tqdm` để thanh tiến trình bên ngoài
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

            time.sleep(random.uniform(5, 8)) 

            # --- NÂNG CẤP (v3.16): Dùng hàm check_for_captcha ---
            # (Xóa bỏ khối code v3.15 cũ ở đây)
            check_for_captcha(driver)
            # --------------------------------------------------

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
            
            # Giữ thời gian nghỉ (chống bot)
            sleep_time = random.uniform(7.0, 20.0) 
            sleep_int = int(sleep_time)
            print(f"-> Tạm nghỉ {sleep_int} giây (chống bot)...")
            for _ in tqdm(range(sleep_int), desc="Nghỉ giữa các tag", unit="s", leave=False):
                time.sleep(1)
            
        except CaptchaException:
            raise # Đẩy CaptchaException lên cho `main`
            
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi xử lý #{tag}: {e}")
            # Lỗi này không phải CAPTCHA, thử khởi động lại driver
            try:
                driver.quit()
                driver = init_driver(headless=False) 
                load_cookies_from_txt(driver, COOKIES_FILE)
            except Exception as e2:
                print(f"Không thể khởi động lại driver: {e2}. Bỏ qua hashtag này.")
                continue
            continue


# ---------------- MAIN ----------------
def main():
    try:
        os.makedirs(CRAWL_DIR, exist_ok=True)
        print(f"Đã đảm bảo thư mục {CRAWL_DIR} tồn tại.")
    except Exception as e:
        print(f"LỖI: Không thể tạo thư mục {CRAWL_DIR}: {e}")
        return

    # --- NÂNG CẤP (v3.15): Logic Restart ---
    
    df_existing = pd.DataFrame()
    harmful_data_new = []
    safe_data_new = []
    
    # Vòng lặp chính, sẽ chạy lại nếu bị CAPTCHA
    restart_needed = True
    while restart_needed:
        restart_needed = False # Giả sử thành công
        driver = None # Đảm bảo driver được định nghĩa
        
        try:
            # --- GIAI ĐOẠN 0: Tải dữ liệu cũ ---
            # Luôn tải file mới nhất mỗi khi lặp
            if os.path.exists(OUTPUT_XLSX):
                try:
                    print(f"\n--- GIAI ĐOẠN 0: Đang tải dữ liệu cũ từ {OUTPUT_XLSX} ---")
                    df_existing = pd.read_excel(OUTPUT_XLSX)
                    print(f"-> Đã tải {len(df_existing)} link từ file cũ.")
                except Exception as e:
                    print(f"Lỗi khi đọc file Excel cũ, bắt đầu crawl mới: {e}")
                    df_existing = pd.DataFrame()
            else:
                 df_existing = pd.DataFrame()


            # --- Khởi động Driver ---
            driver = init_driver(headless=False) 
            if driver is None:
                print("Không thể khởi tạo driver. Dừng.")
                break # Thoát vòng lặp while

            time.sleep(2)
            load_cookies_from_txt(driver, COOKIES_FILE)
            driver.refresh()
            
            if not is_logged_in(driver):
                print("⚠️ Cảnh báo: Cookie không hợp lệ hoặc chưa đăng nhập TikTok.")
                print("Script sẽ chạy ở chế độ Guest. Dừng lại để kiểm tra cookies.")
                break # Thoát vòng lặp while
            else:
                print("✅ Đã đăng nhập thành công.")


            # --- Tính toán các tag CÒN LẠI ---
            done_harmful_tags = set()
            done_safe_tags = set()
            if 'hashtag' in df_existing.columns and 'label' in df_existing.columns:
                done_harmful_tags = set(df_existing[df_existing['label'] == 'harmful']['hashtag'])
                done_safe_tags = set(df_existing[df_existing['label'] == 'not_harmful']['hashtag'])
            
            remaining_risky = [t for t in RISKY_HASHTAGS if t not in done_harmful_tags]
            remaining_safe = [t for t in SAFE_HASHTAGS if t not in done_safe_tags]

            if not remaining_risky and not remaining_safe:
                print("\n🎉 Tất cả các hashtag đã được crawl xong. Dừng.")
                break # Hoàn thành, thoát vòng lặp while

            # --- Giai đoạn 1: harmful (chỉ chạy nếu còn) ---
            if remaining_risky:
                print(f"\n--- GIAI ĐOẠN 1: Thu thập {len(remaining_risky)} harmful hashtag còn lại ---")
                collect_hashtag_links(driver, remaining_risky, label="harmful", 
                                      output_list=harmful_data_new, limit_per_tag=random.randint(90, 150))

            # --- Giai đoạn 2: not harmful (chỉ chạy nếu còn) ---
            if remaining_safe:
                print(f"\n--- GIAI ĐOẠN 2: Thu thập {len(remaining_safe)} safe hashtag còn lại ---")
                collect_hashtag_links(driver, remaining_safe, label="not_harmful", 
                                      output_list=safe_data_new, limit_per_tag=random.randint(90, 150))

        except CaptchaException as e:
            print(f"\n⛔️ BỊ CAPTCHA ({e}).")
            print("Sẽ lưu tiến trình, khởi động lại driver và chạy tiếp...")
            restart_needed = True # Báo hiệu cho vòng lặp `while` chạy lại

        except KeyboardInterrupt:
            print("\n⚠️ Đã dừng bởi người dùng (Ctrl+C). Đang xử lý dữ liệu thu được...")
            break # Thoát vòng lặp while
        
        except Exception as e:
            print(f"\nLỗi không mong muốn xảy ra trong quá trình crawl: {e}")
            break # Thoát vòng lặp while
        
        # --- NÂNG CẤP (v3.15): Logic lưu file (luôn chạy) ---
        finally:
            print("\n--- GIAI ĐOẠN 3: Gộp và lưu dữ liệu (luôn chạy) ---")
            
            df_new = pd.DataFrame(harmful_data_new + safe_data_new)
            print(f"Thu được {len(df_new)} link MỚI trong phiên này.")
            
            # Xóa list MỚI để chuẩn bị cho lần lặp sau (nếu có)
            harmful_data_new.clear()
            safe_data_new.clear()

            if df_existing.empty and df_new.empty:
                print("Không có dữ liệu nào (cũ hay mới) để lưu. Kết thúc.")
            else:
                all_df = pd.concat([df_existing, df_new], ignore_index=True)
                
                if 'link' not in all_df.columns:
                     print("Lỗi: Không tìm thấy cột 'link' trong dữ liệu. Bỏ qua lưu.")
                else:
                    pre_dedup_count = len(all_df)
                    all_df = all_df.drop_duplicates(subset=['link'], keep='last').reset_index(drop=True)
                    post_dedup_count = len(all_df)
                    print(f"Đã gộp dữ liệu. Tổng cộng: {post_dedup_count} link (đã xoá {pre_dedup_count - post_dedup_count} trùng lặp).")

                    # 4. Xuất full dữ liệu
                    try:
                        all_df.to_excel(OUTPUT_XLSX, index=False)
                        print(f"💾 Đã lưu toàn bộ {len(all_df)} dòng vào {OUTPUT_XLSX}")
                    except Exception as e:
                        print(f"LỖI khi lưu Excel: {e}")
                        print(f"Thử lưu file backup vào {CRAWL_DIR}...")
                        all_df.to_excel(os.path.join(CRAWL_DIR, "tiktok_links_BACKUP.xlsx"), index=False)
                    
                    # CẬP NHẬT df_existing cho lần lặp tiếp theo
                    df_existing = all_df.copy()

                    # 5. Random chọn mẫu (Lấy từ code của bạn)
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

            print("Đóng driver (nếu có)...")
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass 
            
            # Nếu cần restart, nghỉ 30s
            if restart_needed:
                print("Tạm nghỉ 30s trước khi khởi động lại...")
                for _ in tqdm(range(30), desc="Nghỉ 30s", leave=True):
                    time.sleep(1)

    print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ---")


if __name__ == "__main__":
    main()