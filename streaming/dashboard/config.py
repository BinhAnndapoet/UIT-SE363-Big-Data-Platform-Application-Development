"""
Configuration settings for the TikTok Safety Dashboard
"""

import os
import re

# --- Extract Tailscale/Public IP from MINIO_PUBLIC_ENDPOINT ---
_minio_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
_match = re.match(r"https?://([^:]+)", _minio_endpoint)
PUBLIC_HOST = _match.group(1) if _match else "localhost"

# Database Config
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "tiktok_safety_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

# MinIO Config
MINIO_CONF = {
    "public_endpoint": _minio_endpoint,
    "bucket": os.getenv("MINIO_BUCKET_VIDEOS", "tiktok-raw-videos"),
    "bucket_audios": os.getenv("MINIO_BUCKET_AUDIOS", "tiktok-raw-audios"),
}

# External URLs (use PUBLIC_HOST for Tailscale access)
EXTERNAL_URLS = {
    "airflow": f"http://{PUBLIC_HOST}:8080",
    "minio_console": f"http://{PUBLIC_HOST}:9001",
    "minio_api": f"http://{PUBLIC_HOST}:9000",
    "spark_ui": f"http://{PUBLIC_HOST}:9090",
    "dashboard": f"http://{PUBLIC_HOST}:8501",
}

# Airflow Config
AIRFLOW_API_URL = "http://airflow-webserver:8080/api/v1/dags"
AIRFLOW_AUTH = (
    os.getenv("AIRFLOW_ADMIN_USERNAME", "admin"),
    os.getenv("AIRFLOW_ADMIN_PASSWORD", "admin"),
)

# App Config
APP_CONFIG = {
    "refresh_interval": 30000,  # 30 seconds
    "max_records": 500,
    "items_per_page": 12,
}

# Blacklist keywords for content moderation
BLACKLIST_KEYWORDS = [
    "gaixinh",
    "gái xinh",
    "nhảy sexy",
    "nhay sexy",
    "khoe body",
    "khoe dáng",
    "bikini",
    "hở bạo",
    "sugar baby",
    "sugarbaby",
    "sgbb",
    "nuôi baby",
    "phòng the",
    "phong the",
    "chuyện người lớn",
    "18+",
    "lộ clip",
    "khoe hàng",
    "đánh nhau",
    "danh nhau",
    "đánh ghen",
    "danh ghen",
    "bóc phốt",
    "boc phot",
    "drama",
    "showbiz",
    "xăm trổ",
    "giang hồ",
    "biến căng",
    "check var",
    "hỗn chiến",
    "bạo lực học đường",
    "chửi bậy",
    "tài xỉu",
    "xóc đĩa",
    "xoc dia",
    "nổ hũ",
    "no hu",
    "bắn cá",
    "soi kèo",
    "cho vay",
    "bốc bát họ",
    "kiếm tiền online",
    "lừa đảo",
    "app vay tiền",
    "nhóm kéo",
    "kéo tài xỉu",
    "cá độ",
    "lô đề",
    "bay lắc",
    "dân chơi",
    "trà đá vỉa hè",
    "nhậu nhẹt",
    "say rượu",
    "hút thuốc",
    "vape",
    "pod",
    "cần sa",
    "ke",
    "kẹo",
    "gọi vong",
    "xem bói",
    "bùa ngải",
    "kumathong",
    "kumanthong",
    "tâm linh",
]
