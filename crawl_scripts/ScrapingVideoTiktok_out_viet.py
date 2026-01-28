# %%
# ===========================
# 0) CÀI THƯ VIỆN CẦN THIẾT
# ===========================
!pip -q install yt-dlp requests pandas xlsxwriter
print("✅ Đã cài đặt xong các thư viện cần thiết.")


# %%
# ===========================
# 1) KHAI BÁO & MOUNT DRIVE (tuỳ chọn)
# ===========================
# from google.colab import drive
# drive.mount('/content/drive')
# BASE_DRIVE_DIR = "/content/drive/MyDrive/SE363/Crawl"   # đổi nếu muốn lưu thẳng vào Drive của bạn
# print("Output folder:", BASE_DRIVE_DIR)

import os

ROOT_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in globals()
    else os.getcwd()
)
# 2. Định nghĩa các đường dẫn con
CRAWL_DIR = os.path.join(ROOT_DIR, "data_viet", "crawl")
VIDEO_DIR = os.path.join(ROOT_DIR, "data_viet", "videos")

# Đường dẫn file CSV đầu vào (được tạo bởi script crawl)
INPUT_CSV = os.path.join(CRAWL_DIR, "sub_tiktok_links_viet.csv")
HARMFUL_DIR = os.path.join(VIDEO_DIR, "harmful")
NOT_HARMFUL_DIR = os.path.join(VIDEO_DIR, "not_harmful")

# 3. Tạo các thư mục nếu chưa tồn tại
os.makedirs(CRAWL_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(HARMFUL_DIR, exist_ok=True)
os.makedirs(NOT_HARMFUL_DIR, exist_ok=True)


print(f"📂 Thư mục dự án: {ROOT_DIR}")
print(f"📄 File dữ liệu đầu vào: {INPUT_CSV}")
print(f"📁 Thư mục lưu video HARMFUL: {HARMFUL_DIR}")
print(f"📁 Thư mục lưu video NOT_HARMFUL: {NOT_HARMFUL_DIR}")


# %% [markdown]
# # Step up crawl video id follow dataframe index

# %%
# START_INDEX = 0 # BAn
# END_INDEX = 332 # BAn

START_INDEX = 0 # Khoi
END_INDEX = 1000 # Khoi

# START_INDEX = 666 # Nam
# END_INDEX = 999 # Nam


# %%
# ===========================
# 2) IMPORT & NẠP COOKIES.TXT (Netscape)
#    -> KHÔNG gán thẳng vào header "Cookie"
#    -> Dùng MozillaCookieJar + requests.Session
# ===========================
import os, re, json, time, requests
import http.cookiejar as cookielib
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
import pandas as pd
import yt_dlp

COOKIES_PATH = "cookies.txt"  # Upload file này lên Colab cùng notebook

# Kiểm tra cookies.txt tồn tại
if not os.path.exists(COOKIES_PATH):
    from google.colab import files
    print("Vui lòng upload cookies.txt (Export từ trình duyệt).")
    uploaded = files.upload()
    COOKIES_PATH = next(iter(uploaded))

# Tạo session dùng cookie Netscape
cj = cookielib.MozillaCookieJar()
cj.load(COOKIES_PATH, ignore_discard=True, ignore_expires=True)

session = requests.Session()
session.cookies = cj
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.tiktok.com/"
})

# Kiểm tra có cookie cho tiktok không
has_tiktok_cookies = any("tiktok.com" in c.domain for c in session.cookies)
print("Cookies for tiktok.com found:", has_tiktok_cookies)


# %%
# ===========================
# 3) HÀM HỖ TRỢ (oEmbed, parse URL/aweme_id)
# ===========================
def fetch_oembed(video_url, timeout=12):
    """Lấy metadata oEmbed cơ bản của video (official)."""
    oembed_url = "https://www.tiktok.com/oembed"
    try:
        r = session.get(oembed_url, params={"url": video_url}, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print("oEmbed error:", e)
        return None

def extract_aweme_id_from_url(video_url: str):
    """Parse aweme_id từ URL dạng /video/<digits>"""
    m = re.search(r"/video/(\d+)", video_url)
    return m.group(1) if m else None


# %%
# ===========================
# 4) DOWNLOAD VIDEO BẰNG yt-dlp (dùng cookiefile + headers)
# ===========================
def download_tiktok_with_yt_dlp(video_url, out_dir, write_info_json=True, max_filesize=None):
    os.makedirs(out_dir, exist_ok=True)
    out_template = os.path.join(out_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": out_template,
        "format": "best",
        "noplaylist": True,
        # Dùng cookiefile + UA/Referer để giảm lỗi regional/age/403
        "cookiefile": COOKIES_PATH,
        "http_headers": {
            "User-Agent": "Mozilla/5.0",
            "Referer": video_url
        },
        # Tránh tải lại cùng video
        "download_archive": os.path.join(out_dir, "downloaded.txt"),
    }

    if write_info_json:
        ydl_opts.update({
            "writedescription": True,
            "writesubtitles": False,
            "writeinfojson": True
        })

    if max_filesize:
        ydl_opts["max_filesize"] = max_filesize

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    # Lấy info json nếu có
    info_json_path = None
    if isinstance(info, dict) and "id" in info:
        candidate = os.path.join(out_dir, f"{info['id']}.info.json")
        if os.path.exists(candidate):
            info_json_path = candidate

    if info_json_path:
        with open(info_json_path, "r", encoding="utf-8") as f:
            info_data = json.load(f)
    else:
        info_data = info
    return info_data


# %%
# ===========================
# 5) CRAWL COMMENT (WEB API KHÔNG CHÍNH THỨC) BẰNG session
#    Lưu ý: Có thể 403/empty trên Colab dù có cookies.
# ===========================
def fetch_comments_web(aweme_id: str, session: requests.Session, max_comments=200, sleep=1.0):
    url = "https://www.tiktok.com/api/comment/list/"
    cursor, out = 0, []
    while len(out) < max_comments:
        params = {"aid": 1988, "aweme_id": aweme_id, "cursor": cursor, "count": 20}
        r = session.get(url, params=params, timeout=20)
        if r.status_code != 200:
            print("HTTP", r.status_code, r.text[:200])
            break
        try:
            data = r.json()
        except Exception as e:
            print("JSON parse error:", e, r.text[:200]); break

        out.extend(data.get("comments") or [])
        print(f"Fetched {len(out)} comments so far…")

        if not data.get("has_more"):
            break
        cursor = data.get("cursor", cursor + 20)
        if sleep: time.sleep(sleep)
    return out

def fetch_replies_web(aweme_id: str, comment_id: str, session: requests.Session, max_replies=100, sleep=1.0):
    url = "https://www.tiktok.com/api/comment/list/reply/"
    cursor, out = 0, []
    while len(out) < max_replies:
        params = {"aid": 1988, "aweme_id": aweme_id, "comment_id": comment_id, "cursor": cursor, "count": 20}
        r = session.get(url, params=params, timeout=20)
        if r.status_code != 200:
            print("HTTP", r.status_code, r.text[:200])
            break
        try:
            data = r.json()
        except Exception as e:
            print("JSON parse error:", e, r.text[:200]); break

        out.extend(data.get("comments") or [])
        if not data.get("has_more"):
            break
        cursor = data.get("cursor", cursor + 20)
        if sleep: time.sleep(sleep)
    return out

def fetch_all_comments_with_replies_web(aweme_id: str, session: requests.Session,
                                        max_comments=200, max_replies_per_comment=50, sleep=1.0):
    comments = fetch_comments_web(aweme_id, session, max_comments=max_comments, sleep=sleep)
    results = []
    for c in comments:
        item = {
            "cid": c.get("cid"),
            "text": c.get("text"),
            "author": (c.get("user") or {}).get("nickname"),
            "create_time": c.get("create_time"),
            "like_count": c.get("digg_count"),
            "reply_count": c.get("reply_comment_total"),
            "replies": []
        }
        try:
            if item["cid"]:
                rs = fetch_replies_web(aweme_id, item["cid"], session, max_replies=max_replies_per_comment, sleep=sleep)
                item["replies"] = rs
        except Exception as e:
            print(f"⚠️ Reply error for {item['cid']}: {e}")
        results.append(item)
    return results


# %%
# ===========================
# 6) HÀM CRAWL 1 VIDEO: oEmbed → yt-dlp → comments → JSON
#    + Fallback lấy aweme_id nếu oEmbed không có
# ===========================
def crawl_one_tiktok(video_url, out_dir, use_comments=False, max_comments=200, max_replies_per_comment=50, sleep=1.0):
    os.makedirs(out_dir, exist_ok=True)
    result = {
        "url": video_url,
        "crawled_at": datetime.utcnow().isoformat() + "Z"
    }

    # 1) oEmbed
    oembed = fetch_oembed(video_url)
    result["oembed"] = oembed

    # 2) Tải video + đọc info
    try:
        meta = download_tiktok_with_yt_dlp(video_url, out_dir)
        result["yt_dlp_info"] = meta
    except Exception as e:
        result["yt_dlp_error"] = str(e)
        meta = None

    # 3) Lấy aweme_id
    aweme_id = None
    if oembed and isinstance(oembed, dict):
        aweme_id = oembed.get("embed_product_id")
    if not aweme_id:
        aweme_id = extract_aweme_id_from_url(video_url)
    if not aweme_id and isinstance(meta, dict):
        aweme_id = str(meta.get("id"))

    if not aweme_id:
        raise ValueError("Không lấy được aweme_id cho video này")

    print("aweme_id:", aweme_id)

    # 4) Comments (tuỳ chọn)
    if use_comments:
        cmts = fetch_all_comments_with_replies_web(
            aweme_id, session, max_comments=max_comments,
            max_replies_per_comment=max_replies_per_comment, sleep=sleep
        )
        result["comments"] = cmts

    # 5) Save metadata JSON
    json_path = os.path.join(out_dir, f"{aweme_id}_crawl.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result, json_path


# %%
# ===========================
# 7) XUẤT EXCEL (comments + replies thành 1 sheet)
# ===========================
# def export_comments_to_excel(all_items, aweme_id: str, out_dir: str):
#     rows = []
#     for c in all_items or []:
#         # Top-level
#         rows.append({
#             "video_id": aweme_id,
#             "cid": c.get("cid"),
#             "parent_cid": None,
#             "is_reply": 0,
#             "author_name": c.get("author"),
#             "text": c.get("text"),
#             "like_count": c.get("like_count"),
#             "reply_count": c.get("reply_count"),
#             "create_time": c.get("create_time"),
#         })
#         # Replies
#         for r in (c.get("replies") or []):
#             ru = r.get("user") or {}
#             rows.append({
#                 "video_id": aweme_id,
#                 "cid": r.get("cid"),
#                 "parent_cid": c.get("cid"),
#                 "is_reply": 1,
#                 "author_name": ru.get("nickname"),
#                 "text": r.get("text"),
#                 "like_count": r.get("digg_count") or r.get("like_count"),
#                 "reply_count": r.get("reply_comment_total") or r.get("reply_count"),
#                 "create_time": r.get("create_time"),
#             })

#     df = pd.DataFrame(rows)

#     # Epoch -> thời gian
#     if "create_time" in df.columns:
#         dt = pd.to_datetime(df["create_time"], unit="s", errors="coerce", utc=True)
#         df["created_at_utc"] = dt
#         df["created_at_vn"] = dt.dt.tz_convert("Asia/Ho_Chi_Minh")

#     # Sắp cột
#     cols = ["video_id","cid","parent_cid","is_reply","author_name",
#             "text","like_count","reply_count","create_time",
#             "created_at_utc","created_at_vn"]
#     df = df[[c for c in cols if c in df.columns]]

#     os.makedirs(out_dir, exist_ok=True)
#     xlsx_path = os.path.join(out_dir, f"{aweme_id}_comments.xlsx")
#     with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
#         df.to_excel(writer, index=False, sheet_name="comments")
#         ws = writer.sheets["comments"]
#         ws.freeze_panes(1, 0)
#         for i, col in enumerate(df.columns):
#             maxlen = min(60, max(10, df[col].astype(str).str.len().max() if not df.empty else 10))
#             ws.set_column(i, i, maxlen + 2)
#     print("✅ Saved Excel:", xlsx_path)
#     return xlsx_path, df


# %%


def export_comments_to_excel(all_items, aweme_id: str, out_dir: str):
    import os, pandas as pd
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    for c in all_items or []:
        # Top-level
        rows.append({
            "video_id": aweme_id,
            "cid": c.get("cid"),
            "parent_cid": None,
            "is_reply": 0,
            "author_name": c.get("author"),
            "text": c.get("text"),
            "like_count": c.get("like_count"),
            "reply_count": c.get("reply_count"),
            "create_time": c.get("create_time"),
        })
        # Replies
        for r in (c.get("replies") or []):
            ru = r.get("user") or {}
            rows.append({
                "video_id": aweme_id,
                "cid": r.get("cid"),
                "parent_cid": c.get("cid"),
                "is_reply": 1,
                "author_name": ru.get("nickname"),
                "text": r.get("text"),
                "like_count": r.get("digg_count") or r.get("like_count"),
                "reply_count": r.get("reply_comment_total") or r.get("reply_count"),
                "create_time": r.get("create_time"),
            })

    df = pd.DataFrame(rows)

    # Epoch -> datetime (tz-aware), rồi bỏ tz để Excel chấp nhận
    if "create_time" in df.columns:
        dt_utc = pd.to_datetime(df["create_time"], unit="s", errors="coerce", utc=True)
        # BẢN NAIVE (không timezone)
        df["created_at_utc"] = dt_utc.dt.tz_localize(None)
        df["created_at_vn"]  = dt_utc.dt.tz_convert("Asia/Ho_Chi_Minh").dt.tz_localize(None)

    # Sắp cột
    cols = ["video_id","cid","parent_cid","is_reply","author_name",
            "text","like_count","reply_count","create_time",
            "created_at_utc","created_at_vn"]
    df = df[[c for c in cols if c in df.columns]]

    xlsx_path = os.path.join(out_dir, f"{aweme_id}_comments.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter",
                        datetime_format="yyyy-mm-dd hh:mm:ss") as writer:
        df.to_excel(writer, index=False, sheet_name="comments")
        ws = writer.sheets["comments"]
        ws.freeze_panes(1, 0)
        # Auto-width
        for i, col in enumerate(df.columns):
            maxlen = min(60, max(10, df[col].astype(str).str.len().max() if not df.empty else 10))
            ws.set_column(i, i, maxlen + 2)

    print("✅ Saved Excel:", xlsx_path)
    return xlsx_path, df



# %%
# ===========================
# 8) CHẠY TỰ ĐỘNG TỪ FILE CSV (CÓ PHÂN LOẠI & RESUME)
# ===========================
import pandas as pd
import time
import os
from tqdm.notebook import tqdm # Bỏ comment nếu muốn dùng thanh tiến trình đẹp hơn

# 1. Đọc và Lọc file CSV
if not os.path.exists(INPUT_CSV):
    print(f"❌ LỖI: Không tìm thấy file {INPUT_CSV}")
    print("Vui lòng chạy script 'find_tiktok_links.py' trước để có dữ liệu.")
else:
    print(f"Đang đọc dữ liệu từ: {INPUT_CSV} ...")
    df = pd.read_csv(INPUT_CSV)
    print(f"-> Tổng số dòng trong CSV: {len(df)}")

    # LỌC QUAN TRỌNG: Chỉ lấy những link là VIDEO (có chứa '/video/')
    # Loại bỏ các link profile (ví dụ: tiktok.com/@username)
    # Làm sạch link (bỏ các phần thừa sau dấu ?)
    # Loại bỏ các link trùng lặp
    df_videos = df[df['link'].str.contains('/video/', na=False)].copy()
    df_videos['link'] = df_videos['link'].apply(lambda x: x.split('?')[0])
    df_videos = df_videos.drop_duplicates(subset=['link'])
    print(f"-> Số lượng VIDEO thực tế cần crawl: {len(df_videos)}")
    
    # Lọc dataframe theo khoảng index
    df_videos = df_videos.iloc[START_INDEX:END_INDEX]

    print(f"-> Số lượng VIDEO thực tế cần crawl theo index: {len(df_videos)}")
    print("=======================================================")
    

    # 2. Vòng lặp Crawl chính
    # (Dùng itertuples để lặp qua dataframe nhanh hơn)
    # (Dùng tqdm bọc df_videos.itertuples() để có thanh tiến trình)
    for row in tqdm(df_videos.itertuples(index=True), total=len(df_videos), desc="Tổng tiến độ"):
        index = row.Index  # index dataframe
        original_url = row.link
        label = row.label
        hashtag = row.hashtag
        
        # a) Lấy ID video
        aweme_id = extract_aweme_id_from_url(original_url)
        if not aweme_id:
            print(f"\n   ⚠️ Không lấy được ID video từ URL: {original_url}. Bỏ qua.")
            continue

        # --- Tên thư mục theo index dataframe ---
        if label == 'harmful':
            base_save_dir = HARMFUL_DIR
        else:
            base_save_dir = NOT_HARMFUL_DIR

        folder_name = f"video_{index}"

        print(f"\n▶️ Đang xử lý: {original_url}")
        print(f"   🏷️ Nhãn: {label.upper()} | #️⃣ Hashtag: #{hashtag}")
        print(f"   📁 Tên thư mục: {folder_name} (ID: {aweme_id})")

        # c) Tạo thư mục riêng cho video này
        video_specific_dir = os.path.join(base_save_dir, folder_name)

        # d) Kiểm tra RESUME
        if os.path.exists(video_specific_dir) and os.listdir(video_specific_dir):
            print(f"   ⏭️ Thư mục '{folder_name}' đã tồn tại dữ liệu. Bỏ qua (Resume).")
            continue

        os.makedirs(video_specific_dir, exist_ok=True)

        # e) Bắt đầu Crawl (Gọi lại hàm crawl_one_tiktok của bạn)
        try:
            print(f"   ⬇️ Bắt đầu crawl vào: {video_specific_dir} ...")

            # --- GỌI HÀM CRAWL GỐC ---
            res, jsonp = crawl_one_tiktok(
                original_url,
                video_specific_dir,
                use_comments=True,          # Lấy comment
                max_comments=200,           # Tăng số lượng nếu cần
                max_replies_per_comment=50,
                sleep=1.0                   # Nghỉ giữa các lần gọi API comment
            )
            print(f"   ✅ Metadata JSON saved: {os.path.basename(jsonp)}")

            # --- XUẤT EXCEL COMMENT ---
            cmts = res.get("comments", [])
            if cmts:
                # Gọi hàm export_comments_to_excel gốc
                xlsx_path, _ = export_comments_to_excel(cmts, aweme_id, video_specific_dir)
                if xlsx_path:
                    print(f"   ✅ Comments Excel saved: {os.path.basename(xlsx_path)} ({len(cmts)} cmts)")
            else:
                print("   ℹ️ Không tìm thấy comment nào.")

        except Exception as e:
             print(f"   ❌ LỖI KHI CRAWL VIDEO NÀY: {e}")
             # Có thể xóa thư mục lỗi nếu muốn sạch sẽ
             # import shutil
             # shutil.rmtree(video_specific_dir, ignore_errors=True)

        # f) Nghỉ ngơi để tránh bị chặn (Rate Limit)
        print("   💤 Đang nghỉ 5s...")
        time.sleep(5)

    print("\n🎉🎉🎉 ĐÃ HOÀN TẤT TOÀN BỘ DANH SÁCH VIDEO! 🎉🎉🎉")


# %%
# # ===========================
# # 8) CHẠY TỰ ĐỘNG TỪ FILE TXT (CÓ CƠ CHẾ RESUME)
# # ===========================
# import time
# import os # Đảm bảo os đã được import (mặc dù đã có ở ô 3)

# URL_FILE_PATH = "urls.txt" # Tên file bạn đã upload

# # --- Đọc file urls.txt ---
# try:
#     with open(URL_FILE_PATH, 'r') as f:
#         VIDEO_URL_LIST = [line.strip() for line in f if line.strip() and line.strip().startswith("http")]
    
#     if not VIDEO_URL_LIST:
#         print(f"Lỗi: File {URL_FILE_PATH} trống hoặc không chứa link hợp lệ.")
#     else:
#         print(f"*** Đã tìm thấy {len(VIDEO_URL_LIST)} URLs trong file. Bắt đầu crawl... ***")

# except FileNotFoundError:
#     print(f"Lỗi: Không tìm thấy file {URL_FILE_PATH}. Bạn đã upload file chưa?")
#     VIDEO_URL_LIST = []
# # -----------------------------


# # Dùng enumerate để lấy cả index (0, 1, 2...) và url
# for index, url in enumerate(VIDEO_URL_LIST):
    
#     # Tạo tên thư mục, ví dụ: "vid_1", "vid_2"...
#     folder_name = f"vid_{index + 1}"
    
#     # Tạo đường dẫn đầy đủ đến thư mục mới này
#     video_specific_dir = os.path.join(CRAWL_DIR, folder_name)
    
#     # -------- CƠ CHẾ RESUME (PHẦN THÊM MỚI) --------
#     # Kiểm tra xem thư mục này đã tồn tại hay chưa
#     if os.path.exists(video_specific_dir):
#         # Nếu đã tồn tại, in thông báo và bỏ qua (continue)
#         print(f"\n--- [BỎ QUA] Thư mục '{folder_name}' đã tồn tại. Chuyển sang video tiếp theo. ---")
#         continue # Lệnh mấu chốt: Dừng vòng lặp này, đi đến video tiếp theo
#     # -----------------------------------------------

#     # Nếu thư mục chưa tồn tại, TẠO MỚI và bắt đầu crawl
#     os.makedirs(video_specific_dir, exist_ok=True) 

#     print(f"\n=======================================================")
#     print(f"--- [BẮT ĐẦU] Xử lý: {url} (Lưu vào: {video_specific_dir}) ---")
    
#     try:
#         # Gọi hàm crawl và TRUYỀN THƯ MỤC MỚI vào:
#         res, jsonp = crawl_one_tiktok(
#             url, video_specific_dir, 
#             use_comments=True,         
#             max_comments=100,          
#             max_replies_per_comment=50 
#         )
#         print(f"✅ Đã lưu Metadata JSON vào: {jsonp}")

#         # Nếu có comments thì xuất Excel
#         cmts = res.get("comments", [])
#         if cmts:
#             aweme_id = extract_aweme_id_from_url(url) or (res.get("oembed") or {}).get("embed_product_id")
#             if aweme_id:
#                 xlsx_path, df_preview = export_comments_to_excel(cmts, aweme_id, video_specific_dir) 
#                 print(f"✅ Đã lưu Comments Excel vào: {xlsx_path}")
#             else:
#                  print("⚠️ Không tìm thấy aweme_id, bỏ qua xuất Excel.")
#         else:
#             print("ℹ️ Video này không có comment (hoặc crawl comment thất bại).")

#     except Exception as e:
#         print(f"!!!!!!!! LỖI NGHIÊM TRỌNG !!!!!!!!")
#         print(f"Lỗi khi xử lý {url}: {e}")
#         print(f"--- [BỎ QUA] Video này và tiếp tục. ---")

#     print(f"=======================================================")
    
#     time.sleep(5)

# print("\n*** ĐÃ HOÀN TẤT TOÀN BỘ DANH SÁCH! ***")



