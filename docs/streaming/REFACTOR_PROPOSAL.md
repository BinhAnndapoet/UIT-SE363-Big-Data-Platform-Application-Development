# 🏗️ Đề xuất Tổ chức lại Folder Streaming Pipeline

## 📊 Cấu trúc Hiện tại vs Đề xuất

### ❌ Cấu trúc Hiện tại (Không rõ ràng theo layer)

```
streaming/
├── docker-compose.yml
├── .env
├── start_all.sh
├── link_host.sh
├── DOCUMENTATION.md
│
├── airflow/                    # Layer 3
│   ├── Dockerfile.airflow
│   ├── docker-compose-airflow.yml  # ⚠️ Legacy/unused
│   └── dags/
│
├── dashboard/                  # Layer 7
│   ├── Dockerfile.dashboard
│   ├── app.py
│   └── requirements.txt
│
├── tiktok-pipeline/           # ⚠️ Mixed: Layer 2, 4, 5
│   ├── Dockerfile.spark       # Layer 2
│   ├── ingestion/             # Layer 4
│   │   ├── modules/
│   │   └── ...
│   ├── processing/            # Layer 5
│   ├── data_viet/             # ⚠️ Data nên ở riêng
│   ├── run_spark.sh           # ⚠️ Debug script
│   ├── start_pipeline.sh      # ⚠️ Deprecated
│   ├── postgres_init/         # ⚠️ Nên ở infra
│   └── spark-data/            # ⚠️ Nên ở state/
│
├── scripts/                   # ⚠️ Utility scripts
├── tests/                     # ✅ OK
├── state/                     # ✅ OK (volumes)
├── chrome_profile/            # ⚠️ Nên merge vào state/
└── zookeeper/                 # ⚠️ Nên ở infra
```

---

### ✅ Cấu trúc Đề xuất (Tổ chức theo Layer)

```
streaming/
│
├── 📋 CONFIG (Root level - Entry points)
│   ├── docker-compose.yml      # Master orchestration
│   ├── .env                    # Environment variables
│   ├── .dockerignore
│   ├── start_all.sh            # Main entry point
│   ├── README.md               # Quick start guide
│   └── DOCUMENTATION.md        # Full documentation
│
├── 📦 infra/                   # LAYER 1: Infrastructure configs
│   ├── postgres/
│   │   └── init.sql            # Schema initialization
│   ├── zookeeper/
│   │   └── zoo.cfg
│   └── kafka/
│       └── (nếu cần custom config)
│
├── ⚡ spark/                   # LAYER 2: Spark Cluster
│   ├── Dockerfile              # Dockerfile.spark renamed
│   ├── requirements.txt        # Python deps for Spark
│   └── configs/
│       └── spark-defaults.conf # (nếu cần)
│
├── 🌬️ airflow/                # LAYER 3: Orchestration
│   ├── Dockerfile
│   ├── requirements.txt
│   └── dags/
│       ├── 1_crawler.py
│       └── 2_streaming.py
│
├── 📥 ingestion/              # LAYER 4: Data Ingestion
│   ├── __init__.py
│   ├── config.py
│   ├── main_worker.py         # ingestion_main_worker.py
│   ├── downloader.py          # tiktok_downloader.py
│   ├── crawler.py             # crawler_links.py
│   ├── audio_processor.py     # preprocess_audio.py
│   └── clients/
│       ├── __init__.py
│       ├── minio_client.py
│       └── kafka_client.py
│
├── 🤖 processing/             # LAYER 5: AI Processing
│   ├── __init__.py
│   ├── spark_processor.py
│   └── models/
│       ├── text_classifier.py
│       ├── video_classifier.py
│       └── audio_classifier.py
│
├── 📊 dashboard/              # LAYER 7: Visualization
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
├── 🧪 tests/                  # Testing
│   ├── test_all_layers.sh
│   ├── CHECKLIST.md
│   └── unit/
│       ├── test_ingestion.py
│       └── test_processing.py
│
├── 🛠️ scripts/               # Utility scripts
│   ├── check_infra.sh
│   ├── trigger_crawler.sh
│   ├── ingest_single.sh
│   └── verify_streaming.sh
│
├── 📁 data/                   # Data sources (mounted)
│   └── crawl/
│       └── tiktok_links.csv
│
└── 💾 state/                  # Persistent volumes
    ├── postgres_data/
    ├── minio_data/
    ├── airflow_logs/
    ├── spark_checkpoints/
    ├── ivy2/
    └── chrome_profile/
```

---

## 📋 Chi tiết Thay đổi

### 1. **Root Level - Giữ nguyên**
- `docker-compose.yml` - Main orchestration
- `.env` - Environment config
- `start_all.sh` - Entry point
- `DOCUMENTATION.md` → Có thể đổi thành `README.md`

### 2. **Tạo `infra/` folder** (Layer 1)
```bash
mkdir -p infra/postgres infra/zookeeper
mv tiktok-pipeline/postgres_init/init.sql infra/postgres/
mv zookeeper/zoo.cfg infra/zookeeper/
rm -rf zookeeper/  # Remove old
```

### 3. **Tạo `spark/` folder** (Layer 2)
```bash
mkdir -p spark
mv tiktok-pipeline/Dockerfile.spark spark/Dockerfile
```

### 4. **Giữ `airflow/` folder** (Layer 3)
```bash
# Rename DAGs for clarity
mv airflow/dags/1_TIKTOK_ETL_COLLECTOR.py airflow/dags/1_crawler.py
mv airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py airflow/dags/2_streaming.py
rm airflow/docker-compose-airflow.yml  # Legacy, không dùng
```

### 5. **Tách `ingestion/` ra khỏi tiktok-pipeline** (Layer 4)
```bash
mv tiktok-pipeline/ingestion/ ./ingestion/
# Rename files
mv ingestion/ingestion_main_worker.py ingestion/main_worker.py
mv ingestion/tiktok_downloader.py ingestion/downloader.py
mv ingestion/crawler_links.py ingestion/crawler.py
mv ingestion/preprocess_audio.py ingestion/audio_processor.py
# Move modules to clients/
mv ingestion/modules/ ingestion/clients/
```

### 6. **Tách `processing/` ra khỏi tiktok-pipeline** (Layer 5)
```bash
mv tiktok-pipeline/processing/ ./processing/
```

### 7. **Di chuyển data**
```bash
mkdir -p data/crawl
mv tiktok-pipeline/data_viet/crawl/*.csv data/crawl/
```

### 8. **Merge chrome_profile vào state/**
```bash
mv chrome_profile/ state/chrome_profile/
```

### 9. **Xóa files deprecated**
```bash
rm tiktok-pipeline/run_spark.sh       # Debug only
rm tiktok-pipeline/start_pipeline.sh  # Deprecated
rm -rf tiktok-pipeline/               # Empty after moves
```

---

## 🎯 Lợi ích của Cấu trúc Mới

| Aspect | Trước | Sau |
|--------|-------|-----|
| **Layer clarity** | Mixed trong tiktok-pipeline | Mỗi folder = 1 layer |
| **Navigation** | Khó tìm file | Dễ navigate |
| **Docker builds** | 1 context lớn | Context nhỏ, build nhanh |
| **Testing** | Test toàn bộ | Test từng layer |
| **Scaling** | Khó scale | Dễ tách service |
| **Onboarding** | Mất thời gian | Hiểu ngay cấu trúc |

---

## ⚠️ Breaking Changes

Nếu refactor, cần update:
1. `docker-compose.yml` - Đổi build context paths
2. DAG files - Đổi import paths
3. `start_all.sh` - Đổi paths nếu cần
4. Mount volumes - Đổi source paths

---

## 🤔 Khuyến nghị

### Option A: **Refactor nhẹ** (Safe, ít risk)
- Chỉ xóa files deprecated
- Merge `chrome_profile/` vào `state/`
- Giữ nguyên `tiktok-pipeline/`

### Option B: **Refactor đầy đủ** (Clean, nhưng cần test lại)
- Apply full structure above
- Update tất cả paths
- Re-test toàn bộ

**Recommend:** Nếu pipeline đang chạy ổn định → Option A
Nếu có thời gian và muốn maintainable lâu dài → Option B
