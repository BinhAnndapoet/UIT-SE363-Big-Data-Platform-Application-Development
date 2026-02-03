# 🤖 Model Training Module - TikTok Safety Classification

## 📋 Overview

This module contains training scripts for:
- **Text Classification**: Vietnamese/multilingual text safety detection
- **Video Classification**: Video frame-based harmful content detection
- **Fusion Model**: Multimodal late fusion combining text + video

---

## 🚀 Quick Start

### Prerequisites

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# For GPU training (recommended)
# Make sure CUDA is installed, PyTorch will auto-detect
```

### Data Preparation

Place training data in `processed_data/`:
```
processed_data/
├── text/
│   ├── train_split.csv
│   ├── eval_split.csv
│   └── test_split.csv
└── fusion/
    └── fusion_data.parquet
```

CSV format for text:
```csv
text,label
"Content here...",0
"Harmful content...",1
```

Video data should be in `data/` folder with structure matching CSV paths.

---

## 🏋️ Training Models

### 1. Text Model

```bash
cd train_eval_module

# Train with CafeBERT (Vietnamese - model_idx=0)
python -m text.train --model_idx 0 --metric_type eval_f1

# Train with XLM-RoBERTa (Multilingual - model_idx=1)
python -m text.train --model_idx 1 --metric_type eval_f1

# Train with DistilBERT (Lighter - model_idx=2)
python -m text.train --model_idx 2 --metric_type eval_f1
```

Available models:
| idx | Model | Description |
|-----|-------|-------------|
| 0 | uitnlp/CafeBERT | Vietnamese BERT (best for VN text) |
| 1 | xlm-roberta-base | Multilingual (best for mixed languages) |
| 2 | distilbert-base-multilingual-cased | Lighter, faster |

Output: `text/output/{model_name}/train_{metric_type}/best_checkpoint/`

### 2. Video Model

```bash
cd train_eval_module

# Train with VideoMAE (recommended - model_idx=0)
python -m video.train --model_idx 0

# Train with TimeSformer (model_idx=1)
python -m video.train --model_idx 1
```

Available models:
| idx | Model | Description |
|-----|-------|-------------|
| 0 | MCG-NJU/videomae-base-finetuned-kinetics | VideoMAE (87M params) |
| 1 | facebook/timesformer-base-finetuned-k400 | TimeSformer (121M params) |
| 2 | google/vivit-b-16x2-kinetics400 | ViViT (heavy but accurate) |

Output: `video/output/{model_name}/train/best_checkpoint/`

### 3. Fusion Model

> ⚠️ **Prerequisite**: Train text and video models first!

```bash
cd train_eval_module

# Train Late Fusion (text + video)
python -m fusion.train
```

Uses pre-trained:
- Text: `text/output/xlm-roberta-base/train/best_checkpoint/`
- Video: `video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint/`

Output: `fusion/output/fusion_videomae/`

### 4. Offline Training (No MLflow)

> 💡 Use `--no-mlflow` flag to train without MLflow server connection.

```bash
cd train_eval_module

# Text model without MLflow
python -m text.train --model_idx 0 --no-mlflow

# Video model without MLflow
python -m video.train --model_idx 0 --no-mlflow

# Fusion model without MLflow
python -m fusion.train --no-mlflow
```

Alternatively, set the environment variable:
```bash
export ENABLE_MLFLOW=false
python -m text.train --model_idx 0
```

---

## 🧪 Testing Models

```bash
# Test text model
python -m text.test --model_path text/output/uitnlp_CafeBERT/train/best_checkpoint

# Test video model
python -m video.test --model_path video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint

# Test fusion model
python -m fusion.test --model_path fusion/output/fusion_videomae
```

---

## 📤 Push to HuggingFace Hub

```bash
# Install huggingface-hub
pip install huggingface-hub

# Login
huggingface-cli login

# Push model
python scripts/push_hf_model.py \
    --model_path text/output/uitnlp_CafeBERT/train/best_checkpoint \
    --repo-id your-username/tiktok-text-safety-classifier
```

---

## 📁 Folder Structure

```
train_eval_module/
├── text/                       # Text classification
│   ├── train.py                # Training script
│   ├── test.py                 # Evaluation script
│   ├── text_configs.py         # Hyperparameters
│   └── output/                 # Trained models
│
├── video/                      # Video classification
│   ├── train.py
│   ├── test.py
│   ├── video_configs.py
│   └── output/
│
├── fusion/                     # Multimodal fusion
│   ├── train.py
│   ├── test.py
│   ├── fusion_configs.py
│   ├── src/model.py            # LateFusionModel class
│   └── output/
│
├── audio/                      # Audio (experimental)
├── shared_utils/               # Common utilities
│   ├── logger.py
│   └── data_loader.py
│
├── scripts/                    # Utility scripts
│   ├── push_hf_model.py        # Push to HF Hub
│   └── download_missing_videos.py
│
├── configs/                    # Global configs
├── data_splits/                # Train/val/test splits
└── requirements.txt            # Dependencies
```

---

## 📊 Training Results (Expected)

| Model | F1 Score | Notes |
|-------|----------|-------|
| Text (CafeBERT) | ~0.80+ | Best for Vietnamese |
| Text (XLM-RoBERTa) | ~0.78+ | Best for multilingual |
| Video (VideoMAE) | ~0.72+ | CPU-intensive |
| Fusion | ~0.82+ | Best overall performance |

---

## ⚙️ Configuration

Edit config files to customize training:

- `text/text_configs.py` - Text hyperparameters
- `video/video_configs.py` - Video hyperparameters
- `fusion/fusion_configs.py` - Fusion hyperparameters

Key parameters:
```python
# Batch size & accumulation
"batch_size": 8,
"grad_accum": 8,  # Effective batch = 64

# Learning rate
"lr": 1.5e-5,
"lr_scheduler_type": "cosine",
"warmup_ratio": 0.15,

# Early stopping
"stop_patience": 3,
"metric_for_best_model": "eval_f1"
```

---

## 🔗 Related Documentation

- [Main README](../README.md) - Full project overview
- [Streaming Pipeline](../streaming/README.md) - Deployment guide
- [MLflow Integration](../docs/mlflow/MLFLOW_INTEGRATION_GUIDE.md) - Model registry
