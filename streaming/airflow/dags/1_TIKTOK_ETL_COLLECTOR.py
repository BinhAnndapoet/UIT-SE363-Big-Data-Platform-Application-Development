from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Đường dẫn trong Docker Airflow (cấu trúc mới sau refactor)
INGESTION_PATH = "/opt/project/streaming/ingestion"

default_args = {
    "owner": "airflow",
    "retries": 0,  # Tắt retry tự động để tránh loop nếu lỗi code
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "1_TIKTOK_ETL_COLLECTOR",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    # [QUAN TRỌNG] Chỉ cho phép 1 Instance chạy tại 1 thời điểm
    max_active_runs=1,
    concurrency=1,
    tags=["etl", "source"],
) as dag:

    # 1. Kiểm tra Database
    check_infra = BashOperator(
        task_id="monitor_db_health",
        bash_command="pg_isready -h postgres -U user -d tiktok_safety_db",
    )

    # 2. Chạy Crawler (Xvfb Mode) - file renamed: crawler_links.py -> crawler.py
    crawl_task = BashOperator(
        task_id="crawl_tiktok_links",
        # Thêm timeout để tự kill nếu treo quá 45p
        bash_command=f"xvfb-run -a --server-args='-screen 0 1920x1080x24' python {INGESTION_PATH}/crawler.py",
        execution_timeout=timedelta(minutes=45),
    )

    check_infra >> crawl_task
