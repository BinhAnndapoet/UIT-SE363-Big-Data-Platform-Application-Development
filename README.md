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
9. [Installation Guide](#-installation-guide)
10. [Usage](#-usage)
11. [Testing](#-testing)
12. [Documentation](#-documentation)
13. [Troubleshooting](#-troubleshooting)
14. [Tech Stack](#️-tech-stack)
15. [Authors](#-authors)

---

## 🚀 Quick Start

### Clone Repository

```bash
git clone https://github.com/BinhAnndapoet/UIT-SE363-Big-Data-Platform-Application-Development.git
cd UIT-SE363-Big-Data-Platform-Application-Development
```

### Setup Environment

```bash
# Copy environment file
cp streaming/.env.example streaming/.env

# (Optional) Edit .env if needed
nano streaming/.env
```

### Download Data (Required for Training)

> **Note**: Raw data and audio files are not included in the repository due to size constraints. Download them from Google Drive:

| Folder | Download Link | Description |
|--------|---------------|-------------|
| `data/` | [Google Drive](https://drive.google.com) *(link TBD)* | Raw crawled videos (batch 1) |
| `data_1/` | [Google Drive](https://drive.google.com) *(link TBD)* | Raw crawled videos (batch 2) |
| `data_viet/` | [Google Drive](https://drive.google.com) *(link TBD)* | Vietnamese TikTok videos |
| `processed_data/audios/` | [Google Drive](https://drive.google.com) *(link TBD)* | Extracted audio files (.wav) |

**After downloading**, extract and place folders in the project root:

```
UIT-SE363-Big-Data-Platform-Application-Development/
├── data/                    # ← Extract here
├── data_1/                  # ← Extract here
├── data_viet/               # ← Extract here
└── processed_data/
    └── audios/              # ← Extract here
```

> **💡 Alternative**: If you **don't have the data**, you can run the **streaming pipeline** which will automatically crawl new videos for you. Skip to "Run with Docker" section.

### Setup TikTok Cookies (Required for Crawling)

> **Important**: TikTok requires authentication cookies to download videos. Without valid cookies, crawling will fail with 403 errors.

**Steps to get cookies:**

1. Install the Chrome extension **"Get cookies.txt LOCALLY"** from Chrome Web Store
2. Login to TikTok in Chrome
3. Click the extension icon and select **"Export All Cookies"**
4. Save the file as `cookies.txt`
5. Copy to the required location:
   ```bash
   # For streaming pipeline (Docker)
   cp cookies.txt streaming/ingestion/cookies.txt
   
   # For manual crawling scripts:
   cp cookies.txt crawl_scripts/cookies.txt
   ```

### Run with Docker (Ubuntu)

```bash
cd streaming
chmod +x start_all.sh
./start_all.sh
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | - |
| **Airflow** | http://localhost:8080 | admin / admin |
| **MinIO Console** | http://localhost:9001 | admin / password123 |
| **Spark Master** | http://localhost:9090 | - |
| **MLflow** | http://localhost:5000 | - |

---

## 📁 Project Structure

```
UIT-SE363-Big-Data-Platform-Application-Development/
│
├── streaming/                          # 🔄 Streaming Pipeline
│   ├── airflow/                        # Airflow configuration
│   │   └── dags/                       # DAG definitions
│   │       ├── 1_TIKTOK_ETL_COLLECTOR.py
│   │       └── 2_TIKTOK_STREAMING_PIPELINE.py
│   ├── dashboard/                      # Streamlit Dashboard
│   │   ├── app.py                      # Main entry point
│   │   └── page_modules/               # Page components
│   │       ├── dashboard_monitor.py
│   │       ├── system_operations.py
│   │       ├── content_audit.py
│   │       ├── database_manager.py
│   │       └── project_info.py
│   ├── ingestion/                      # Data Ingestion Layer
│   │   ├── crawler.py                  # TikTok crawler (Selenium)
│   │   ├── downloader.py               # Video downloader
│   │   ├── main_worker.py              # Main ingestion worker
│   │   └── clients/                    # External clients
│   │       ├── minio_client.py
│   │       └── kafka_client.py
│   ├── processing/                     # Stream Processing
│   │   └── spark_processor.py          # Spark AI inference
│   ├── mlflow/                         # MLflow Integration
│   │   ├── client.py                   # Model registry client
│   │   └── model_updater.py            # Auto-update mechanism
│   ├── spark/                          # Spark Docker config
│   ├── scripts/                        # Automation scripts
│   ├── tests/                          # Test files
│   │   ├── test_layer1_infrastructure.sh
│   │   ├── test_layer2_ingestion.sh
│   │   ├── test_layer3_processing.sh
│   │   ├── test_layer4_dashboard.sh
│   │   └── run_all_tests.sh
│   ├── docker-compose.yml              # Main compose file
│   ├── start_all.sh                    # Full startup script
│   ├── .env.example                    # Environment template
│   └── .env                            # Environment config (gitignored)
│
├── train_eval_module/                  # 🤖 Model Training
│   ├── text/                           # Text classification
│   │   ├── train_text_spark.py
│   │   └── output/uitnlp_CafeBERT/
│   ├── video/                          # Video classification
│   │   ├── train_video.py
│   │   └── output/MCG-NJU_videomae-base-finetuned-kinetics/
│   ├── fusion/                         # Multimodal fusion
│   │   ├── train_fusion.py
│   │   └── output/fusion_videomae/
│   ├── audio/                          # Audio (experimental)
│   ├── scripts/                        # Utility scripts
│   │   └── push_hf_model.py            # Push to HuggingFace Hub
│   └── shared_utils/                   # Common utilities
│
├── crawl_scripts/                      # 🕷️ Crawling Scripts
│   ├── ScrapingVideoTiktok.py          # Main video scraper
│   ├── crawl_tiktok_links_update_v1.py # Link crawler v1
│   ├── crawl_tiktok_links_update_viet.py # Link crawler (Vietnamese)
│   ├── create_sub_samples_tiktok_links.py # Sample creator
│   └── find_tiktok_links.py            # Link finder
│
├── notebooks/                          # 📓 Jupyter Notebooks
│   ├── ScrapingVideoTiktok.ipynb       # Web scraping notebook
│   ├── create_sub_samples_tiktok_links.ipynb
│   ├── eda.ipynb                       # Exploratory Data Analysis
│   └── audio_trial.ipynb               # Audio experiments
│
├── docs/                               # 📖 Documentation
│   ├── streaming/                      # Streaming docs
│   │   ├── 01_PROJECT_OVERVIEW.md
│   │   ├── 02_LAYER_ARCHITECTURE.md
│   │   ├── 03_DASHBOARD_PAGES.md
│   │   ├── 04_SETUP_GUIDE.md
│   │   ├── 05_TESTING_GUIDE.md
│   │   └── 06_API_REFERENCE.md
│   └── mlflow/                         # MLflow docs
│       └── MLFLOW_INTEGRATION_GUIDE.md
│
├── processed_data/                     # 📊 Processed Data
│   ├── text/                           # Text CSV files
│   └── fusion/                         # Fusion training data
│
└── data/                               # 📦 Raw Data
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

The system follows an **8-layer architecture**:

```
┌────────────────────────────────────────────────────────────────────────┐
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
| **L3: Object Storage** | MinIO (9000/9001) | [minio_client.py](streaming/ingestion/clients/minio_client.py) |
| **L4: Data Ingestion** | Crawler, Downloader, Producer | [crawler.py](streaming/ingestion/crawler.py), [main_worker.py](streaming/ingestion/main_worker.py) |
| **L5: Stream Processing** | Spark + AI Models | [spark_processor.py](streaming/processing/spark_processor.py) |
| **L6: Orchestration** | Airflow DAGs | [airflow/dags/](streaming/airflow/dags/) |
| **L7: Data Storage** | PostgreSQL | [db_migrator.py](streaming/db_migrator.py) |
| **L8: Presentation** | Streamlit Dashboard | [dashboard/app.py](streaming/dashboard/app.py) |

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

- **Architecture**: Late Fusion with Cross-Attention
- **Text Backbone**: XLM-RoBERTa-base
- **Video Backbone**: VideoMAE-base

---

## 📦 Installation Guide

### Prerequisites

- **OS**: Ubuntu 20.04+ or Windows 10+ with WSL2
- **Docker**: Docker Engine 20.10+ & Docker Compose v2
- **Python**: 3.9+
- **RAM**: Minimum 16GB (32GB recommended)

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
# .\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run Docker

```bash
cd streaming
chmod +x start_all.sh
./start_all.sh
```

---

## 🚀 Usage

### Running the Pipeline

1. **Open Airflow** at http://localhost:8080

2. **Trigger DAG 1**: `1_TIKTOK_ETL_COLLECTOR`
   - Crawls TikTok videos by hashtags
   - Wait for completion (Success status)

3. **Trigger DAG 2**: `2_TIKTOK_STREAMING_PIPELINE`
   - Downloads videos to MinIO
   - Runs AI inference with Spark
   - Stores results in PostgreSQL
   - Auto-loops for continuous processing

4. **Monitor Dashboard** at http://localhost:8501

### Manual Docker Commands

```bash
cd streaming

# Start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f spark-processor

# Stop all services
docker compose down
```

---

## 🧪 Testing

### Shell Scripts (Ubuntu)

```bash
cd streaming

# Run all tests
./tests/run_all_tests.sh

# Test individual layers
./tests/test_layer1_infrastructure.sh
./tests/test_layer2_ingestion.sh
./tests/test_layer3_processing.sh
./tests/test_layer4_dashboard.sh
```

### Python Tests

```bash
cd streaming
pytest tests/ -v
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
