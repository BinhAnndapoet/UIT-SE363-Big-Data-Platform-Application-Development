# 🛡️ TikTok Safety Platform - Big Data Harmful Content Detection System

<div align="center">

**📚 Course**: SE363 - Big Data Platform Application Development  
**🏛️ Institution**: University of Information Technology (UIT) - VNU-HCM  
**👥 Authors**: [KhoiBui16](https://github.com/KhoiBui16) • [BinhAnndapoet](https://github.com/BinhAnndapoet) • [PhamQuocNam](https://github.com/PhamQuocNam)

---

![TikTok Safety](https://img.shields.io/badge/TikTok-Safety-ff0050?style=for-the-badge&logo=tiktok&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Apache Spark](https://img.shields.io/badge/Apache-Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache-Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)

**A Big Data platform for detecting harmful content on TikTok using multimodal AI (Text + Video + Fusion)**

</div>

---

## 📋 Project Overview

This project implements a **Lambda Architecture** based Big Data platform for real-time detection of harmful content on TikTok videos. The system combines:

- **Batch Processing**: Training multimodal AI models (Text, Video, Fusion)
- **Stream Processing**: Real-time video analysis using Apache Spark Streaming
- **Serving Layer**: Streamlit Dashboard for monitoring and content moderation

### Key Capabilities

- 🔍 **Multimodal Analysis**: Combines text (captions, comments) and video frame analysis
- ⚡ **Real-time Processing**: Stream processing with Kafka + Spark
- 🤖 **AI-Powered Detection**: State-of-the-art models for content classification
- 📊 **Interactive Dashboard**: Real-time monitoring and content audit tools
- 🔄 **MLflow Integration**: Model versioning and auto-update capabilities

---

## 📑 Table of Contents

1. [Quick Start](#-quick-start)
2. [Project Structure](#-project-structure)
3. [Architecture](#️-architecture)
4. [Layer Architecture](#-layer-architecture)
5. [Airflow DAGs](#-airflow-dags)
6. [Data Flow](#-data-flow)
7. [Features](#-features)
8. [AI Models](#-ai-models)
9. [Data Crawling](#-data-crawling)
10. [Model Training](#-model-training)
11. [Installation Guide](#-installation-guide)
12. [Usage](#-usage)
13. [Testing](#-testing)
14. [Documentation](#-documentation)
15. [Troubleshooting](#-troubleshooting)
16. [Tech Stack](#️-tech-stack)
17. [Authors](#-authors)

---


## 🚀 Quick Start & Installation Guide

### Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Ubuntu 20.04+ / Windows 10+ (WSL2) | Ubuntu 22.04 |
| **Docker** | Docker Engine 20.10+ & Compose v2 | Latest |
| **Python** | 3.9+ | 3.10+ |
| **RAM** | 16GB | 32GB |
| **Storage** | 50GB free | 100GB+ |

### Step 1: Clone Repository

```bash
git clone https://github.com/BinhAnndapoet/UIT-SE363-Big-Data-Platform-Application-Development.git
cd UIT-SE363-Big-Data-Platform-Application-Development
```

### Step 2: Setup Environment

```bash
# Copy environment template
cp streaming/.env.example streaming/.env

# (Optional) Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies (for local development)
pip install -r requirements.txt
```

### Step 3: Setup Cookies (Required for Crawling)

1. Install Chrome extension **"Get cookies.txt LOCALLY"**
2. Login to TikTok in Chrome
3. Click extension → **"Export All Cookies"** → Save as `cookies.txt`
4. Copy to streaming folder:
   ```bash
   cp cookies.txt streaming/ingestion/cookies.txt
   ```

### Step 4: Download Data (Optional)

> **💡 Alternative**: Skip this step - the streaming pipeline will automatically crawl new videos!

| Folder | Download Link | Description |
|--------|---------------|-------------|
| `data/` | [Google Drive](https://drive.google.com) *(link TBD)* | Raw crawled videos (batch 1) |
| `data_1/` | [Google Drive](https://drive.google.com) *(link TBD)* | Raw crawled videos (batch 2) |
| `data_viet/` | [Google Drive](https://drive.google.com) *(link TBD)* | Vietnamese TikTok videos |

### Step 5: Run with Docker

```bash
cd streaming
chmod +x start_all.sh
./start_all.sh
```

**Alternative Docker Commands:**
```bash
# Manual start
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f spark-processor

# Stop all
docker compose down
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | - |
| **Airflow** | http://localhost:8080 | admin / admin |
| **MLflow** | http://localhost:5000 | - |
| **MinIO Console** | http://localhost:9001 | admin / password123 |
| **Spark Master** | http://localhost:9090 | - |

---

## 🎮 Usage

### Running the Pipeline

1. **Open Airflow** at http://localhost:8080 (login: admin/admin)

2. **Trigger DAG 1**: `1_TIKTOK_ETL_COLLECTOR`
   - Crawls TikTok videos by hashtags
   - Wait for completion (Success status)

3. **Trigger DAG 2**: `2_TIKTOK_STREAMING_PIPELINE`
   - Downloads videos to MinIO
   - Runs AI inference with Spark
   - Stores results in PostgreSQL
   - **Auto-loops** for continuous processing

4. **Trigger DAG 3**: `3_MODEL_RETRAINING` (Optional/Scheduled)
   - Checks for new data and performance drift
   - Retrains models on Spark Cluster
   - Registers new best models to MLflow (auto-updates pipeline)

5. **Monitor Dashboard** at http://localhost:8501

---

## 🧪 Testing

### Shell Scripts (Ubuntu)

```bash
cd streaming

# Run all tests
./tests/run_all_tests.sh

# Test individual layers
./tests/test_layer1_infrastructure.sh  # Docker, Kafka, MinIO
./tests/test_layer2_ingestion.sh       # Crawler, Downloader
./tests/test_layer3_processing.sh      # Spark, AI Models
./tests/test_layer4_dashboard.sh       # Streamlit Dashboard
```

### Python Tests

```bash
cd streaming
pytest tests/ -v
```

---

## 📁 Project Structure

```bash
UIT-SE363-Big-Data-Platform-Application-Development/
├── streaming/                          # 🚀 Real-time Pipeline Root
│   ├── airflow/
│   │   └── dags/                       # ⚡ Airflow DAGs
│   │       ├── 1_TIKTOK_ETL_COLLECTOR.py
│   │       ├── 2_TIKTOK_STREAMING_PIPELINE.py
│   │       └── 3_MODEL_RETRAINING.py
│   ├── ingestion/                      # 📥 Data Ingestion Layer
│   │   ├── clients/                    # External clients
│   │   │   └── minio_kafka_clients.py
│   │   ├── crawler.py                  # TikTok crawler (Selenium)
│   │   ├── downloader.py               # Video downloader
│   │   ├── main_worker.py              # Main ingestion worker
│   │   └── config.py
│   ├── processing/                     # 🧠 Stream Processing Layer
│   │   └── spark_processor.py          # Spark AI Inference Job
│   ├── mlflow/                         # 🔄 MLOps & Model Registry
│   │   ├── client.py                   # Registry client wrapper
│   │   └── model_updater.py            # Model auto-updater logic
│   ├── dashboard/                      # 📊 Streamlit Dashboard
│   │   ├── app.py                      # Main dashboard entrypoint
│   │   ├── config.py
│   │   ├── helpers.py
│   │   ├── styles.py
│   │   ├── page_modules/               # UI Components
│   │   └── Dockerfile.dashboard
│   ├── spark/                          # 🐳 Spark Docker Config
│   │   └── Dockerfile
│   ├── tests/                          # 🧪 Comprehensive Test Suite
│   │   ├── run_all_tests.sh            # Master test script
│   │   ├── test_layer1_infrastructure.sh
│   │   ├── test_layer2_ingestion.sh
│   │   ├── test_layer3_processing.sh
│   │   ├── test_layer4_dashboard.sh
│   │   ├── test_layer5_mlflow.sh
│   │   ├── test_mlflow.py              # Unit tests
│   │   ├── test_dashboard.py
│   │   ├── test_db_layer.py
│   │   └── ... (helper scripts)
│   ├── docker-compose.yml              # Main Infrastructure Config
│   ├── start_all.sh                    # One-click Startup Script
│   ├── link_host.sh                    # Host URL generator
│   └── .env                            # Environment Config
│
├── train_eval_module/                  # 🤖 AI Model Training & Eval
│   ├── text/                           # Text Model (CafeBERT)
│   │   ├── src/                        # Model source code
│   │   ├── train.py
│   │   ├── test.py
│   │   ├── text_configs.py
│   │   └── output/uitnlp_CafeBERT/     # Spec: 1024-dim
│   ├── video/                          # Video Model (VideoMAE)
│   │   ├── src/
│   │   ├── train.py
│   │   ├── test.py
│   │   ├── video_configs.py
│   │   └── output/MCG-NJU_videomae.../ # Spec: 768-dim
│   ├── fusion/                         # Multimodal Fusion
│   │   ├── src/
│   │   ├── train.py
│   │   ├── test.py
│   │   ├── fusion_configs.py
│   │   └── output/fusion_videomae/     # Retrained 1024-dim Text + 768-dim Video
│   ├── audio/                          # Audio Model (Experimental)
│   │   ├── src/
│   │   ├── train.py
│   │   └── ...
│   ├── scripts/                        # Utility Scripts
│   │   ├── push_hf_model.py            # HuggingFace Uploader
│   │   ├── split_data.py
│   │   └── check_paths.py
│   └── shared_utils/                   # Common Utilities
│       ├── file_utils.py
│       ├── logger.py
│       ├── mlflow_logger.py
│       └── processing.py
│
├── crawl_scripts/                      # 🕷️ Standalone Crawling Utils
│   ├── ScrapingVideoTiktok.py          # Main video scraper
│   ├── find_tiktok_links.py            # Link finder by hashtag
│   ├── create_sub_samples_tiktok_links.py
│   ├── crawl_tiktok_links_update_v1.py
│   └── crawl_tiktok_links_update_viet.py
│
├── notebooks/                          # 📓 Analysis & Experiments
│   ├── ScrapingVideoTiktok.ipynb
│   ├── create_sub_samples_tiktok_links.ipynb
│   ├── eda.ipynb
│   └── audio_trial.ipynb
│
├── docs/                               # 📚 Project Documentation
│   ├── streaming/
│   │   ├── 01_PROJECT_OVERVIEW.md
│   │   ├── 02_LAYER_ARCHITECTURE.md
│   │   ├── 03_DASHBOARD_PAGES.md
│   │   ├── 04_SETUP_GUIDE.md
│   │   ├── 05_TESTING_GUIDE.md
│   │   └── 06_API_REFERENCE.md
│   └── mlflow/
│       └── MLFLOW_INTEGRATION_GUIDE.md
│
├── processed_data/                     # 💾 Processed Datasets (CSV)
├── data/                               # 📦 Raw Data Storage (Images/Videos)
└── requirements.txt                    # 🐍 Project Dependencies (Root)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LAMBDA ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   TikTok     │───▶│   Crawler    │───▶│   MinIO (Storage)    │   │
│  │   Videos     │    │   Service    │    │   Videos & Audios    │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│                             │                        │               │
│                             ▼                        ▼               │
│                      ┌──────────────┐    ┌──────────────────────┐   │
│                      │    Kafka     │───▶│   Spark Streaming    │   │
│                      │   Broker     │    │   (AI Inference)     │   │
│                      └──────────────┘    └──────────────────────┘   │
│                                                      │               │
│                                                      ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   Streamlit  │◀───│  PostgreSQL  │◀───│   Processed Results  │   │
│  │   Dashboard  │    │   Database   │    │                      │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| **Dashboard** | `8501` | Streamlit monitoring UI |
| **Airflow** | `8080` | DAG scheduling & orchestration |
| **Spark Master** | `9090` | Spark cluster management |
| **Spark Processor** | - | AI inference streaming job |
| **Kafka** | `9092` | Message broker |
| **MinIO** | `9000`, `9001` | Object storage (videos/audios) |
| **PostgreSQL** | `5432` | Results database |
| **MLflow** | `5000` | Model registry & tracking |

---

## 🏗️ Layer Architecture

The system follows a **9-layer architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Layer 9: MODEL REGISTRY        │  MLflow (port 5000)                  │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 8: PRESENTATION          │  Streamlit Dashboard (port 8501)    │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 7: DATA STORAGE          │  PostgreSQL (processed_results)     │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 6: ORCHESTRATION         │  Airflow DAGs (port 8080)           │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 5: STREAM PROCESSING     │  Spark Streaming + AI Models        │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 4: DATA INGESTION        │  Crawler → Downloader → Producer    │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 3: OBJECT STORAGE        │  MinIO (videos, audios)             │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 2: MESSAGE QUEUE         │  Kafka + Zookeeper                  │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 1: INFRASTRUCTURE        │  Docker Network, Volumes            │
└────────────────────────────────────────────────────────────────────────┘
```

### Layer Details

| Layer | Components | Key Files |
|-------|------------|-----------|
| **L1: Infrastructure** | Docker Network, Volumes | [docker-compose.yml](streaming/docker-compose.yml) |
| **L2: Message Queue** | Kafka (9092), Zookeeper | [docker-compose.yml](streaming/docker-compose.yml) |
| **L3: Object Storage** | MinIO (9000/9001) | [minio_kafka_clients.py](streaming/ingestion/clients/minio_kafka_clients.py) |
| **L4: Data Ingestion** | Crawler, Downloader, Producer | [crawler.py](streaming/ingestion/crawler.py), [main_worker.py](streaming/ingestion/main_worker.py) |
| **L5: Stream Processing** | Spark + AI Models | [spark_processor.py](streaming/processing/spark_processor.py) |
| **L6: Orchestration** | Airflow DAGs | [airflow/dags/](streaming/airflow/dags/) |
| **L7: Data Storage** | PostgreSQL | [docker-compose.yml](streaming/docker-compose.yml), [infra/postgres/](streaming/infra/postgres/) |
| **L8: Presentation** | Streamlit Dashboard | [dashboard/app.py](streaming/dashboard/app.py) |
| **L9: Model Registry** | MLflow Server | [mlflow/client.py](streaming/mlflow/client.py), [model_updater.py](streaming/mlflow/model_updater.py) |

### MLflow Layer (L9) - Model Registry & Auto-Update

**Purpose**: Automatic model versioning, tracking, and production updates based on F1-score.

**Features:**
- 📊 **Experiment Tracking**: Log metrics, params, artifacts for each training run
- 📦 **Model Registry**: Version control for text, video, and fusion models
- 🔄 **Auto-Update**: Every **2 minutes (testing)** or **30 minutes (default)**, Spark checks for better models in MLflow
- 📈 **F1-Score Based**: Only updates if new model surpasses threshold:

| Model | Minimum F1 Threshold |
|-------|---------------------|
| Text | 0.75 |
| Video | 0.70 |
| Fusion | 0.80 |

**How it works:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Training Job   │────►│  MLflow Server  │◄────│ Spark Processor │
│ (logs metrics)  │     │  (port 5000)    │     │ (checks every   │
└─────────────────┘     └─────────────────┘     │  2 or 30 minutes)│
                               │                └─────────────────┘
                               ▼
                     ┌─────────────────────┐
                     │ If new F1 > current │
                     │ → Download & Update │
                     └─────────────────────┘
```

---

## 🔄 Airflow DAGs

### DAG 1: `1_TIKTOK_ETL_COLLECTOR`

**Purpose**: Crawl TikTok videos by hashtags

```
┌─────────────────────┐      ┌────────────────────────┐
│ monitor_db_health   │ ───► │   crawl_tiktok_links   │
│ (pg_isready check)  │      │  (Selenium + Xvfb)     │
└─────────────────────┘      └────────────────────────┘
```

| Task | Description | Timeout |
|------|-------------|---------|
| `monitor_db_health` | Check PostgreSQL connection | - |
| `crawl_tiktok_links` | Crawl TikTok with Selenium (headless) | 45 min |

### DAG 2: `2_TIKTOK_STREAMING_PIPELINE`

**Purpose**: Download videos, run AI inference, continuous processing loop

```
┌──────────────────┐   ┌──────────────────┐   ┌─────────────────────┐
│ prepare_environ  │──►│ check_kafka_infra│──►│ run_ingestion_worker│
└──────────────────┘   └──────────────────┘   └─────────────────────┘
                                                        │
         ┌─────────────────────────────────────────────┘
         ▼
┌────────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ verify_spark_result│──►│ wait_30s_cooldown│──►│ loop_self_trigger│
│   (SQL Sensor)     │   │                 │   │  (Auto-restart)  │
└────────────────────┘   └─────────────────┘   └─────────────────┘
```

| Task | Description |
|------|-------------|
| `prepare_environment` | Check queue file exists |
| `check_kafka_infra` | Verify Kafka is healthy |
| `run_ingestion_worker` | Download → Upload MinIO → Send Kafka |
| `verify_spark_ai_result` | Wait for Spark processing |
| `wait_30s_cooldown` | Cooldown before next loop |
| `loop_self_trigger` | Self-trigger for continuous processing |

### DAG 3: `3_MODEL_RETRAINING`

**Purpose**: Automated model retraining & MLflow registration

```
┌────────────────┐     ┌──────────────────┐     ┌───────────────────┐    ┌────────────────┐
│ check_new_data │────►│ submit_spark_job │────►│ monitor_spark_job │───►│ notify_success │
└────────────────┘     │  (REST API)      │     │  (Polling)        │    └────────────────┘
                       └──────────────────┘     └───────────────────┘
```

| Task | Description |
|------|-------------|
| `check_new_data` | Validate if sufficient new data exists |
| `submit_training_job` | Submit training job to Spark Master (Cluster Mode) |
| `monitor_training_job` | Track job status until FINISHED |
| `notify_success` | Log completion and registration status |

---

## 📊 Data Flow

```
     TikTok Website
          │
          ▼ (1. Crawl)
    ┌─────────────┐
    │   Crawler   │ ───► tiktok_links_viet.csv
    └─────────────┘
          │
          ▼ (2. Download)
    ┌─────────────┐     ┌─────────┐
    │  Downloader │────►│  MinIO  │
    └─────────────┘     └─────────┘
          │
          ▼ (3. Produce)
    ┌─────────────┐     ┌─────────┐
    │   Producer  │────►│  Kafka  │
    └─────────────┘     └─────────┘
          │
          ▼ (4. AI Inference)
    ┌─────────────────────────────────┐
    │         Spark Processor         │
    │  ┌──────┐ ┌──────┐ ┌──────┐    │
    │  │ Text │ │Video │ │Fusion│    │
    │  └──────┘ └──────┘ └──────┘    │
    └─────────────────────────────────┘
          │
          ▼ (5. Store)
    ┌─────────────┐
    │  PostgreSQL │
    └─────────────┘
          │
          ▼ (6. Display)
    ┌─────────────┐
    │  Dashboard  │
    └─────────────┘
```

---

## ✨ Features

### 1. Analytics Dashboard
- **KPI Monitoring**: Total processed videos, harmful detection rate, average risk score
- **Visual Analysis**: Time-series charts and category distribution
- **Real-time Updates**: Live data refresh from PostgreSQL

### 2. System Operations
- **Pipeline Control**: Start/Stop crawler and streaming pipelines
- **Status Monitor**: Real-time container and service health checks
- **System Logs**: Centralized logging viewer

### 3. Content Audit
- **Gallery Mode**: Visual grid of processed videos with risk scores
- **Detail View**: In-depth analysis of individual videos
- **Table View**: Sortable/filterable data table

### 4. Database Manager
- **Table Browser**: Schema inspection and data preview
- **Query Tool**: Execute custom SQL queries
- **Statistics**: Database performance metrics

### 5. Project Info
- **Architecture Diagrams**: Visual system documentation
- **Data Pipeline Flow**: End-to-end data journey
- **AI Models Documentation**: Model specifications

---

## 🤖 AI Models

All models are available on HuggingFace Hub:

### Text Classification Model
**Repository**: [KhoiBui/tiktok-text-safety-classifier](https://huggingface.co/KhoiBui/tiktok-text-safety-classifier)

- **Base Model**: CafeBERT (uitnlp/CafeBERT)
- **Task**: Binary classification (safe/harmful)
- **Languages**: Vietnamese, English

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("KhoiBui/tiktok-text-safety-classifier")
model = AutoModelForSequenceClassification.from_pretrained("KhoiBui/tiktok-text-safety-classifier")
```

### Video Classification Model
**Repository**: [KhoiBui/tiktok-video-safety-classifier](https://huggingface.co/KhoiBui/tiktok-video-safety-classifier)

- **Base Model**: VideoMAE (MCG-NJU/videomae-base-finetuned-kinetics)
- **Task**: Binary classification (safe/harmful)
- **Input**: 16 video frames (224x224)

### Multimodal Fusion Model
**Repository**: [KhoiBui/tiktok-multimodal-fusion-classifier](https://huggingface.co/KhoiBui/tiktok-multimodal-fusion-classifier)

- **Architecture**: Late Fusion with Cross-Attention + Gating
- **Text Backbone**: KhoiBui/tiktok-text-safety-classifier (1024-dim XLM-RoBERTa compatible)
- **Video Backbone**: KhoiBui/tiktok-video-safety-classifier (768-dim VideoMAE)
- **Internal Weights**: 50% text + 50% video (trong Cross-Attention)
- **Status**: **Retrained & Fixed** (Jan 29, 2026) to resolve dimension mismatch (1024 vs 768).

### Inference Modes (Streaming Pipeline)

Spark Processor sử dụng chiến lược **auto-fallback** trong `spark_processor.py`:

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Thử load FUSION MODEL                              │
│    ✓ Thành công → Dùng FUSION mode (50-50 trained weights)  │
│    ✗ Thất bại  → Auto-fallback về LATE_SCORE                │
└─────────────────────────────────────────────────────────────┘
```

| Mode | Khi nào dùng | Models Used | Score Calculation |
|------|--------------|-------------|-------------------|
| **FUSION** | Default (nếu load được) | 1 Fusion model | End-to-end (50-50 trained) |
| **LATE_SCORE** | Fallback (khi FUSION fail) | 2 separate models | `text*0.3 + video*0.7` |

> **⚠️ Note**: FUSION is the primary mode with end-to-end trained model. LATE_SCORE is only used automatically when Fusion model fails to load.

### Rule-based Filtering (Pre-AI Check)

Before calling AI models, the system performs a quick check based on **60+ banned keywords** in Vietnamese, divided into 5 groups:

| Group | Content Type | Examples |
|-------|--------------|----------|
| 1 | Adult/Sexual content | 18+, sex, xxx |
| 2 | Violence/Gang-related | fighting, knife, gun |
| 3 | Gambling/Fraud | casino, betting, ponzi |
| 4 | Social vices | drugs, narcotics |
| 5 | Superstition | fortune telling, black magic |

**Logic**: If text contains banned keyword → Immediately assign `score = 0.85` + `label = harmful` **WITHOUT calling AI** → Saves GPU resources.

### Streaming Inference Logic

```
┌────────────────────────────────────────────────────────────────┐
│  1. Kafka Consumer reads messages (max 5 offsets/trigger)      │
├────────────────────────────────────────────────────────────────┤
│  2. Download video from MinIO → Extract 16 frames (decord)     │
├────────────────────────────────────────────────────────────────┤
│  3. Rule-based check (60+ keywords)                            │
│     ✓ Match → score=0.85, skip AI                              │
│     ✗ No match → Continue to AI                                │
├────────────────────────────────────────────────────────────────┤
│  4. AI Inference (UDFs - Lazy Loading)                         │
│     - Text UDF: CafeBERT (max 256 tokens)                      │
│     - Video UDF: VideoMAE (16 frames 224x224)                  │
├────────────────────────────────────────────────────────────────┤
│  5. Score Fusion: text*0.3 + video*0.7 (configurable)          │
│     - Threshold = 0.5 → final_decision                         │
├────────────────────────────────────────────────────────────────┤
│  6. PostgreSQL UPSERT (10 columns + processed_at)              │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Dataset Statistics

### Data Sources

| Folder | Videos | Description |
|--------|--------|-------------|
| `data/` | 959 | Original dataset (mixed languages) |
| `data_1/` | 838 | Supplementary dataset |
| `data_viet/` | 818 | Vietnamese-only dataset |
| **Total Collected** | **2,615** | - |
| **After Filtering** | **1,820** | Removed corrupt/short/no-text videos |

### Train/Val/Test Split (80:10:10)

| Split | Samples | Safe | Harmful |
|-------|---------|------|---------|
| Train | 1,456 | ~1,100 | ~356 |
| Val | 182 | 137 | 45 |
| Test | 182 | 137 | 45 |

> **Note**: Video test set = 180 samples (2 videos corrupt/too short for VideoMAE)

---

## 📈 Experimental Results

### Text Models (Test Set = 182 samples)

| Model | Accuracy | F1-Harmful | Precision | Recall |
|-------|----------|------------|-----------|--------|
| **CafeBERT** | **79.7%** | **57.5%** | 59.5% | 55.6% |
| XLM-RoBERTa | 75.8% | 38.9% | 50.0% | 31.8% |
| DistilBERT | 70.3% | 46.0% | 48.6% | 43.7% |

### Video Models (Test Set = 180 samples)

| Model | Accuracy | F1-Harmful | Precision | Recall |
|-------|----------|------------|-----------|--------|
| **VideoMAE** | **87.2%** | **87.8%** | 88.5% | 87.1% |
| TimeSformer | 85.6% | 86.9% | 87.2% | 86.6% |
| ViViT | 78.3% | 81.2% | 79.4% | 83.1% |

### Fusion Model (Test Set = 182 samples)

| Metrics | Value |
|---------|-------|
| Accuracy | 79.1% |
| F1-Weighted | 79.4% |
| F1-Harmful | 60.0% |
| Precision-Harmful | 57.0% |
| Recall-Harmful | 62.2% |

**Confusion Matrix:**
```
                    Predicted
                 Safe    Harmful
Actual Safe       116       21
Actual Harmful     17       28
```

---

## ⚡ Performance Metrics

| Metric | Value |
|--------|-------|
| **Throughput** | 1.66 videos/sec |
| **Hourly Capacity** | ~6,000 videos/hour |
| **Latency** | < 2 seconds per video |
| **Frame Extraction** | 0.2 sec/video |
| **VideoMAE Inference** | 0.4 sec/video |
| **DB Write** | 0.05 sec/batch |

> Tested on: 32GB RAM, GPU with 4GB+ VRAM

---

## 🕷️ Data Crawling

### Using Crawl Scripts (Local)

The `crawl_scripts/` folder contains scripts for collecting TikTok data:

```bash
cd crawl_scripts

# 1. Prepare cookies.txt (required for authentication)
# Export cookies from Chrome using "Get cookies.txt LOCALLY" extension
# Save as cookies.txt in crawl_scripts/

# 2. Find TikTok video links by hashtags
python find_tiktok_links.py --hashtag "funny" --max_videos 100

# 3. Download videos from collected links
python ScrapingVideoTiktok.py
```

### Using Airflow DAGs (Streaming Pipeline)

```bash
# 1. Start the streaming infrastructure
cd streaming
./start_all.sh

# 2. Access Airflow at http://localhost:8080 (admin/admin)

# 3. Trigger DAG "1_TIKTOK_ETL_COLLECTOR"
#    - Crawls TikTok videos by hashtags
#    - Saves links to CSV file

# 4. Trigger DAG "2_TIKTOK_STREAMING_PIPELINE"
#    - Downloads videos to MinIO
#    - Sends to Kafka for processing
```

### Data Output Structure

```
data/
├── crawl/
│   └── tiktok_links_viet.csv    # Crawled video URLs
├── videos/
│   └── {video_id}.mp4           # Downloaded videos
└── audios/
  └── {video_id}.wav           # Extracted audio (optional)
```

---

## 🏋️ Model Training

> For detailed training instructions, see [train_eval_module/README.md](train_eval_module/README.md)

### Prerequisites

```bash
cd train_eval_module

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Data Preparation (Required Before Training)

> ⚠️ **IMPORTANT**: After crawling data, you MUST run these scripts to prepare train/val/test splits before training any model.

**Step 1: Check System Paths & Data Status**

```bash
cd train_eval_module

# Verify all paths and check if data files exist
python scripts/check_paths.py
```

This script checks:
- Raw video folders (harmful/not_harmful)
- Audio processed directory
- Text labels CSV
- Master Index JSON files (train/val/test)

**Step 2: Create Train/Val/Test Splits**

```bash
# Generate data splits (80% train, 10% val, 10% test)
python scripts/split_data.py
```

This script creates:
- `data_splits/master_train.json`, `master_val.json`, `master_test.json` (Video/Audio)
- `processed_data/text/train_split.csv`, `val_split.csv`, `test_split.csv` (Text)
- `processed_data/fusion/train_fusion.json`, `val_fusion.json`, `test_fusion.json` (Fusion)

**Step 3: Verify Splits**

```bash
# Re-run check to confirm all split files are ready
python scripts/check_paths.py
```

Expected output: `🟢 Dữ liệu Index ĐÃ SẴN SÀNG.`

### Train Text Model

```bash
# Train CafeBERT (Vietnamese - recommended)
python -m text.train --model_idx 0 --metric_type eval_f1

# Train XLM-RoBERTa (Multilingual)
python -m text.train --model_idx 1 --metric_type eval_f1
```

| Model | Index | Best For |
|-------|-------|----------|
| uitnlp/CafeBERT | 0 | Vietnamese text |
| xlm-roberta-base | 1 | Mixed languages |
| distilbert-base-multilingual-cased | 2 | Lighter/faster |

### Train Video Model

```bash
# Train VideoMAE (recommended)
python -m video.train --model_idx 0

# Train TimeSformer
python -m video.train --model_idx 1
```

### Train Fusion Model

> ⚠️ Requires pre-trained text and video models

```bash
# Train Late Fusion (text + video)
python -m fusion.train
```

### Push to HuggingFace Hub

```bash
huggingface-cli login

python scripts/push_hf_model.py \
    --model_path text/output/uitnlp_CafeBERT/train/best_checkpoint \
  --repo-id your-username/tiktok-text-safety-classifier
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [01_PROJECT_OVERVIEW.md](docs/streaming/01_PROJECT_OVERVIEW.md) | Project introduction |
| [02_LAYER_ARCHITECTURE.md](docs/streaming/02_LAYER_ARCHITECTURE.md) | Architecture details |
| [03_DASHBOARD_PAGES.md](docs/streaming/03_DASHBOARD_PAGES.md) | Dashboard usage guide |
| [04_SETUP_GUIDE.md](docs/streaming/04_SETUP_GUIDE.md) | Installation guide |
| [05_TESTING_GUIDE.md](docs/streaming/05_TESTING_GUIDE.md) | Testing documentation |
| [MLFLOW_INTEGRATION_GUIDE.md](docs/mlflow/MLFLOW_INTEGRATION_GUIDE.md) | MLflow setup |

---

## 🔧 Troubleshooting

### Common Issues

**1. Docker containers not starting:**
```bash
docker compose logs <service-name>
docker compose restart <service-name>
```

**2. Spark processor failing:**
```bash
docker logs spark-processor -f
```

**3. Database connection issues:**
```bash
docker exec postgres pg_isready -U user -d tiktok_safety_db
```

**4. Reset everything:**
```bash
cd streaming
docker compose down -v
rm -rf state/
./start_all.sh
```

---

## 🛠️ Tech Stack

### Core Technologies

| Category | Technology | Version |
|----------|------------|---------|
| **Language** | Python | 3.9+ |
| **Container** | Docker & Docker Compose | 20.10+ |
| **Stream Processing** | Apache Spark | 3.5.0 |
| **Message Queue** | Apache Kafka | 7.5.0 |
| **Object Storage** | MinIO | Latest |
| **Database** | PostgreSQL | 15 |
| **Orchestration** | Apache Airflow | 2.8.1 |
| **ML Tracking** | MLflow | 2.8.1 |
| **Dashboard** | Streamlit | 1.28+ |

### AI/ML Frameworks

| Framework | Purpose |
|-----------|---------|
| PyTorch | Deep learning backend |
| Transformers | Pre-trained models |
| CafeBERT | Vietnamese text classification |
| VideoMAE | Video frame analysis |

### Supporting Tools

| Tool | Purpose |
|------|---------|
| Selenium + Chrome | Web scraping |
| FFmpeg | Audio extraction |
| Decord | Video frame extraction |
| kafka-python | Kafka client |

---

## 👥 Authors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/KhoiBui16">
        <img src="https://github.com/KhoiBui16.png" width="100px;" alt="KhoiBui16"/><br />
        <sub><b>KhoiBui16</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/BinhAnndapoet">
        <img src="https://github.com/BinhAnndapoet.png" width="100px;" alt="BinhAnndapoet"/><br />
        <sub><b>BinhAnndapoet</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/PhamQuocNam">
        <img src="https://github.com/PhamQuocNam.png" width="100px;" alt="PhamQuocNam"/><br />
        <sub><b>PhamQuocNam</b></sub>
      </a>
    </td>
  </tr>
</table>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ Star this repo if you find it helpful! ⭐**

Made with ❤️ by KhoiBui16, BinhAnndapoet & PhamQuocNam

</div>
