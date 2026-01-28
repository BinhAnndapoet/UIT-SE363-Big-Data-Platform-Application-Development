from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.sql import SqlSensor
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import time

# --- CẤU HÌNH ĐƯỜNG DẪN (CẤU TRÚC MỚI SAU REFACTOR) ---
INGESTION_DIR = "/opt/project/streaming/ingestion"
DATA_DIR = "/opt/project/streaming/data"
QUEUE_FILE = f"{DATA_DIR}/crawl/tiktok_links_viet.csv"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


def wait_before_loop():
    """Nghỉ 30s để hệ thống giải phóng tài nguyên và đóng log cũ"""
    print("⏳ Đang nghỉ 30 giây trước khi bắt đầu vòng lặp mới...")
    time.sleep(30)


with DAG(
    "2_TIKTOK_STREAMING_PIPELINE",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["streaming", "processing"],
) as dag:

    # 1. Kiểm tra file Queue
    prepare_env = BashOperator(
        task_id="prepare_environment",
        bash_command=f"test -s {QUEUE_FILE} && echo 'Environment Ready'",
    )

    # 2. Kiểm tra hạ tầng Kafka (Bỏ qua MinIO qua Bash để tránh lỗi DNS)
    check_infra = BashOperator(
        task_id="check_kafka_infra",
        bash_command="nc -zv kafka 29092 -w 2 && echo 'Kafka OK'",
    )

    # 3. Chạy Ingestion (Tải video & đẩy vào Kafka) - file renamed: main_worker.py
    run_ingestion = BashOperator(
        task_id="run_ingestion_worker",
        bash_command=f"python {INGESTION_DIR}/main_worker.py",
        execution_timeout=timedelta(minutes=30),
    )

    # 4. Sensor đợi dữ liệu (SỬA LẠI: Dùng mode poke để thoát ra ngay khi thấy dữ liệu)
    verify_spark = SqlSensor(
        task_id="verify_spark_ai_result",
        conn_id="postgres_pipeline",
        # SQL đơn giản để kiểm tra xem Spark có đang hoạt động không
        sql="SELECT CASE WHEN count(*) > 0 THEN 1 ELSE 0 END FROM processed_results;",
        poke_interval=20,
        timeout=300,
        mode="poke",  # FIX: Chuyển sang poke để chạy tuần tự
    )

    # 5. Task nghỉ để tránh lỗi log và quá tải container
    wait_task = PythonOperator(
        task_id="wait_30s_cooldown",
        python_callable=wait_before_loop,
        trigger_rule=TriggerRule.ALL_DONE,  # Luôn chạy kể cả sensor timeout
    )

    # 6. VÒNG LẶP: Tự kích hoạt lại
    loop_retry = TriggerDagRunOperator(
        task_id="loop_self_trigger",
        trigger_dag_id="2_TIKTOK_STREAMING_PIPELINE",
        trigger_rule=TriggerRule.ALL_DONE,  # Luôn lặp lại
        wait_for_completion=False,
    )

    # Luồng xử lý tuần tự
    (
        prepare_env
        >> check_infra
        >> run_ingestion
        >> verify_spark
        >> wait_task
        >> loop_retry
    )
