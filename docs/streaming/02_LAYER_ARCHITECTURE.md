# 🏗️ Layer Architecture Documentation

## Overview

Hệ thống TikTok Safety được xây dựng theo kiến trúc **Lambda Architecture** với 8 layers chính:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAYER ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: Infrastructure    ──────────────────────────────────────────────  │
│           (Docker, Network, Volumes)                                         │
│                                                                              │
│  Layer 2: Message Queue     ──────────────────────────────────────────────  │
│           (Kafka, Zookeeper)                                                 │
│                                                                              │
│  Layer 3: Object Storage    ──────────────────────────────────────────────  │
│           (MinIO - S3 compatible)                                            │
│                                                                              │
│  Layer 4: Data Ingestion    ──────────────────────────────────────────────  │
│           (Crawler, Downloader, Producer)                                    │
│                                                                              │
│  Layer 5: Stream Processing ──────────────────────────────────────────────  │
│           (Spark Streaming, AI Models)                                       │
│                                                                              │
│  Layer 6: Orchestration     ──────────────────────────────────────────────  │
│           (Airflow DAGs)                                                     │
│                                                                              │
│  Layer 7: Data Storage      ──────────────────────────────────────────────  │
│           (PostgreSQL)                                                       │
│                                                                              │
│  Layer 8: Presentation      ──────────────────────────────────────────────  │
│           (Streamlit Dashboard)                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Infrastructure

### Components
| Component | Image | Purpose |
|-----------|-------|---------|
| Docker Network | tiktok-network | Service communication |
| Volumes | ./state/* | Persistent storage |

### Network Configuration
```yaml
networks:
  tiktok-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Mounts
```
./state/postgres_data     → PostgreSQL data
./state/minio_data        → MinIO object storage
./state/spark_checkpoints → Spark streaming state
./state/airflow_logs      → Airflow logs
```

### Tests
- Network exists: `docker network ls | grep tiktok-network`
- Volume sizes: `du -sh state/`

---

## Layer 2: Message Queue

### Components
| Container | Image | Ports | Purpose |
|-----------|-------|-------|---------|
| zookeeper | confluentinc/cp-zookeeper:7.5.0 | 2181 | Kafka coordination |
| kafka | confluentinc/cp-kafka:7.5.0 | 9092, 29092 | Message streaming |

### Kafka Configuration
```yaml
kafka:
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

### Topics
| Topic | Purpose |
|-------|---------|
| tiktok_raw_data | Video metadata for processing |

### Commands
```bash
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic tiktok_raw_data --partitions 1 --replication-factor 1

# Consume messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic tiktok_raw_data --from-beginning --max-messages 1
```

### Tests
- Zookeeper: `echo ruok | nc localhost 2181`
- Kafka health: `docker inspect kafka --format '{{.State.Health.Status}}'`

---

## Layer 3: Object Storage

### Components
| Container | Image | Ports | Purpose |
|-----------|-------|-------|---------|
| minio | minio/minio:latest | 9000, 9001 | S3-compatible storage |
| minio-init | minio/mc | - | Bucket initialization |

### MinIO Configuration
```yaml
minio:
  environment:
    MINIO_ROOT_USER: admin
    MINIO_ROOT_PASSWORD: password123
  command: server /data --console-address ":9001"
```

### Buckets
| Bucket | Purpose |
|--------|---------|
| tiktok-raw-videos | Video files (.mp4) |
| tiktok-raw-audios | Audio files (.wav) |

### Directory Structure
```
tiktok-raw-videos/
├── raw/
│   ├── harmful/
│   │   └── {video_id}.mp4
│   └── safe/
│       └── {video_id}.mp4
```

### Commands
```bash
# Access MinIO with mc client
docker run --rm --network tiktok-network minio/mc sh -c '
  mc alias set local http://minio:9000 admin password123 && 
  mc ls -r local/tiktok-raw-videos/'
```

### Tests
- Health: `curl http://localhost:9000/minio/health/live`
- Console: http://localhost:9001 (admin/password123)

---

## Layer 4: Data Ingestion

### Components
| File | Purpose |
|------|---------|
| ingestion/crawler.py | TikTok video crawler (Selenium) |
| ingestion/downloader.py | Video/Audio downloader |
| ingestion/main_worker.py | Main ingestion worker |
| ingestion/audio_processor.py | Audio extraction (ffmpeg) |

### Data Flow
```
1. crawler.py     → Scrape TikTok links by hashtag
2. downloader.py  → Download video files
3. main_worker.py → Upload to MinIO + Send to Kafka
```

### Configuration
```python
# ingestion/config.py
KAFKA_CONFIG = {
    "bootstrap_servers": "kafka:9092",
    "topic": "tiktok_raw_data"
}

MINIO_CONFIG = {
    "endpoint": "minio:9000",
    "access_key": "admin",
    "secret_key": "password123"
}
```

### Data Source
```
../data_viet/crawl/sub_tiktok_links_viet.csv
# Contains: video_url, hashtag, label, ...
```

### Tests
- Files exist: `ls ingestion/*.py`
- CSV exists: `wc -l ../data_viet/crawl/sub_tiktok_links_viet.csv`

---

## Layer 5: Stream Processing

### Components
| Container | Image | Purpose |
|-----------|-------|---------|
| spark-master | apache/spark:3.5.0 (custom) | Spark master node |
| spark-worker | apache/spark:3.5.0 (custom) | Spark worker node |
| spark-processor | apache/spark:3.5.0 (custom) | AI inference |

### Spark Configuration
```yaml
spark-processor:
  environment:
    - TEXT_WEIGHT=0.6
    - VIDEO_WEIGHT=0.4
    - DECISION_THRESHOLD=0.5
    - SPARK_CHECKPOINT_DIR=/opt/spark/checkpoints/tiktok_multimodal
```

### AI Models Mount
```yaml
volumes:
  - ../../train_eval_module/output/text_models/CafeBERT_finetuned_best:/models/text/CafeBERT_finetuned_best
  - ../../train_eval_module/output/video_models:/models/video
```

### Processing Logic
```python
# spark/spark_processor.py
def process_batch(batch_df):
    for row in batch_df:
        # 1. Load video from MinIO
        video = load_video(row.video_url)
        
        # 2. Extract text (transcript)
        text = row.transcript
        
        # 3. Run AI models
        text_score = text_model.predict(text)
        video_score = video_model.predict(video)
        
        # 4. Late fusion
        avg_score = text_score * 0.6 + video_score * 0.4
        verdict = "harmful" if avg_score >= 0.5 else "safe"
        
        # 5. Save to PostgreSQL
        save_to_db(row.video_id, text_score, video_score, avg_score, verdict)
```

### Tests
- Spark UI: http://localhost:9090
- PyTorch: `docker exec spark-processor python -c "import torch; print(torch.__version__)"`

---

## Layer 6: Orchestration

### Components
| Container | Image | Ports | Purpose |
|-----------|-------|-------|---------|
| airflow-db | postgres:15 | 5432 | Airflow metadata |
| airflow-scheduler | apache/airflow:2.8.1 | - | DAG scheduling |
| airflow-webserver | apache/airflow:2.8.1 | 8080 | Web UI |

### DAGs
| DAG ID | Schedule | Purpose |
|--------|----------|---------|
| 1_TIKTOK_ETL_COLLECTOR | Manual | Crawl & download videos |
| 2_TIKTOK_STREAMING_PIPELINE | Manual | AI processing |

### DAG 1: ETL Collector
```python
# airflow/dags/1_TIKTOK_ETL_COLLECTOR.py
with DAG("1_TIKTOK_ETL_COLLECTOR"):
    task_crawl = PythonOperator(
        task_id="crawl_tiktok",
        python_callable=crawl_tiktok_videos
    )
    
    task_download = PythonOperator(
        task_id="download_videos",
        python_callable=download_and_upload
    )
    
    task_crawl >> task_download
```

### DAG 2: Streaming Pipeline
```python
# airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py
with DAG("2_TIKTOK_STREAMING_PIPELINE"):
    task_start_streaming = BashOperator(
        task_id="start_spark_streaming",
        bash_command="docker exec spark-processor ..."
    )
```

### Commands
```bash
# List DAGs
docker exec airflow-webserver airflow dags list

# Trigger DAG
docker exec airflow-webserver airflow dags trigger 1_TIKTOK_ETL_COLLECTOR

# Unpause DAG
docker exec airflow-webserver airflow dags unpause 1_TIKTOK_ETL_COLLECTOR
```

### Tests
- Health: `curl http://localhost:8080/health`
- UI: http://localhost:8080 (admin/admin)

---

## Layer 7: Data Storage

### Components
| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| postgres | postgres:15 | 5432 | Results storage |

### Database Schema
```sql
-- Database: tiktok_safety_db

CREATE TABLE processed_results (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(100) UNIQUE,
    raw_text TEXT,
    human_label VARCHAR(50),
    text_verdict VARCHAR(50),
    video_verdict VARCHAR(50),
    text_score FLOAT,
    video_score FLOAT,
    audio_score FLOAT,
    avg_score FLOAT,
    final_decision VARCHAR(50),
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_video_id ON processed_results(video_id);
CREATE INDEX idx_processed_at ON processed_results(processed_at);
CREATE INDEX idx_final_decision ON processed_results(final_decision);
```

### Commands
```bash
# Connect to database
docker exec -it postgres psql -U user -d tiktok_safety_db

# Query results
SELECT video_id, final_decision, avg_score, processed_at 
FROM processed_results 
ORDER BY processed_at DESC LIMIT 5;

# Count by category
SELECT final_decision, COUNT(*) 
FROM processed_results 
GROUP BY final_decision;
```

### Tests
- Health: `docker exec postgres pg_isready -U user -d tiktok_safety_db`
- Count: `SELECT COUNT(*) FROM processed_results;`

---

## Layer 8: Presentation

### Components
| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| dashboard | python:3.9-slim (custom) | 8501 | Streamlit UI |

### Module Structure
```
dashboard/
├── app.py              # Main entry point
├── config.py           # Configuration (DB, MinIO, URLs)
├── helpers.py          # Utility functions
├── styles.py           # CSS styles
└── page_modules/       # Page components
    ├── dashboard_monitor.py   # Analytics page
    ├── system_operations.py   # Pipeline control
    ├── content_audit.py       # Video review
    ├── project_info.py        # Documentation
    └── database_manager.py    # DB tools
```

### Configuration
```python
# dashboard/config.py
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "dbname": "tiktok_safety_db",
    "user": "user",
    "password": "password"
}

MINIO_CONF = {
    "public_endpoint": os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000"),
    "bucket": "tiktok-raw-videos"
}

EXTERNAL_URLS = {
    "airflow": f"http://{PUBLIC_HOST}:8080",
    "minio_console": f"http://{PUBLIC_HOST}:9001",
    "spark_ui": f"http://{PUBLIC_HOST}:9090"
}
```

### Tests
- UI: http://localhost:8501
- Health: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8501`
