# 🎯 MLFLOW INTEGRATION - FINAL REPORT
## Tích hợp MLflow cho Model Registry & Auto-Update

> **Ngày tạo:** 2025-01-27  
> **Status:** ✅ **SETUP HOÀN TẤT** - Ready to integrate into training scripts

---

## 📋 TÓM TẮT NHANH

### ✅ Đã hoàn thành:

1. **MLflow Server** - Thêm vào docker-compose.yml ✅
2. **MLflow Client Utilities** - `streaming/mlflow/client.py` ✅
3. **Auto-Updater** - `streaming/mlflow/model_updater.py` ✅
4. **MLflow Logger** - `train_eval_module/shared_utils/mlflow_logger.py` ✅
5. **Documentation** - `MLFLOW_INTEGRATION_GUIDE.md` (hướng dẫn chi tiết) ✅
6. **UI/UX Checklist** - `UI_UX_CHECKLIST.md` (liệt kê issues cần fix) ✅

---

## 🏗️ KIẾN TRÚC ĐÃ XÂY DỰNG

### 1. MLflow Server (Port 5000)

**Location:** `streaming/docker-compose.yml`

**Features:**
- Tracking Server (File-based backend)
- Artifact Store (File system)
- Model Registry (3 models: text, video, fusion)
- Web UI: `http://localhost:5000`

**Storage:**
- Backend: `streaming/state/mlflow_backend/`
- Artifacts: `streaming/state/mlflow_artifacts/`

### 2. MLflow Client (`streaming/mlflow/client.py`)

**Class:** `MLflowModelRegistry`

**Functions:**
- `log_model()` - Log model vào MLflow registry
- `get_latest_model_version()` - Lấy version mới nhất
- `compare_and_update_model()` - So sánh F1 và quyết định update
- `download_model()` - Download model từ registry

**Model Registry Names:**
- `text_classification_model`
- `video_classification_model`
- `fusion_multimodal_model`

**F1 Thresholds:**
- Text: 0.75
- Video: 0.70
- Fusion: 0.80

### 3. Auto-Updater (`streaming/mlflow/model_updater.py`)

**Class:** `ModelAutoUpdater`

**Features:**
- Background thread check mỗi 30 phút (configurable)
- Compare F1 score với model hiện tại
- Auto-download và update nếu F1 tốt hơn
- Lazy reload (không cần restart streaming)

**Workflow:**
```
Every 30 minutes:
  ├─► Check MLflow registry
  ├─► Get latest model version
  ├─► Compare F1 scores
  └─► If new F1 > current F1 AND new F1 > threshold:
      ├─► Download new model
      ├─► Update model path
      └─► Log update event
```

### 4. MLflow Logger (`train_eval_module/shared_utils/mlflow_logger.py`)

**Functions:**
- `log_text_model()` - Wrapper cho text models
- `log_video_model()` - Wrapper cho video models
- `log_fusion_model()` - Wrapper cho fusion models
- `log_model_to_mlflow()` - Generic logger

**Usage:**
```python
from shared_utils.mlflow_logger import log_text_model

# Sau training
log_text_model(
    model_path="path/to/best_checkpoint",
    metrics={"eval_f1": 0.85, "eval_accuracy": 0.90},
    params={"model_name": "xlm-roberta-base", "batch_size": 8},
    model_name="xlm-roberta-base",
)
```

---

## 🔄 WORKFLOW CHI TIẾT

### Phase 1: Training → MLflow (Log Models)

```
Training Script (train.py)
    │
    ├─► Train Model
    ├─► Evaluate → Metrics (F1, Accuracy, ...)
    ├─► Save best_checkpoint
    └─► mlflow_logger.log_model()
         │
         ├─► Connect MLflow (http://mlflow:5000)
         ├─► Create/Get experiment: "tiktok_safety_{model_type}"
         ├─► Start new run
         ├─► Log metrics: eval_f1, eval_accuracy, ...
         ├─► Log params: batch_size, lr, epochs, ...
         ├─► Upload model artifact (best_checkpoint folder)
         └─► Register to Model Registry: "{model_type}_classification_model"
              └─► Stage: "None" (default)

Promote to Production (manual hoặc auto):
  - F1 > threshold → Promote to "Production"
  - Hoặc promote manual qua MLflow UI
```

### Phase 2: Streaming → MLflow (Auto-Update)

```
Streaming Service (spark_processor.py)
    │
    ├─► Start ModelAutoUpdater (background thread)
    └─► Every 30 minutes:
         ├─► Check MLflow registry
         ├─► For each model_type (text, video, fusion):
         │   ├─► Get latest version from Production stage
         │   ├─► Get F1 score from run metrics
         │   ├─► Compare with current F1:
         │   │   ├─► If new F1 > current F1 AND new F1 > threshold:
         │   │   │   ├─► Download model từ MLflow
         │   │   │   ├─► Save to: /models/{type}/mlflow/{type}_latest
         │   │   │   ├─► Update model_paths[model_type]
         │   │   │   └─► Log update event
         │   │   └─► Else: Skip update
         │   └─► Sleep 30 minutes → Repeat

Model Reload (lazy loading):
  ├─► Models load lazy khi first inference
  ├─► If model_path changed → Next inference load model mới
  └─► Không cần restart streaming service
```

---

## 📁 CẤU TRÚC FILES

```
streaming/
├── docker-compose.yml              # [UPDATED] Added MLflow service
│
├── mlflow/                         # [NEW] MLflow utilities
│   ├── __init__.py
│   ├── client.py                   # MLflowModelRegistry class
│   └── model_updater.py            # ModelAutoUpdater class
│
└── state/
    ├── mlflow_backend/             # [NEW] MLflow backend (SQLite)
    └── mlflow_artifacts/           # [NEW] MLflow artifacts (models)

train_eval_module/
└── shared_utils/
    └── mlflow_logger.py            # [NEW] Logger cho training scripts

Root/
├── MLFLOW_INTEGRATION_GUIDE.md     # [NEW] Hướng dẫn chi tiết
├── MLFLOW_SETUP_COMPLETE.md        # [NEW] Quick start guide
├── MLFLOW_FINAL_REPORT.md          # [NEW] This report
└── UI_UX_CHECKLIST.md              # [NEW] UI/UX issues list
```

---

## 🚀 CÁCH SỬ DỤNG

### 1. Start MLflow Server

```bash
cd /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming
conda activate SE363
./start_all.sh
```

MLflow sẽ tự động start và accessible tại: `http://localhost:5000`

### 2. Log Model sau Training

**Trong training script** (text/video/fusion), thêm vào cuối function:

```python
from shared_utils.mlflow_logger import log_text_model

# Sau trainer.train()
log_text_model(
    model_path=save_path,
    metrics={"eval_f1": 0.85, "eval_accuracy": 0.90},
    params={"model_name": "xlm-roberta-base", "batch_size": 8},
    model_name="xlm-roberta-base",
)
```

**Xem chi tiết:** `MLFLOW_INTEGRATION_GUIDE.md` section 3

### 3. Enable Auto-Update trong Streaming

**Trong spark_processor.py**, thêm vào `main()`:

```python
from mlflow.model_updater import ModelAutoUpdater

model_updater = ModelAutoUpdater(
    tracking_uri=MLFLOW_TRACKING_URI,
    check_interval_minutes=30,
    model_paths={...},
    current_metrics={...},
)
model_updater.start()
```

**Xem chi tiết:** `MLFLOW_INTEGRATION_GUIDE.md` section 4

### 4. Access MLflow UI

**URL:** `http://localhost:5000`

**Features:**
- Experiments: Xem tất cả training runs
- Models: Xem registered models
- Compare: So sánh metrics giữa các runs
- Promote: Promote models to Production

---

## ⚙️ CONFIGURATION

### Environment Variables

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=http://mlflow:5000  # Internal (Docker)
MLFLOW_TRACKING_URI=http://localhost:5000  # External (Development)

# Auto-Update Settings
MLFLOW_ENABLED=true
MLFLOW_UPDATE_INTERVAL_MINUTES=30

# F1 Thresholds
MLFLOW_TEXT_F1_THRESHOLD=0.75
MLFLOW_VIDEO_F1_THRESHOLD=0.70
MLFLOW_FUSION_F1_THRESHOLD=0.80
```

### Model Registry Stages

```
None → Staging → Production

Auto-promote rules:
- F1 > threshold → Promote to "Production"
- Manual promote qua MLflow UI hoặc API
```

---

## 📊 SO SÁNH TRƯỚC/SAU

### Trước MLflow:

| Task | Method | Issues |
|------|--------|--------|
| **Model Management** | Hardcoded paths trong code | ❌ Khó track versions |
| **Model Update** | Manual copy/restart | ❌ Tốn thời gian, dễ sai |
| **Metrics Tracking** | Logs files | ❌ Khó so sánh |
| **Model Registry** | Không có | ❌ Khó quản lý |

### Sau MLflow:

| Task | Method | Benefits |
|------|--------|----------|
| **Model Management** | MLflow Model Registry | ✅ Version control, stages |
| **Model Update** | Auto-update mỗi 30p | ✅ Tự động, không cần restart |
| **Metrics Tracking** | MLflow Tracking | ✅ So sánh, charts, search |
| **Model Registry** | MLflow Registry | ✅ Production-ready models |

---

## 🧪 TESTING

### Test 1: MLflow Connection

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
"
```

### Test 2: Log Model

```python
# test_mlflow_log.py
from train_eval_module.shared_utils.mlflow_logger import log_text_model

log_text_model(
    model_path="train_eval_module/text/output/xlm-roberta-base/train/best_checkpoint",
    metrics={"eval_f1": 0.85, "eval_accuracy": 0.90},
    params={"model_name": "xlm-roberta-base"},
    model_name="xlm-roberta-base",
)
```

### Test 3: Auto-Updater

```python
# test_auto_updater.py
from streaming.mlflow.model_updater import ModelAutoUpdater

updater = ModelAutoUpdater(
    check_interval_minutes=1,  # Test với 1 phút
    current_metrics={"text": 0.80, "video": 0.75, "fusion": 0.85},
)

# Check once
updater.check_and_update_models()
```

---

## ⚠️ TROUBLESHOOTING

### Issue 1: MLflow connection failed

**Error:** `Connection refused to http://mlflow:5000`

**Solution:**
- Kiểm tra MLflow container: `docker ps | grep mlflow`
- Kiểm tra network: `docker network inspect tiktok-network`
- Kiểm tra env var: `MLFLOW_TRACKING_URI`

### Issue 2: Model not found in registry

**Error:** `No model found in registry for text`

**Solution:**
- Đảm bảo đã log model sau training
- Kiểm tra experiment name match
- Kiểm tra model registry name match

### Issue 3: F1 score not found

**Error:** `No F1 score found for latest model`

**Solution:**
- Đảm bảo metrics được log với key "eval_f1" hoặc "f1"
- Kiểm tra run metrics trong MLflow UI

### Issue 4: Model download failed

**Error:** `Failed to download model`

**Solution:**
- Kiểm tra artifact store path
- Kiểm tra permissions
- Kiểm tra disk space

---

## 📝 NEXT STEPS

### 1. ⏳ Integrate vào Training Scripts

Cần modify các training scripts để log vào MLflow:

- `train_eval_module/text/train.py` - Thêm `log_text_model()` sau training
- `train_eval_module/video/train.py` - Thêm `log_video_model()` sau training
- `train_eval_module/fusion/train.py` - Thêm `log_fusion_model()` sau training

**Xem hướng dẫn:** `MLFLOW_INTEGRATION_GUIDE.md` section 3

### 2. ⏳ Integrate Auto-Updater vào Streaming

Cần modify `spark_processor.py` để enable auto-update:

- Thêm `ModelAutoUpdater` vào `main()`
- Update `current_metrics` từ actual test results
- Handle model path updates

**Xem hướng dẫn:** `MLFLOW_INTEGRATION_GUIDE.md` section 4

### 3. ⏳ Test End-to-End

- Train model → Log vào MLflow → Check registry → Auto-update trong streaming

---

## 🎯 KẾT LUẬN

### ✅ Đã setup hoàn tất:

1. ✅ MLflow Server running (port 5000)
2. ✅ MLflow Client utilities ready
3. ✅ Auto-Updater mechanism ready
4. ✅ MLflow Logger ready
5. ✅ Documentation complete

### ⏳ Cần integrate tiếp:

1. ⏳ Modify training scripts để log vào MLflow
2. ⏳ Integrate auto-updater vào spark_processor.py
3. ⏳ Test end-to-end workflow

### 📚 Documentation:

- **`MLFLOW_INTEGRATION_GUIDE.md`** - Hướng dẫn chi tiết từng bước
- **`MLFLOW_SETUP_COMPLETE.md`** - Quick start guide
- **`UI_UX_CHECKLIST.md`** - UI/UX issues list

---

## 🔗 LINKS

- **MLflow UI:** http://localhost:5000
- **MLflow Docs:** https://mlflow.org/docs/latest/index.html
- **Integration Guide:** `MLFLOW_INTEGRATION_GUIDE.md`

---

**MLflow integration setup đã hoàn tất! Bạn có thể bắt đầu integrate vào training scripts theo hướng dẫn trong `MLFLOW_INTEGRATION_GUIDE.md`.**
