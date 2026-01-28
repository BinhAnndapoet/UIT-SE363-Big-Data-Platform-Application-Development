# 📊 GIT_STATUS_REPORT.md - Pre-Push Analysis

> **Date:** 2026-01-22  
> **Repository:** https://github.com/BinhAnndapoet/UIT-SE363-Big-Data-Platform-Application-Development

---

## 📋 SUMMARY

| Category | Count | Size |
|----------|-------|------|
| Modified Files | 5 | - |
| Deleted Files | 1 | - |
| Untracked (New) | 17 | ~140GB |

---

## 🔍 ALREADY COMMITTED (TRACKED)

**Latest Commit:** `aeb23d3` - "add: processed text data"

**Tracked folders/files:**
- `data/` - Video data với LFS (đã push trước đó)
- `data_1/` - Video data với LFS (đã push trước đó)
- `.gitignore`, `.gitattributes`
- `ScrapingVideoTiktok*.ipynb`
- `cookies.txt`, `crawl_tiktok_links_update_v1.py`

---

## 🔄 MODIFIED (Need Commit)

| File | Status |
|------|--------|
| `.gitignore` | M (Modified) |
| `ScrapingVideoTiktok.ipynb` | M (Modified) |
| `cookies.txt` | M (Modified) |
| `crawl_tiktok_links_update_v1.py` | M (Modified) |
| `create_sub_samples_tiktok_links.ipynb` | M (Modified) |

---

## ❌ DELETED

| File | Status |
|------|--------|
| `data/comments_labelled.csv` | D (Deleted) |

---

## 🆕 UNTRACKED (Not yet added to git)

### Major Folders (Large)

| Folder | Size | Notes |
|--------|------|-------|
| `streaming/` | **21GB** | ⚠️ Contains `state/` (20GB runtime data) |
| `train_eval_module/` | **114GB** | ⚠️ Contains model checkpoints (~100GB) |
| `data_viet/` | **5.1GB** | Dataset videos |
| `processed_data/` | ? | Processed data files |

### Files

| File | Notes |
|------|-------|
| `.vscode/` | Editor config |
| `ANALYSIS_REPORT.md` | Analysis report |
| `DOCKER_OPTIMIZATION_REPORT.md` | Docker report |
| `FUSION_INTEGRATION_SUMMARY.md` | Fusion summary |
| `MLFLOW_FINAL_REPORT.md` | MLflow report |
| `MLFLOW_INTEGRATION_GUIDE.md` | MLflow guide |
| `MLFLOW_SETUP_COMPLETE.md` | MLflow setup |
| `UI_UX_CHECKLIST.md` | UI/UX checklist |
| `ScrapingVideoTiktok.py` | Python script |
| `ScrapingVideoTiktok_out_viet.ipynb` | Notebook |
| `ScrapingVideoTiktok_out_viet.py` | Python script |
| `crawl_tiktok_links_update_viet.py` | Crawler script |
| `eda.ipynb` | EDA notebook |
| `pipeine.txt` | Pipeline notes |

---

## 📦 GIT LFS STATUS

**Tracked by LFS:**
```
*.mp4 filter=lfs diff=lfs merge=lfs -text
```

**Should add to LFS:**
```
*.safetensors  # Model weights
*.bin          # PyTorch model files
*.ckpt         # Checkpoints
```

---

## 🗑️ SHOULD ADD TO .gitignore (streaming/state/)

`streaming/state/` contains 20GB of **runtime data** that should NOT be pushed:

| Folder | Size | Description |
|--------|------|-------------|
| `airflow_logs/` | Logs | Runtime logs |
| `chrome_profile/` | Browser | Selenium profile |
| `ivy2/` | Cache | Spark dependencies |
| `minio_data/` | Storage | MinIO object data |
| `mlflow_artifacts/` | Models | MLflow artifacts |
| `mlflow_backend/` | DB | MLflow SQLite |
| `postgres_data/` | DB | PostgreSQL data |
| `spark_checkpoints/` | Checkpoints | Spark streaming |

**Recommended addition to .gitignore:**
```gitignore
# Streaming runtime state (regenerated on docker-compose up)
streaming/state/
```

---

## ✅ RECOMMENDED ACTIONS BEFORE PUSH

1. **Add `streaming/state/` to .gitignore** (or manually exclude)
2. **Configure LFS for model files** (if pushing train_eval_module)
3. **Stage and commit** the untracked files
4. **Push** to GitHub

---

## ⚠️ SIZE WARNING

Total untracked data is approximately **140GB**. 

If pushing everything:
- Use Git LFS for large binary files
- Consider excluding model checkpoints (download from HuggingFace Hub instead)

---

> **Note:** Data folders (`data`, `data_1`, `data_viet`) are OK to push with LFS for team sharing.
