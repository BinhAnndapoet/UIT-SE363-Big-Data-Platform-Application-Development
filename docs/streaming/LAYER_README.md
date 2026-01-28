# 🏗️ STREAMING LAYER ARCHITECTURE & RUN GUIDE

> **Project:** TikTok Safety Real-Time Detection Platform  
> **Updated:** 2026-01-22

---

## 📋 TABLE OF CONTENTS

1. [Architecture Overview](#1-architecture-overview)
2. [Layer 1: Ingestion Layer](#2-layer-1-ingestion-layer)
3. [Layer 2: Spark Processing Layer](#3-layer-2-spark-processing-layer)
4. [Layer 3: Database Layer](#4-layer-3-database-layer)
5. [Layer 4: Dashboard Layer](#5-layer-4-dashboard-layer)
6. [Orchestration Layer (Airflow)](#6-orchestration-layer-airflow)
7. [MLOps Layer (MLflow)](#7-mlops-layer-mlflow)
8. [Docker Configuration](#8-docker-configuration)
9. [Quick Start](#9-quick-start)

---

## 1. ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION (Layer 1)                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Crawler   │───►│  Downloader │───►│ Audio Proc  │───►│   MinIO     │   │
│  │ (TikTok)    │    │ (yt-dlp)    │    │ (ffmpeg)    │    │ (S3 Store)  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘   │
│                                                                   │          │
│                              ▼ Kafka Message                      │          │
├───────────────────────────────────────────────────────────────────┼──────────┤
│                        SPARK PROCESSING (Layer 2)                  │          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │          │
│  │ Text Model  │    │Video Model  │    │Fusion Model │◄───────────┘          │
│  │ (CafeBERT)  │    │ (VideoMAE)  │    │ (Attention) │                       │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                       │
│         └──────────────────┴──────────────────┘                              │
│                              ▼                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                        DATABASE (Layer 3)                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL: video_predictions, system_logs                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────────┤
│                        DASHBOARD (Layer 4)                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Streamlit Dashboard: Real-time monitoring & visualization              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. LAYER 1: INGESTION LAYER

### 📂 Directory Structure
```
streaming/ingestion/
├── crawler.py          # TikTok hashtag crawler (Selenium)
├── downloader.py       # Video downloader (yt-dlp)
├── audio_processor.py  # Audio extraction (ffmpeg)
├── main_worker.py      # Main ingestion worker
├── config.py           # Configuration
└── clients/
    └── minio_kafka_clients.py  # MinIO & Kafka clients
```

### 🔧 Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Crawler | Selenium + Chrome | Crawl TikTok hashtags for video links |
| Downloader | yt-dlp | Download videos from TikTok URLs |
| Audio Processor | ffmpeg | Extract audio from videos |
| Storage | MinIO (S3) | Store videos & audios |
| Messaging | Kafka | Send metadata to Spark processor |

### 🚀 How to Run

```bash
# Run unit tests
./scripts/run_ingestion.sh test

# Run crawler
./scripts/run_ingestion.sh crawler

# Run main worker (requires Kafka, MinIO)
./scripts/run_ingestion.sh worker
```

### ⚙️ Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka broker address |
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO server URL |
| `MINIO_ROOT_USER` | `admin` | MinIO username |
| `MINIO_ROOT_PASSWORD` | `password123` | MinIO password |
| `INPUT_CSV_PATH` | `data/crawl/tiktok_links_viet.csv` | Input CSV path |

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Kafka | 29092 | 9092 |
| MinIO API | 9000 | 9000 |
| MinIO Console | 9001 | 9001 |

---

## 3. LAYER 2: SPARK PROCESSING LAYER

### 📂 Directory Structure
```
streaming/processing/
├── spark_processor.py    # Main Spark streaming processor
└── __init__.py

streaming/spark/
├── Dockerfile            # Spark container with AI dependencies
└── requirements.txt      # Python dependencies
```

### 🔧 Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Text Model | CafeBERT / XLM-RoBERTa | Vietnamese text classification |
| Video Model | VideoMAE | Video frame classification |
| Fusion Model | Late Fusion (Attention) | Multimodal classification |
| Stream Processing | Spark Structured Streaming | Real-time Kafka consumption |

### 🚀 How to Run

```bash
# Run unit tests
./scripts/run_spark.sh test

# Run via Docker (recommended)
./scripts/run_spark.sh docker

# View logs
docker logs -f spark-processor
```

### ⚙️ Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `USE_FUSION_MODEL` | `true` | Enable fusion model |
| `TEXT_WEIGHT` | `0.3` | Weight for text model (0-1) |
| `DECISION_THRESHOLD` | `0.5` | Harmful classification threshold |
| `HF_MODEL_TEXT` | (empty) | HuggingFace model ID for text |
| `HF_MODEL_VIDEO` | (empty) | HuggingFace model ID for video |
| `HF_MODEL_FUSION` | (empty) | HuggingFace model ID for fusion |

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Spark Master | 7077 | 7077 |
| Spark Master UI | 8080 | 8081 |
| Spark Worker UI | 8081 | 8082 |

---

## 4. LAYER 3: DATABASE LAYER

### 📂 Structure
```
PostgreSQL Database: tiktok_safety_db

Tables:
├── video_predictions   # AI classification results
│   ├── video_id (PK)
│   ├── raw_text, human_label
│   ├── text_verdict, text_score
│   ├── video_verdict, video_score
│   ├── avg_score, final_decision
│   └── created_at
│
└── system_logs         # System logs
    ├── id (PK)
    ├── timestamp, level, message
    └── source
```

### 🚀 How to Run

```bash
# Run unit tests
./scripts/run_database.sh test

# Start PostgreSQL
./scripts/run_database.sh start

# Connect via psql
./scripts/run_database.sh connect

# View logs
./scripts/run_database.sh logs
```

### ⚙️ Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_USER` | `user` | Database user |
| `POSTGRES_PASSWORD` | `password` | Database password |
| `POSTGRES_DB` | `tiktok_safety_db` | Database name |

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| PostgreSQL | 5432 | 5432 |

---

## 5. LAYER 4: DASHBOARD LAYER

### 📂 Directory Structure
```
streaming/dashboard/
├── app.py              # Main Streamlit app
├── config.py           # Configuration
├── helpers.py          # Utility functions
├── styles.py           # CSS styles
├── Dockerfile.dashboard
└── page_modules/       # Page components
```

### 🚀 How to Run

```bash
# Via Docker (recommended)
docker compose up dashboard -d

# Local development
cd dashboard
streamlit run app.py
```

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Streamlit | 8501 | 8501 |

---

## 6. ORCHESTRATION LAYER (AIRFLOW)

### 📂 Directory Structure
```
streaming/airflow/
├── dags/
│   ├── 1_tiktok_etl_collector.py    # DAG 1: Crawl & Ingest
│   └── 2_tiktok_streaming_pipeline.py # DAG 2: Start Spark
├── Dockerfile.airflow
└── requirements.txt
```

### 🚀 DAG Workflow

1. **DAG 1: `1_TIKTOK_ETL_COLLECTOR`**
   - Crawl TikTok hashtags → Download videos → Upload to MinIO → Send to Kafka

2. **DAG 2: `2_TIKTOK_STREAMING_PIPELINE`**
   - Start Spark processor → Consume Kafka → Classify → Save to PostgreSQL

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Airflow Webserver | 8080 | 8080 |

### 🔐 Default Credentials
- **Username:** `admin`
- **Password:** `admin`

---

## 7. MLOPS LAYER (MLFLOW)

### 📂 Directory Structure
```
streaming/mlflow/
├── client.py           # MLflow client utilities
├── model_updater.py    # Auto-update mechanism
└── __init__.py

train_eval_module/shared_utils/
└── mlflow_logger.py    # Training script logger
```

### 🚀 How to Run

```bash
# Access MLflow UI
http://localhost:5000

# Push model to HuggingFace Hub
cd train_eval_module
python scripts/push_hf_model.py
```

### 📡 Ports

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| MLflow | 5000 | 5000 |

---

## 8. DOCKER CONFIGURATION

### 📂 Docker Files
```
streaming/
├── docker-compose.yml          # Main orchestration file
├── .env                        # Environment variables
├── .dockerignore               # Docker ignore rules
│
├── spark/Dockerfile            # Spark with AI libs
├── airflow/Dockerfile.airflow  # Airflow with custom deps
└── dashboard/Dockerfile.dashboard # Streamlit dashboard
```

### 🐳 Services in docker-compose.yml

| Service | Image | Purpose |
|---------|-------|---------|
| zookeeper | confluentinc/cp-zookeeper | Kafka coordination |
| kafka | confluentinc/cp-kafka | Message broker |
| minio | minio/minio | Object storage |
| minio-init | minio/mc | Bucket initialization |
| postgres | postgres:15 | Database |
| spark-master | bitnami/spark | Spark master |
| spark-worker | bitnami/spark | Spark worker |
| spark-processor | custom | AI processing |
| airflow-db | postgres:13 | Airflow metadata |
| airflow-init | custom | Airflow initialization |
| airflow-webserver | custom | Airflow UI |
| airflow-scheduler | custom | Airflow scheduler |
| mlflow | mlflow/mlflow | Model registry |
| dashboard | custom | Streamlit UI |

---

## 9. QUICK START

### Option 1: Full System (Recommended)

```bash
cd streaming

# Start all services
./scripts/run_docker_all.sh up

# Check status
./scripts/run_docker_all.sh status

# View logs
./scripts/run_docker_all.sh logs
```

### Option 2: Layer by Layer

```bash
# 1. Start infrastructure
docker compose up zookeeper kafka minio postgres -d

# 2. Run ingestion tests
./scripts/run_ingestion.sh test

# 3. Run spark tests
./scripts/run_spark.sh test

# 4. Run database tests
./scripts/run_database.sh test

# 5. Start full system
./scripts/run_docker_all.sh up
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:8501 | - |
| Airflow | http://localhost:8080 | admin/admin |
| MinIO | http://localhost:9001 | admin/password123 |
| MLflow | http://localhost:5000 | - |
| Spark UI | http://localhost:8081 | - |

---

> **Note:** All scripts support `--help` flag for detailed usage information.
