# 📚 TikTok Harmful Content Detection - Project Overview

## 🎯 Mục đích dự án

Hệ thống **TikTok Safety** là một Big Data Pipeline phát hiện nội dung độc hại trong video TikTok sử dụng **AI đa phương thức (Multi-modal)**. Hệ thống thu thập video từ TikTok, phân tích bằng các mô hình AI (Text, Video, Audio) và hiển thị kết quả qua Dashboard real-time.

## 🏗️ Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TikTok Safety Pipeline                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │ TikTok   │───▶│ Crawler  │───▶│  MinIO   │───▶│  Kafka   │───▶│ Spark  │ │
│  │   API    │    │(Selenium)│    │(S3 Store)│    │ (Queue)  │    │Streaming│ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘ │
│                                                                      │       │
│                                                                      ▼       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 ┌──────────┐  │
│  │Dashboard │◀───│PostgreSQL│◀───│AI Models │◀────────────────│  Spark   │  │
│  │(Streamlit│    │ (Results)│    │Text/Video│                 │ Processor│  │
│  └──────────┘    └──────────┘    └──────────┘                 └──────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Airflow (Orchestration)                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Container | Docker + Docker Compose | Containerization |
| Network | tiktok-network (172.20.0.0/16) | Service communication |
| Orchestration | Apache Airflow 2.8.1 | DAG scheduling |

### Data Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Message Queue | Apache Kafka 3.5 | Event streaming |
| Coordinator | Apache Zookeeper | Kafka coordination |
| Object Storage | MinIO (S3-compatible) | Video/Audio storage |
| Database | PostgreSQL 15 | Structured results |

### Processing Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Stream Processing | Apache Spark 3.5.0 | Real-time processing |
| Text AI | PhoBERT/CafeBERT | Vietnamese text classification |
| Video AI | TimeSformer | Video content analysis |
| Audio AI | Wav2Vec2 | Audio analysis (placeholder) |

### Presentation Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Dashboard | Streamlit 1.31+ | Real-time visualization |
| Charts | Plotly | Interactive charts |

## 📊 Mô hình AI

### Late Fusion Strategy
```python
# Weighted average fusion
weights = {
    "text": 0.6,   # 60% weight - TextModel hiệu quả nhất với tiếng Việt
    "video": 0.4,  # 40% weight - VideoModel bổ sung visual analysis
    "audio": 0.0   # 0% - Chưa implement (placeholder)
}

avg_score = (
    text_score * weights["text"] +
    video_score * weights["video"] +
    audio_score * weights["audio"]
)

# Decision threshold
verdict = "Harmful" if avg_score >= 0.5 else "Safe"
```

### Model Details
| Model | Architecture | Input | Output |
|-------|-------------|-------|--------|
| TextModel | CafeBERT (fine-tuned) | Vietnamese transcript | Harmful probability (0-1) |
| VideoModel | TimeSformer | 16 video frames | Harmful probability (0-1) |
| AudioModel | Wav2Vec2 | Audio waveform | Harmful probability (0-1) |

## 📁 Cấu trúc thư mục

```
streaming/
├── 📂 airflow/              # Workflow orchestration
│   ├── dags/                # DAG definitions
│   │   ├── 1_TIKTOK_ETL_COLLECTOR.py
│   │   └── 2_TIKTOK_STREAMING_PIPELINE.py
│   └── Dockerfile.airflow
│
├── 📂 dashboard/            # Streamlit Dashboard
│   ├── app.py               # Main entry point
│   ├── config.py            # Configuration
│   ├── helpers.py           # Utility functions
│   ├── styles.py            # CSS styles
│   └── page_modules/        # Page components
│
├── 📂 ingestion/            # Data collection
│   ├── crawler.py           # TikTok crawler
│   ├── downloader.py        # Video downloader
│   └── main_worker.py       # Main worker
│
├── 📂 spark/                # Spark processing
│   └── spark_processor.py   # AI inference
│
├── 📂 tests/                # Test scripts
│   ├── test_comprehensive.sh
│   └── test_all_layers.sh
│
├── 📂 state/                # Persistent data
│   ├── minio_data/          # MinIO storage
│   ├── postgres_data/       # PostgreSQL data
│   └── spark_checkpoints/   # Spark state
│
├── 📂 Documents/            # Documentation
│
├── docker-compose.yml       # Service definitions
├── .env                     # Environment variables
└── start_all.sh             # Startup script
```

## 🌐 Service URLs

| Service | Internal URL | External URL (Tailscale) |
|---------|-------------|--------------------------|
| Dashboard | http://localhost:8501 | http://100.69.255.87:8501 |
| Airflow UI | http://localhost:8080 | http://100.69.255.87:8080 |
| MinIO Console | http://localhost:9001 | http://100.69.255.87:9001 |
| Spark UI | http://localhost:9090 | http://100.69.255.87:9090 |
| Kafka | localhost:9092 | 100.69.255.87:9092 |
| PostgreSQL | localhost:5432 | 100.69.255.87:5432 |

## 🔐 Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Airflow | admin | admin |
| MinIO | admin | password123 |
| PostgreSQL | user | password |

## 📈 KPIs & Metrics

Dashboard hiển thị các chỉ số:
- **Total Processed**: Tổng số video đã xử lý
- **Harmful Detected**: Số video phát hiện độc hại
- **Safe Content**: Số video an toàn
- **Avg Risk Score**: Điểm rủi ro trung bình (0-10)
- **Category Distribution**: Biểu đồ phân bố Harmful/Safe
- **Timeline**: Số lượng video xử lý theo thời gian

## 👥 Team

**UIT - SE363 Big Data Platform Application Development**

Course: SE363 - Big Data Platform Application Development
University: University of Information Technology (UIT-VNU)
