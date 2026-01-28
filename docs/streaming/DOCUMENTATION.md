# 📖 TikTok Big Data Pipeline - Tài liệu Hệ thống

> **Cập nhật:** 2024-01-01
> **Version:** 1.0.1
> **Test Status:** ✅ 37/37 tests passed

---

## 📁 Cấu trúc Folder Tổng quan

```
streaming/
├── docker-compose.yml          # Master orchestration (13+ services)
├── .env                         # Centralized environment variables
├── start_all.sh                 # ✅ Entry-point chính
├── link_host.sh                 # Port forwarding info (Tailscale)
├── DOCUMENTATION.md             # Tài liệu này
│
├── tests/                       # ✅ NEW - Test suite
│   └── test_all_layers.sh       # 37 tests cho 8 layers
│
├── state/                       # ✅ ACTIVE - Persistent volumes (16GB)
│   ├── minio_data/              # Video storage
│   ├── postgres_data/           # Database
│   ├── airflow_logs/            # DAG execution logs
│   ├── ivy2/                    # Spark dependencies cache
│   └── spark_checkpoints/       # Spark streaming state
│
├── airflow/                     # ✅ ACTIVE - DAG orchestration
│   ├── docker-compose-airflow.yml  # (Legacy, merged)
│   ├── Dockerfile.airflow          # Chrome + XVFB + Python
│   ├── dags/
│   │   ├── 1_TIKTOK_ETL_COLLECTOR.py      # Crawler DAG
│   │   └── 2_TIKTOK_STREAMING_PIPELINE.py # Ingestion DAG
│   ├── logs/
│   └── plugins/
│
├── dashboard/                   # ✅ ACTIVE - Streamlit UI
│   ├── Dockerfile.dashboard
│   ├── requirements.txt
│   └── app.py
│
├── tiktok-pipeline/             # ✅ ACTIVE - Core processing (714MB after cleanup)
│   ├── Dockerfile.spark
│   ├── data_viet/crawl/         # CSV data source (3612 lines)
│   ├── ingestion/               # Download + MinIO + Kafka
│   │   ├── config.py
│   │   ├── ingestion_main_worker.py
│   │   ├── crawler_links.py
│   │   ├── tiktok_downloader.py
│   │   ├── preprocess_audio.py
│   │   └── modules/
│   │       ├── ai_labeler.py
│   │       ├── data_cleaner.py
│   │       └── minio_kafka_clients.py
│   └── processing/
│       └── spark_processor.py   # Spark Streaming + AI Models
│
├── chrome_profile/              # ✅ ACTIVE - Selenium persistence
│   └── Default/                 # Chrome cookies/session
│
└── zookeeper/                   # ✅ ACTIVE - Config
    └── zoo.cfg

```

---

## 🔴 FOLDERS ĐÃ XÓA (Tiết kiệm ~4GB)

| Folder | Size trước | Lý do |
|--------|-----------|-------|
| `tiktok-pipeline/minio_data/` | 3.8GB | Duplicate của `state/minio_data/` |
| `tiktok-pipeline/kafka_data/` | 8KB | Empty, Kafka dùng internal volume |
| `tiktok-pipeline/postgres_data/` | 4KB | Empty, Postgres dùng `state/postgres_data/` |
| `tiktok-pipeline/zookeeper_data/` | 12KB | Empty, Zookeeper dùng internal config |
| `tiktok-pipeline/.ivy2/` | 116MB | Duplicate của `state/ivy2/` |

**✅ Đã xóa thành công!**

---

## 🔄 Pipeline Workflow Chi tiết

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AIRFLOW ORCHESTRATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DAG 1: 1_TIKTOK_ETL_COLLECTOR (Schedule: 6h)                               │
│  ┌──────────────────┐    ┌────────────────────┐                             │
│  │ monitor_db_health │───▶│ crawl_tiktok_links │                             │
│  │ (Check Postgres)  │    │ (Selenium + Chrome)│                             │
│  └──────────────────┘    └────────────────────┘                             │
│                                   │                                          │
│                                   ▼                                          │
│                          CSV: data_viet/crawl/                               │
│                          sub_tiktok_links_viet.csv                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DAG 2: 2_TIKTOK_STREAMING_PIPELINE (Schedule: None, Self-loop)             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────┐          │
│  │prepare_environment│─▶│check_kafka_infra│─▶│run_ingestion_worker│          │
│  └─────────────────┘   └─────────────────┘   └───────────────────┘          │
│                                                        │                     │
│                                                        ▼                     │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────┐          │
│  │loop_self_trigger│◀──│wait_30s_cooldown│◀──│verify_spark_result│          │
│  └─────────────────┘   └─────────────────┘   └───────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [1. CRAWL]          [2. DOWNLOAD]         [3. UPLOAD]                      │
│  ┌───────────┐       ┌───────────────┐     ┌───────────────┐                │
│  │ Selenium  │──CSV──▶│ TikTok API    │────▶│    MinIO      │                │
│  │ (Chrome)  │       │ (yt-dlp)      │     │ tiktok-raw-   │                │
│  │           │       │               │     │ videos bucket │                │
│  └───────────┘       └───────────────┘     └───────┬───────┘                │
│                              │                      │                        │
│                              ▼                      │                        │
│  [4. AUDIO EXTRACT]  ┌───────────────┐             │                        │
│                      │   ffmpeg      │◀────────────┘                        │
│                      │ .mp4 → .mp3   │                                      │
│                      └───────┬───────┘                                      │
│                              │                                              │
│                              ▼                                              │
│  [5. KAFKA MESSAGE]  ┌───────────────┐                                      │
│                      │    Kafka      │                                      │
│                      │ tiktok_raw_   │                                      │
│                      │ data topic    │                                      │
│                      └───────┬───────┘                                      │
│                              │                                              │
│                              ▼                                              │
│  [6. SPARK STREAMING]┌───────────────────────────────────────┐              │
│                      │         Spark Processor               │              │
│                      │  ┌─────────────────────────────────┐  │              │
│                      │  │ process_batch_with_upsert()     │  │              │
│                      │  │ ┌─────────┐ ┌─────────┐ ┌─────┐ │  │              │
│                      │  │ │CafeBERT │ │VideoMAE │ │Audio│ │  │              │
│                      │  │ │ (Text)  │ │ (Video) │ │(WIP)│ │  │              │
│                      │  │ └────┬────┘ └────┬────┘ └──┬──┘ │  │              │
│                      │  │      │           │         │     │  │              │
│                      │  │      ▼           ▼         ▼     │  │              │
│                      │  │   score_text  score_video score_a│  │              │
│                      │  │      │           │         │     │  │              │
│                      │  │      └─────┬─────┴─────────┘     │  │              │
│                      │  │            ▼                     │  │              │
│                      │  │   final_score = TEXT*0.6 +       │  │              │
│                      │  │               VIDEO*0.4          │  │              │
│                      │  └─────────────────────────────────┘  │              │
│                      └───────────────┬───────────────────────┘              │
│                                      │                                      │
│                                      ▼                                      │
│  [7. POSTGRES]       ┌───────────────────────────────────────┐              │
│                      │     tiktok_results table              │              │
│                      │  (UPSERT ON CONFLICT DO UPDATE)       │              │
│                      └───────────────┬───────────────────────┘              │
│                                      │                                      │
│                                      ▼                                      │
│  [8. DASHBOARD]      ┌───────────────────────────────────────┐              │
│                      │     Streamlit Dashboard               │              │
│                      │  - Real-time metrics                  │              │
│                      │  - Confusion matrix                   │              │
│                      │  - Time series charts                 │              │
│                      └───────────────────────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 Mô tả Chi tiết Từng File

### 🔧 Docker Compose & Configuration

| File | Mô tả |
|------|-------|
| `docker-compose.yml` | Master orchestration, 13+ services, tiktok-network |
| `.env` | Env vars: TEXT_WEIGHT=0.6, DECISION_THRESHOLD=0.5, KAFKA_STARTING_OFFSETS=latest |
| `start_all.sh` | Entry-point: create volumes → docker-compose up → wait healthy |
| `link_host.sh` | Display port forwarding info (Tailscale IP: 100.69.255.87) |

### 📦 Dockerfiles

| File | Base Image | Layers | Mô tả |
|------|------------|--------|-------|
| `tiktok-pipeline/Dockerfile.spark` | apache/spark:3.5.0 | 5 layers | System → PyTorch CPU → AI libs → Utils → Permissions |
| `dashboard/Dockerfile.dashboard` | python:3.10-slim | 3 layers | System → requirements → source |
| `airflow/Dockerfile.airflow` | apache/airflow:2.8.1 | 4 layers | System → Chrome/XVFB → Python deps → Scripts |

### 🌬️ Airflow DAGs

| File | Schedule | Tasks | Mô tả |
|------|----------|-------|-------|
| `1_TIKTOK_ETL_COLLECTOR.py` | 0 */6 * * * | 2 | Crawl TikTok links với Selenium headless |
| `2_TIKTOK_STREAMING_PIPELINE.py` | None | 6 | Self-loop: Ingestion → Spark verify → Wait → Loop |

### 🔄 Ingestion Module

| File | Function | Mô tả |
|------|----------|-------|
| `config.py` | Configuration | Paths, MinIO (minio:9000), Kafka (kafka:29092) |
| `ingestion_main_worker.py` | Main worker | Download → Audio extract → MinIO → Kafka |
| `tiktok_downloader.py` | Download | yt-dlp wrapper, retry logic |
| `preprocess_audio.py` | Audio | ffmpeg .mp4 → .mp3 |
| `crawler_links.py` | Crawl | Selenium + Chrome, hashtag search |
| `modules/ai_labeler.py` | AI | Text/Video/Audio inference |
| `modules/data_cleaner.py` | Clean | Text normalization |
| `modules/minio_kafka_clients.py` | Clients | MinIO upload, Kafka producer |

### ⚡ Processing Module

| File | Function | Mô tả |
|------|----------|-------|
| `spark_processor.py` | Spark Streaming | Read Kafka → AI Models → UPSERT Postgres |

### 📊 Dashboard

| File | Function | Mô tả |
|------|----------|-------|
| `app.py` | Streamlit | Real-time metrics, confusion matrix, charts |
| `requirements.txt` | Dependencies | streamlit, plotly, pandas, sqlalchemy, psycopg2 |

---

## 🐳 Docker Services (13+)

| Service | Port | Health Check | Depends On |
|---------|------|--------------|------------|
| zookeeper | 2181 | ruok | - |
| kafka | 9092, 29092 | kafka-topics.sh | zookeeper |
| minio | 9000, 9001 | /minio/health/live | - |
| minio-init | - | (one-shot) | minio |
| postgres | 5432 | pg_isready | - |
| spark-master | 8080, 7077 | curl :8080 | - |
| spark-worker | 8081 | curl :8081 | spark-master |
| spark-processor | - | (streaming) | spark-master, kafka, postgres |
| airflow-db | 5433 | pg_isready | - |
| airflow-init | - | (one-shot) | airflow-db |
| airflow-webserver | 8888 | curl :8080 | airflow-init |
| airflow-scheduler | - | (running) | airflow-init |
| dashboard | 8501 | curl :8501 | postgres |
| db-migrator | - | (one-shot) | postgres |

---

## 🔍 Dockerfile Layer Optimization Analysis

### ✅ tiktok-pipeline/Dockerfile.spark (OPTIMIZED)

```dockerfile
# Layer 1: System deps (rarely changes)
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 ...

# Layer 2: PyTorch CPU-only (large, stable)
RUN pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2+cpu ...

# Layer 3: AI libs (medium, occasional updates)
RUN pip install transformers decord ...

# Layer 4: Utils (small, may change)
RUN pip install boto3 minio kafka-python psycopg2-binary ...

# Layer 5: Permissions (always last)
RUN useradd -m sparkuser && chown -R sparkuser:sparkuser /app
```

**Verdict:** ✅ Tối ưu tốt, layers từ stable → volatile

### ✅ dashboard/Dockerfile.dashboard (OPTIMIZED)

```dockerfile
# Layer 1: System
RUN apt-get update && apt-get install -y libpq-dev

# Layer 2: Requirements (copy riêng để cache)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Layer 3: Source code (changes frequently)
COPY . .
```

**Verdict:** ✅ Đúng pattern: deps trước, source sau

### ✅ airflow/Dockerfile.airflow (OPTIMIZED)

```dockerfile
# Layer 1: System + Chrome + XVFB
RUN apt-get update && apt-get install -y chromium chromium-driver xvfb ...

# Layer 2: Python deps
RUN pip install selenium-wire webdriver-manager ...

# Layer 3: Copy scripts
COPY dags/ /opt/airflow/dags/
```

**Verdict:** ✅ Tối ưu tốt

---

## 📋 Environment Variables (.env)

```bash
# AI Model Weights
TEXT_WEIGHT=0.6          # Weight cho text model (60%)
VIDEO_WEIGHT=0.4         # Weight cho video model (40%)
AUDIO_WEIGHT=0.0         # Audio chưa implement

# Decision Threshold
DECISION_THRESHOLD=0.5   # >= 0.5 = harmful

# Kafka Settings
KAFKA_STARTING_OFFSETS=latest  # Chỉ đọc messages mới

# Postgres
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=tiktok_db

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=password123
```

---

## 🔗 Network & Ports (Tailscale Access)

**Tailscale IP:** `100.69.255.87`

| Service | Internal Port | External Access |
|---------|---------------|-----------------|
| Airflow UI | 8888 | http://100.69.255.87:8888 |
| Spark Master UI | 8080 | http://100.69.255.87:8080 |
| Spark Worker UI | 8081 | http://100.69.255.87:8081 |
| MinIO Console | 9001 | http://100.69.255.87:9001 |
| Dashboard | 8501 | http://100.69.255.87:8501 |
| Kafka | 9092 | 100.69.255.87:9092 |
| Postgres | 5432 | 100.69.255.87:5432 |

---

## 📊 Current Performance Metrics

- **Total Records:** 28
- **True Positives (TP):** 15
- **True Negatives (TN):** 7
- **False Positives (FP):** 0
- **False Negatives (FN):** 6
- **Accuracy:** 78.6%
- **Precision:** 100%
- **Recall:** 71.4%

---

## 📝 Changelog

### v1.0.0 (2024-01-01)
- TEXT_WEIGHT: 0.3 → 0.5 → 0.6 (reduce FN)
- Dashboard: Fixed SQLAlchemy warnings
- Dashboard: Fixed resample('H') → 'h'
- Spark: Fixed checkpoint permissions
- Added Tailscale IP to link_host.sh
