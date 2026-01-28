# 🔬 MLFLOW INTEGRATION GUIDE
## Model Registry & Auto-Update cho TikTok Safety Platform

> **Ngày tạo:** 2025-01-27  
> **Mục đích:** Hướng dẫn tích hợp MLflow để quản lý models và auto-update trong streaming

---

## 📋 MỤC LỤC

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cài đặt và cấu hình](#2-cài-đặt-và-cấu-hình)
3. [Tích hợp vào Training Scripts](#3-tích-hợp-vào-training-scripts)
4. [Auto-Update trong Streaming](#4-auto-update-trong-streaming)
5. [Workflow chi tiết](#5-workflow-chi-tiết)
6. [Testing và Troubleshooting](#6-testing-và-troubleshooting)

---

## 1. TỔNG QUAN KIẾN TRÚC

### 1.1. MLflow Components

```
┌─────────────────────────────────────────────────────────────┐
│                    MLFLOW SERVER (Port 5000)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Tracking Server │         │  Artifact Store  │         │
│  │  (SQLite/File)   │         │  (File System)   │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         MODEL REGISTRY                               │   │
│  │  - text_classification_model                         │   │
│  │  - video_classification_model                        │   │
│  │  - fusion_multimodal_model                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────┴────────┐                      ┌──────────┴──────────┐
│  Training      │                      │  Streaming          │
│  (Log models)  │                      │  (Auto-update)      │
│                │                      │                     │
│  - text/       │                      │  - spark_processor  │
│  - video/      │                      │  - model_updater    │
│  - fusion/     │                      │  - check mỗi 30p    │
└────────────────┘                      └─────────────────────┘
```

### 1.2. Data Flow

```
Training Script (train.py)
    │
    ├─► Train Model
    ├─► Evaluate → Metrics (F1, Accuracy, ...)
    ├─► Save best_checkpoint
    └─► mlflow_logger.log_model()
         │
         ├─► Log metrics → MLflow Tracking
         ├─► Log params → MLflow Tracking
         ├─► Upload model → MLflow Artifacts
         └─► Register → MLflow Model Registry
              │
              └─► Stage: "None" → "Production" (nếu F1 tốt)

Streaming (spark_processor.py)
    │
    ├─► ModelAutoUpdater.start() (mỗi 30 phút)
    ├─► Check latest model trong MLflow Registry
    ├─► Compare F1 score với model hiện tại
    └─► If new F1 > current F1:
         ├─► Download new model
         ├─► Update model path
         └─► Reload model (lazy reload)
```

---

## 2. CÀI ĐẶT VÀ CẤU HÌNH

### 2.1. Docker Compose Setup

**File:** `streaming/docker-compose.yml`

MLflow service đã được thêm vào:

```yaml
mlflow:
  image: ghcr.io/mlflow/mlflow:v2.8.1
  container_name: mlflow
  ports: ["5000:5000"]
  command: >
    mlflow server
    --host 0.0.0.0
    --port 5000
    --backend-store-uri file:/mlflow/backend
    --default-artifact-root file:/mlflow/artifacts
    --serve-artifacts
  volumes:
    - ./state/mlflow_backend:/mlflow/backend
    - ./state/mlflow_artifacts:/mlflow/artifacts
    - ../train_eval_module:/mlflow/models
  environment:
    - MLFLOW_BACKEND_STORE_URI=file:/mlflow/backend
    - MLFLOW_DEFAULT_ARTIFACT_ROOT=file:/mlflow/artifacts
  healthcheck:
    test: ["CMD-SHELL", "curl -fsS http://localhost:5000/health >/dev/null || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - tiktok-network
```

### 2.2. Environment Variables

**File:** `.env` (hoặc export trong terminal)

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=http://mlflow:5000  # Internal (Docker network)
MLFLOW_TRACKING_URI=http://localhost:5000  # External (local development)

# Model Registry F1 Thresholds
MLFLOW_TEXT_F1_THRESHOLD=0.75
MLFLOW_VIDEO_F1_THRESHOLD=0.70
MLFLOW_FUSION_F1_THRESHOLD=0.80

# Auto-update interval (minutes)
MLFLOW_UPDATE_INTERVAL_MINUTES=30
```

### 2.3. Directories Structure

```
streaming/
├── mlflow/
│   ├── __init__.py
│   ├── client.py          # MLflow client utilities
│   └── model_updater.py   # Auto-update mechanism
│
train_eval_module/
└── shared_utils/
    └── mlflow_logger.py   # Logger cho training scripts

streaming/state/
├── mlflow_backend/        # MLflow backend store (SQLite)
└── mlflow_artifacts/      # MLflow artifacts (models, files)
```

---

## 3. TÍCH HỢP VÀO TRAINING SCRIPTS

### 3.1. Text Model Training

**File:** `train_eval_module/text/train.py`

Thêm vào cuối function `train_text()`:

```python
from shared_utils.mlflow_logger import log_text_model

def train_text(model_idx, metric_type="eval_f1"):
    # ... existing training code ...
    
    trainer.train()
    
    # Save best checkpoint (existing code)
    save_path = os.path.join(full_output_dir, "best_checkpoint")
    # ... save model code ...
    
    # [NEW] Log to MLflow
    try:
        # Get metrics từ trainer state hoặc test
        metrics = {
            "eval_f1": trainer.state.best_metric if hasattr(trainer.state, 'best_metric') else 0.0,
            # Add other metrics as needed
        }
        
        # Get params
        params = {
            "model_name": raw_model_name,
            "batch_size": PARAMS["batch_size"],
            "lr": PARAMS["lr"],
            "epochs": PARAMS["epochs"],
            # Add other params as needed
        }
        
        # Log to MLflow
        log_text_model(
            model_path=save_path,
            metrics=metrics,
            params=params,
            model_name=get_clean_model_name(raw_model_name),
        )
    except Exception as e:
        logger.warning(f"⚠️ MLflow logging failed: {e}")
        # Training vẫn tiếp tục nếu MLflow fail
```

### 3.2. Video Model Training

**File:** `train_eval_module/video/train.py`

Thêm vào cuối function `train_video()`:

```python
from shared_utils.mlflow_logger import log_video_model

def train_video(model_idx):
    # ... existing training code ...
    
    trainer.train()
    
    final_save_path = os.path.join(full_output_dir, "best_checkpoint")
    trainer.save_model(final_save_path)
    
    # [NEW] Log to MLflow
    try:
        # Run test để get metrics (hoặc lấy từ trainer.state)
        # metrics = {...}
        
        log_video_model(
            model_path=final_save_path,
            metrics=metrics,
            params=params,
            model_name=cfg["name"],
        )
    except Exception as e:
        logger.warning(f"⚠️ MLflow logging failed: {e}")
```

### 3.3. Fusion Model Training

**File:** `train_eval_module/fusion/train.py`

Thêm vào cuối function `train_fusion()`:

```python
from shared_utils.mlflow_logger import log_fusion_model

def train_fusion():
    # ... existing training code ...
    
    trainer.train()
    trainer.save_model(os.path.join(output_dir, "best_checkpoint"))
    
    # [NEW] Log to MLflow
    try:
        # Run test để get metrics
        # metrics = {...}
        
        log_fusion_model(
            model_path=os.path.join(output_dir, "best_checkpoint"),
            metrics=metrics,
            params=FUSION_PARAMS,
        )
    except Exception as e:
        logger.warning(f"⚠️ MLflow logging failed: {e}")
```

### 3.4. Cách lấy Metrics

**Option 1: Từ trainer.state (nếu có)**
```python
metrics = {
    "eval_f1": trainer.state.best_metric if hasattr(trainer.state, 'best_metric') else 0.0,
    "eval_accuracy": trainer.state.best_metric_accuracy if hasattr(trainer.state, 'best_metric_accuracy') else 0.0,
}
```

**Option 2: Run test sau training (recommended)**
```python
# Sau trainer.train()
test_results = trainer.evaluate(test_dataset)
metrics = {
    "eval_f1": test_results.get("eval_f1", 0.0),
    "eval_accuracy": test_results.get("eval_accuracy", 0.0),
    "eval_loss": test_results.get("eval_loss", 0.0),
}
```

---

## 4. AUTO-UPDATE TRONG STREAMING

### 4.1. Tích hợp vào spark_processor.py

**File:** `streaming/processing/spark_processor.py`

Thêm vào đầu file:

```python
import os
import sys
sys.path.insert(0, '/app/processing')

# MLflow auto-updater
try:
    from mlflow.model_updater import ModelAutoUpdater
    MLFLOW_ENABLED = os.getenv("MLFLOW_ENABLED", "true").lower() == "true"
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    MLFLOW_UPDATE_INTERVAL = int(os.getenv("MLFLOW_UPDATE_INTERVAL_MINUTES", "30"))
except ImportError:
    MLFLOW_ENABLED = False
    print("⚠️ MLflow not available, skipping auto-update")
```

Thêm vào `main()` function:

```python
def main():
    # ... existing code ...
    
    # [NEW] Initialize MLflow auto-updater
    model_updater = None
    if MLFLOW_ENABLED:
        try:
            from mlflow.model_updater import ModelAutoUpdater
            
            # Current metrics (giả định - sẽ update sau khi test model)
            current_metrics = {
                "text": 0.80,   # Update từ actual test results
                "video": 0.75,  # Update từ actual test results
                "fusion": 0.85, # Update từ actual test results
            }
            
            # Current model paths
            model_paths = {
                "text": PATH_TEXT_MODEL,
                "video": PATH_VIDEO_MODEL,
                "fusion": PATH_FUSION_MODEL,
            }
            
            model_updater = ModelAutoUpdater(
                tracking_uri=MLFLOW_TRACKING_URI,
                check_interval_minutes=MLFLOW_UPDATE_INTERVAL,
                model_paths=model_paths,
                current_metrics=current_metrics,
            )
            
            model_updater.start()
            log_to_db("✅ MLflow auto-updater started", "INFO")
        except Exception as e:
            log_to_db(f"⚠️ Failed to start MLflow auto-updater: {e}", "WARN")
    
    # ... rest of main() code ...
    
    query = df_final.writeStream.foreachBatch(write_to_postgres).start()
    log_to_db("✅ Spark query started. Waiting for Kafka messages...", "INFO")
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        if model_updater:
            model_updater.stop()
        query.stop()
```

### 4.2. Environment Variables trong docker-compose.yml

Thêm vào `spark-processor` service:

```yaml
spark-processor:
  environment:
    # ... existing env vars ...
    - MLFLOW_ENABLED=${MLFLOW_ENABLED:-true}
    - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow:5000}
    - MLFLOW_UPDATE_INTERVAL_MINUTES=${MLFLOW_UPDATE_INTERVAL_MINUTES:-30}
```

---

## 5. WORKFLOW CHI TIẾT

### 5.1. Training Workflow (Log vào MLflow)

```
1. Chạy training script (text/video/fusion)
   python train_eval_module/text/train.py 0  # train text model

2. Training hoàn thành
   ├─► Model saved to: train_eval_module/text/output/.../best_checkpoint
   ├─► Metrics computed (F1, Accuracy, ...)
   └─► mlflow_logger.log_text_model()
       ├─► Connect to MLflow server (http://mlflow:5000)
       ├─► Create/Get experiment: "tiktok_safety_text"
       ├─► Start new run
       ├─► Log metrics: eval_f1, eval_accuracy, ...
       ├─► Log params: batch_size, lr, epochs, ...
       ├─► Upload model artifact (best_checkpoint folder)
       └─► Register to Model Registry: "text_classification_model"
           └─► Stage: "None" (default)

3. Promote to Production (manual hoặc auto)
   - Nếu F1 > threshold → Promote to "Production" stage
   - Có thể dùng MLflow UI hoặc API
```

### 5.2. Streaming Auto-Update Workflow

```
1. Streaming khởi động
   ├─► Load models từ hardcoded paths:
   │   - PATH_TEXT_MODEL = "/models/text/output/..."
   │   - PATH_VIDEO_MODEL = "/models/video/output/..."
   │   - PATH_FUSION_MODEL = "/models/fusion/output/..."
   └─► ModelAutoUpdater.start()
       └─► Start background thread (check mỗi 30 phút)

2. Mỗi 30 phút (auto-check)
   ├─► ModelAutoUpdater.check_and_update_models()
   ├─► For each model_type (text, video, fusion):
   │   ├─► Get latest version từ MLflow Registry
   │   ├─► Get F1 score từ latest version
   │   ├─► Compare với current F1:
   │   │   ├─► If new F1 > current F1 AND new F1 > threshold:
   │   │   │   ├─► Download model từ MLflow
   │   │   │   ├─► Save to: /models/{model_type}/mlflow/{type}_latest
   │   │   │   ├─► Update model_paths[model_type]
   │   │   │   └─► Update current_metrics[model_type] = new_f1
   │   │   └─► Else: Skip update
   │   └─► Log update status
   └─► Sleep 30 minutes → Repeat

3. Model reload (lazy loading)
   ├─► Models được load lazy (khi first inference)
   ├─► Nếu model_path thay đổi → Next inference sẽ load model mới
   └─► Không cần restart streaming service
```

### 5.3. Model Registry Stages

```
Model Lifecycle:
  None → Staging → Production

Auto-promote rules:
  - F1 > threshold → Auto promote to "Production"
  - Manual promote qua MLflow UI hoặc API
```

---

## 6. TESTING VÀ TROUBLESHOOTING

### 6.1. Test MLflow Connection

```bash
# Test từ host
curl http://localhost:5000/health

# Test từ container
docker exec spark-processor python -c "
from mlflow import set_tracking_uri
set_tracking_uri('http://mlflow:5000')
from mlflow.tracking import MlflowClient
client = MlflowClient()
print('✅ MLflow connected')
print(f'Experiments: {len(client.search_experiments())}')
"
```

### 6.2. Test Model Logging

```python
# Test script: test_mlflow_log.py
from train_eval_module.shared_utils.mlflow_logger import log_text_model

log_text_model(
    model_path="train_eval_module/text/output/xlm-roberta-base/train/best_checkpoint",
    metrics={"eval_f1": 0.85, "eval_accuracy": 0.90},
    params={"model_name": "xlm-roberta-base", "batch_size": 8},
    model_name="xlm-roberta-base",
)
```

### 6.3. Test Auto-Updater

```python
# Test script: test_auto_updater.py
from streaming.mlflow.model_updater import ModelAutoUpdater

updater = ModelAutoUpdater(
    check_interval_minutes=1,  # Test với 1 phút
    current_metrics={
        "text": 0.80,
        "video": 0.75,
        "fusion": 0.85,
    },
)

# Check once
updater.check_and_update_models()

# Start auto-updater (run 1 minute)
updater.start()
import time
time.sleep(65)  # Run 1 cycle
updater.stop()
```

### 6.4. Kiểm tra Model Registry

```bash
# Access MLflow UI
http://localhost:5000

# Hoặc dùng API
curl http://localhost:5000/api/2.0/mlflow/registered-models/search
```

### 6.5. Common Issues

**Issue 1: MLflow connection failed**
```
Error: Connection refused to http://mlflow:5000
```
**Solution:**
- Kiểm tra MLflow container đang chạy: `docker ps | grep mlflow`
- Kiểm tra network: `docker network inspect tiktok-network`
- Kiểm tra MLFLOW_TRACKING_URI env var

**Issue 2: Model not found in registry**
```
Warning: No model found in registry for text
```
**Solution:**
- Đảm bảo đã log model sau training
- Kiểm tra experiment name match
- Kiểm tra model registry name match

**Issue 3: F1 score not found**
```
Warning: No F1 score found for latest model
```
**Solution:**
- Đảm bảo metrics được log với key "eval_f1" hoặc "f1"
- Kiểm tra run metrics trong MLflow UI

**Issue 4: Model download failed**
```
Error: Failed to download model
```
**Solution:**
- Kiểm tra artifact store path
- Kiểm tra permissions
- Kiểm tra disk space

---

## 7. BEST PRACTICES

### 7.1. Training Scripts

✅ **DO:**
- Log metrics sau khi test (đảm bảo metrics chính xác)
- Log params đầy đủ (model_name, batch_size, lr, epochs, ...)
- Log tags để dễ filter/search (model_name, date, ...)
- Handle MLflow errors gracefully (không fail training nếu MLflow down)

❌ **DON'T:**
- Log metrics từ train set (chỉ log từ val/test set)
- Log quá nhiều params không quan trọng
- Block training nếu MLflow fail

### 7.2. Streaming Auto-Update

✅ **DO:**
- Set reasonable F1 thresholds (tránh update với model kém)
- Update current_metrics sau khi test model mới
- Log update events vào system_logs (Dashboard hiển thị)
- Handle download errors gracefully (skip update nếu fail)

❌ **DON'T:**
- Update quá thường xuyên (30 phút là OK)
- Update nếu model chưa được test kỹ
- Force reload model nếu không cần thiết

### 7.3. Model Registry

✅ **DO:**
- Promote models to "Production" chỉ khi F1 > threshold
- Tag models với metadata (date, metrics, ...)
- Version models rõ ràng
- Archive old models khi không dùng

❌ **DON'T:**
- Promote models chưa test kỹ
- Xóa models trong Production stage
- Overwrite models trong Production

---

## 8. MONITORING & VISUALIZATION

### 8.1. MLflow UI

**URL:** `http://localhost:5000`

**Features:**
- Experiments: Xem tất cả training runs
- Models: Xem registered models
- Compare: So sánh metrics giữa các runs
- Metrics: Time series charts
- Artifacts: Download models

### 8.2. Dashboard Integration (Future)

Có thể thêm MLflow metrics vào Streamlit Dashboard:
- Show latest model versions
- Show F1 trends over time
- Show update history
- Manual promote button

---

## 📝 TÓM TẮT

### Đã tích hợp:

1. ✅ **MLflow Server** - Thêm vào docker-compose.yml
2. ✅ **MLflow Client** - Utilities để log và query models
3. ✅ **MLflow Logger** - Wrapper cho training scripts
4. ✅ **Auto-Updater** - Background thread check và update models mỗi 30p

### Cần làm tiếp:

1. ⏳ **Integrate mlflow_logger vào training scripts** (text/video/fusion)
2. ⏳ **Integrate auto-updater vào spark_processor.py**
3. ⏳ **Test end-to-end workflow**
4. ⏳ **Update current_metrics từ actual test results**

### Files đã tạo:

- `streaming/mlflow/client.py` - MLflow client utilities
- `streaming/mlflow/model_updater.py` - Auto-update mechanism
- `train_eval_module/shared_utils/mlflow_logger.py` - Logger cho training
- `MLFLOW_INTEGRATION_GUIDE.md` - This guide

---

**Report này cung cấp hướng dẫn chi tiết để tích hợp MLflow vào hệ thống. Bạn có thể bắt đầu integrate vào training scripts theo hướng dẫn trên.**
