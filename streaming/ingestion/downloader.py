import yt_dlp
import os
import shutil
import random
import time
import re


def download_video_to_temp_mobile(video_url):  # Giữ nguyên tên hàm cũ để tương thích
    """
    Tải video TikTok sử dụng yt-dlp với cấu hình Mobile (iPhone) để tránh bị chặn.
    """
    # 1. Thiết lập đường dẫn
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_path = os.path.join(base_dir, "cookies.txt")
    temp_dir = os.path.join(base_dir, "temp_downloads")

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # 2. Cấu hình yt-dlp (Mobile Emulation)
    ydl_opts = {
        "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us",
        },
        "extractor_args": {
            "tiktok": {
                "app_version": "32.0.0",
                "manifest_app_version": "32.0.0",
                "iid": "7318518857994389254",
                "device_id": str(
                    random.randint(7000000000000000000, 7999999999999999999)
                ),
            }
        },
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }

    if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
        ydl_opts["cookiefile"] = cookie_path

    try:
        print(f"🔍 [yt-dlp] Đang tải: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

            if not info:
                print(f"⚠️ Không lấy được thông tin video.")
                return None, None, []

            video_id = info.get("id")
            ext = info.get("ext", "mp4")

            # Lấy nội dung text
            title = info.get("title", "") or ""
            desc = info.get("description", "") or ""

            # Xử lý text: Nếu rỗng thì lấy ID làm text
            raw_text_data = f"{title} {desc}".strip()
            if not raw_text_data:
                raw_text_data = f"tiktok video content {video_id}"

            raw_comments = [raw_text_data]  # Trả về dạng list

            # Kiểm tra file
            expected_file = os.path.join(temp_dir, f"{video_id}.{ext}")
            final_path = None

            if os.path.exists(expected_file):
                final_path = expected_file
            else:
                # Quét thư mục (Fallback)
                for f in os.listdir(temp_dir):
                    if f.endswith(".mp4"):
                        f_path = os.path.join(temp_dir, f)
                        if time.time() - os.path.getmtime(f_path) < 15:
                            final_path = f_path
                            video_id = f.replace(".mp4", "")
                            break

            if final_path and os.path.getsize(final_path) > 1000:
                print(f"✅ Download OK: {os.path.basename(final_path)}")
                return video_id, final_path, raw_comments
            else:
                print("⚠️ File tải về lỗi.")
                return None, None, []

    except Exception as e:
        print(f"❌ Download Exception: {e}")
        return None, None, []
