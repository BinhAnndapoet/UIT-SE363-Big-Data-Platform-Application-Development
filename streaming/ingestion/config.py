import os

# --- PATHS CONFIGURATION (REFACTORED STRUCTURE) ---

# 1. Xác định vị trí file config.py hiện tại
# Container path: /opt/project/streaming/ingestion
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"DEBUG: BASE_DIR is set to: {BASE_DIR}")

# 2. Đi ngược lên 1 cấp để lấy thư mục streaming
# Container path: /opt/project/streaming
STREAMING_DIR = os.path.dirname(BASE_DIR)

# 3. Định nghĩa thư mục data (cấu trúc mới)
# Đường dẫn: /opt/project/streaming/data
DATA_DIR = os.path.join(STREAMING_DIR, "data")

# Các thư mục con
CRAWL_DIR = os.path.join(DATA_DIR, "crawl")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
AUDIO_DIR = os.path.join(DATA_DIR, "audios")

# Tạo thư mục nếu chưa tồn tại
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# File Input/Output
# File CSV kết quả crawl: /opt/project/streaming/data/crawl/tiktok_links_viet.csv
INPUT_CSV_PATH = os.path.join(CRAWL_DIR, "tiktok_links_viet.csv")
print(f"DEBUG: INPUT_CSV_PATH is set to: {INPUT_CSV_PATH}")

# File Cookies và Temp Download nằm ngay trong thư mục ingestion cho gọn
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.txt")
TEMP_DOWNLOAD_DIR = os.path.join(BASE_DIR, "temp_downloads")

# --- MINIO CONFIG ---
# MINIO_ENDPOINT = "localhost:9000"
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
MINIO_BUCKET = "tiktok-raw-videos"
MINIO_AUDIO_BUCKET = "tiktok-raw-audios"

# --- KAFKA CONFIG ---
# KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
KAFKA_BOOTSTRAP_SERVERS = ["kafka:29092"]  # Dùng port nội bộ 29092
KAFKA_TOPIC = "tiktok_raw_data"

# --- AI LABELING CONFIG ---
ENABLE_AI_LABELING = True
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# Tạo các thư mục cần thiết nếu chưa có
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
# Lưu ý: DATA_DIR và CRAWL_DIR phải tồn tại (do bạn đã tạo tay),
# nhưng lệnh này giúp tạo lại nếu lỡ tay xóa.
os.makedirs(CRAWL_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# Tạo thư mục nếu chưa có (Tránh lỗi logic, nhưng việc tạo chính nên để start_all.sh làm)
try:
    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(CRAWL_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
except:
    pass
