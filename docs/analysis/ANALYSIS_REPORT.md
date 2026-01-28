# 📊 BÁO CÁO PHÂN TÍCH HỆ THỐNG
## Multimodal Real-Time Detection of Harmful TikTok Content

> **Ngày tạo:** 2025-01-27  
> **Phiên bản:** 1.0  
> **Mục đích:** Phân tích chi tiết cấu trúc hệ thống, các đường dẫn config, models và streaming pipeline

---

## 📋 MỤC LỤC

1. [Danh sách đường dẫn từ các file config](#1-danh-sách-đường-dẫn-từ-các-file-config)
2. [Phân tích chi tiết train_eval_module](#2-phân-tích-chi-tiết-train_eval_module)
3. [Phân tích chi tiết streaming pipeline](#3-phân-tích-chi-tiết-streaming-pipeline)

---

## 1. DANH SÁCH ĐƯỜNG DẪN TỪ CÁC FILE CONFIG

### 1.1. Train Eval Module Configs

#### 📁 `train_eval_module/configs/paths.py`

**Đường dẫn Base:**
```
CURRENT_DIR = train_eval_module/
BASE_PROJECT_PATH = .. (root project)/
```

**Đường dẫn Data Sources (Raw):**
- `DATA_SOURCES = ["data", "data_1", "data_viet"]`
- Video directories tự động quét:
  - `{BASE_PROJECT_PATH}/data/videos/harmful/`
  - `{BASE_PROJECT_PATH}/data/videos/not_harmful/`
  - `{BASE_PROJECT_PATH}/data_1/videos/harmful/`
  - `{BASE_PROJECT_PATH}/data_1/videos/not_harmful/`
  - `{BASE_PROJECT_PATH}/data_viet/videos/harmful/`
  - `{BASE_PROJECT_PATH}/data_viet/videos/not_harmful/`

**Đường dẫn Text Data:**
- `TEXT_LABEL_FILE = {BASE_PROJECT_PATH}/processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv`
- `TEXT_TRAIN_CSV = {BASE_PROJECT_PATH}/processed_data/text/train_split.csv`
- `TEXT_VAL_CSV = {BASE_PROJECT_PATH}/processed_data/text/eval_split.csv`
- `TEXT_TEST_CSV = {BASE_PROJECT_PATH}/processed_data/text/test_split.csv`

**Đường dẫn Video Splits (Master Index):**
- `MASTER_TRAIN_INDEX = train_eval_module/data_splits/train_split.json`
- `MASTER_VAL_INDEX = train_eval_module/data_splits/val_split.json`
- `MASTER_TEST_INDEX = train_eval_module/data_splits/test_split.json`

**Đường dẫn Fusion Data:**
- `FUSION_TRAIN_JSON = {BASE_PROJECT_PATH}/processed_data/fusion/train_fusion.json`
- `FUSION_VAL_JSON = {BASE_PROJECT_PATH}/processed_data/fusion/val_fusion.json`
- `FUSION_TEST_JSON = {BASE_PROJECT_PATH}/processed_data/fusion/test_fusion.json`

**Đường dẫn Output/Logs:**
- `OUTPUT_DIR = train_eval_module/output/`
- `LOG_DIR = train_eval_module/logs/`
- `PROCESSED_DIR = {BASE_PROJECT_PATH}/processed_data/`
- `AUDIO_DATA_DIR = {BASE_PROJECT_PATH}/processed_data/audios/`

#### 📁 `train_eval_module/text/text_configs.py`

**Model Paths:**
- Text model checkpoints:
  - `train_eval_module/text/output/uitnlp_CafeBERT/train/best_checkpoint/`
  - `train_eval_module/text/output/xlm-roberta-base/train/best_checkpoint/`
  - `train_eval_module/text/output/distilbert-base-multilingual-cased/train/best_checkpoint/`

**Log Paths:**
- `train_eval_module/text/logs/{model_name}/test_results_{model_name}.json`

#### 📁 `train_eval_module/video/video_configs.py`

**Model Configs:**
- VideoMAE: `MCG-NJU/videomae-base-finetuned-kinetics`
- TimeSformer: `facebook/timesformer-base-finetuned-k400`
- ViViT: `google/vivit-b-16x2-kinetics400`

**Output Paths:**
- `train_eval_module/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint/`

#### 📁 `train_eval_module/fusion/fusion_configs.py`

**Model Paths (Fusion Input):**
- `text_model_path = train_eval_module/text/output/xlm-roberta-base/train/best_checkpoint`
- `video_model_path = train_eval_module/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint`

**Fusion Output:**
- `train_eval_module/fusion/output/fusion_videomae/checkpoint-{epoch}/`

#### 📁 `train_eval_module/audio/audio_configs.py`

**Audio Models:**
- `microsoft/wavlm-base`
- `microsoft/wavlm-base-plus`
- `facebook/wav2vec2-base`

**Audio Output:**
- `train_eval_module/audio/output/`
- `train_eval_module/audio/audio_model/checkpoint-{epoch}/`

### 1.2. Streaming Module Configs

#### 📁 `streaming/ingestion/config.py`

**Container Paths (Docker):**
- `BASE_DIR = /opt/project/streaming/ingestion`
- `STREAMING_DIR = /opt/project/streaming`
- `DATA_DIR = /opt/project/streaming/data`

**Local Paths (Development):**
- `DATA_DIR = streaming/data/`
- `CRAWL_DIR = streaming/data/crawl/`
- `VIDEO_DIR = streaming/data/videos/`
- `AUDIO_DIR = streaming/data/audios/`
- `TEMP_DOWNLOAD_DIR = streaming/ingestion/temp_downloads/`

**File Paths:**
- `INPUT_CSV_PATH = streaming/data/crawl/tiktok_links_viet.csv`
- `COOKIES_PATH = streaming/ingestion/cookies.txt`

**Service Endpoints:**
- `MINIO_ENDPOINT = minio:9000` (internal) / `localhost:9000` (external)
- `KAFKA_BOOTSTRAP_SERVERS = ["kafka:29092"]` (internal) / `["localhost:9092"]` (external)
- `KAFKA_TOPIC = "tiktok_raw_data"`
- `MINIO_BUCKET = "tiktok-raw-videos"`
- `MINIO_AUDIO_BUCKET = "tiktok-raw-audios"`

#### 📁 `streaming/processing/spark_processor.py`

**Model Paths (Mounted in Docker):**
- `PATH_TEXT_MODEL = /models/text/output/uitnlp_CafeBERT/train/best_checkpoint_FocalLoss`
- `PATH_VIDEO_MODEL = /models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint`
- `PATH_AUDIO_MODEL = /models/audio/audio_model/checkpoint-2300`

**Local Mapping:**
- Docker volume mount: `../train_eval_module:/models`
- Spark checkpoint: `/opt/spark/checkpoints/tiktok_multimodal` → `streaming/state/spark_checkpoints/`

**Database:**
- `POSTGRES_HOST = postgres` (container) / `localhost` (external)
- `POSTGRES_PORT = 5432`
- `POSTGRES_DB = tiktok_safety_db`
- `POSTGRES_USER = user`
- `POSTGRES_PASSWORD = password`

#### 📁 `streaming/docker-compose.yml`

**Volume Mounts:**
- `./processing:/app/processing` → Spark code
- `./ingestion:/app/ingestion` → Ingestion code
- `../train_eval_module:/models` → AI models
- `./state/minio_data:/data` → MinIO storage
- `./state/postgres_data:/var/lib/postgresql/data` → Postgres data
- `./state/airflow_logs:/opt/airflow/logs` → Airflow logs
- `./state/spark_checkpoints:/opt/spark/checkpoints` → Spark checkpoints
- `./state/ivy2:/tmp/.ivy2` → Spark dependencies cache
- `./state/chrome_profile:/workspace/chrome_profile` → Chrome profile
- `./airflow/dags:/opt/airflow/dags` → Airflow DAGs
- `./dashboard:/app` → Dashboard code

**Service Ports:**
- Zookeeper: `2181`
- Kafka: `9092` (external), `29092` (internal)
- MinIO: `9000` (API), `9001` (Console)
- Postgres: `5432`
- Spark Master: `9090` (UI), `7077` (RPC)
- Airflow: `8080` (Webserver)
- Dashboard: `8501`

#### 📁 `streaming/airflow/dags/`

**DAG Paths:**
- `1_TIKTOK_ETL_COLLECTOR.py` → DAG ID: `1_TIKTOK_ETL_COLLECTOR`
- `2_TIKTOK_STREAMING_PIPELINE.py` → DAG ID: `2_TIKTOK_STREAMING_PIPELINE`

**Task Paths (Container):**
- `INGESTION_PATH = /opt/project/streaming/ingestion`
- `DATA_DIR = /opt/project/streaming/data`

#### 📁 `streaming/infra/postgres/init.sql`

**Database Schema:**
- Table: `processed_results`
- Table: `system_logs`

---

## 2. PHÂN TÍCH CHI TIẾT TRAIN_EVAL_MODULE

### 2.1. Tổng quan cấu trúc

```
train_eval_module/
├── text/              # Text classification models
├── video/             # Video classification models
├── audio/             # Audio classification models
├── fusion/            # Multimodal fusion models
├── configs/           # Shared configuration (paths)
├── data_splits/       # Train/val/test JSON splits
├── output/            # Model checkpoints
└── logs/              # Training logs
```

### 2.2. TEXT MODELS

#### 2.2.1. Models được sử dụng

**1. CafeBERT (`uitnlp/CafeBERT`)**
- **Mục đích:** Tối ưu cho tiếng Việt
- **Kiến trúc:** BERT-based (Vietnamese)
- **Tham số:** ~110M
- **Config:**
  - `max_text_len: 512`
  - `batch_size: 8`
  - `grad_accum: 8` (effective batch = 64)
  - `lr: 1.5e-5`
  - `epochs: 10`

**2. XLM-RoBERTa (`xlm-roberta-base`)**
- **Mục đích:** Tốt cho dữ liệu đa ngôn ngữ (Anh/Việt/Hàn...)
- **Kiến trúc:** RoBERTa-based (Multilingual)
- **Tham số:** ~270M
- **Config:**
  - `max_text_len: 512`
  - `batch_size: 8`
  - `grad_accum: 8`
  - `lr: 1.5e-5`
  - `epochs: 10`

**3. DistilBERT (`distilbert-base-multilingual-cased`)**
- **Mục đích:** Nhẹ, nhanh, đa ngôn ngữ
- **Kiến trúc:** Distilled BERT (Multilingual)
- **Tham số:** ~134M
- **Config:**
  - `max_text_len: 512`
  - `batch_size: 32`
  - `grad_accum: 2` (effective batch = 64)
  - `lr: 3e-5`
  - `epochs: 15`

#### 2.2.2. Phương pháp xử lý Text

**Input Processing:**
1. **Text Aggregation:** Gộp nhiều comments thành 1 string
   - Format: `comment1 [SEP] comment2 [SEP] ...`
   - Max length: 512 tokens (tự động truncate bởi tokenizer)

2. **Tokenization:**
   - Dùng AutoTokenizer từ HuggingFace
   - Padding/truncation tự động
   - Special tokens: `[CLS]`, `[SEP]`, `[PAD]`

3. **Model Architecture:**
   - **Backbone:** Pretrained encoder (BERT/RoBERTa)
   - **Head:** Classification head (2 classes: safe/harmful)
   - **Dropout:** 0.1 (hidden_dropout_prob, attention_probs_dropout_prob)
   - **Output:** Logits → Softmax → Probability

**Training Strategy:**
- **Loss Function:** CrossEntropyLoss với class weights
- **Class Weights:** `[0.5808, 3.5942]` (harmful boost ~6x) - xử lý class imbalance
- **Optimizer:** AdamW
- **Scheduler:** Cosine annealing với warmup (15% epochs)
- **Regularization:**
  - Weight decay: 0.1
  - Max grad norm: 1.0
  - Label smoothing: 0.05
- **Early Stopping:** Patience = 3 epochs
- **Metric:** Eval F1 (weighted F1) làm best model selection

**Model Loading (inference):**
```python
# File: text/src/model.py
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
# Forward: [CLS] token embedding → classifier → logits
```

### 2.3. VIDEO MODELS

#### 2.3.1. Models được sử dụng

**1. VideoMAE (`MCG-NJU/videomae-base-finetuned-kinetics`)**
- **Mục đích:** Model chính được sử dụng (balance tốt giữa accuracy và speed)
- **Kiến trúc:** Video Masked Autoencoder (Vision Transformer)
- **Tham số:** ~87M
- **Processor:** VideoMAEImageProcessor
- **Config:**
  - `num_frames: 16`
  - `image_size: 224`
  - `batch_size: 4`
  - `grad_accum: 16` (effective batch = 64)
  - `lr: 3e-5`

**2. TimeSformer (`facebook/timesformer-base-finetuned-k400`)**
- **Kiến trúc:** Space-Time Attention
- **Tham số:** ~121M
- **Processor:** AutoImageProcessor

**3. ViViT (`google/vivit-b-16x2-kinetics400`)**
- **Kiến trúc:** Video Vision Transformer
- **Tham số:** ~300M+
- **Processor:** VivitImageProcessor

#### 2.3.2. Phương pháp xử lý Video

**Frame Extraction:**
1. **Decord VideoReader:** Đọc video MP4
2. **Frame Sampling:** Uniform sampling 16 frames
   - Công thức: `indices = np.linspace(0, len(video)-1, 16).astype(int)`
   - 16 frames được chọn đều nhau từ video

**Preprocessing:**
1. **VideoMAE Processor:**
   - Resize frames → 224x224
   - Normalize pixel values
   - Format: `(Batch, Channels, Time, Height, Width)` = `(B, 3, 16, 224, 224)`

2. **Model Input:**
   - VideoMAE: Patch embedding → Transformer encoder → Classification token
   - Output shape: `(B, 768)` feature vector

**Model Architecture:**
```python
# File: video/src/model.py
processor = VideoMAEImageProcessor.from_pretrained(model_name)
model = VideoMAEForVideoClassification.from_pretrained(
    model_name,
    num_labels=2,  # safe/harmful
    hidden_dropout_prob=0.1,
    attention_probs_dropout_prob=0.1
)
```

**Training Strategy:**
- **Loss:** CrossEntropyLoss
- **Optimizer:** AdamW (lr=3e-5, weight_decay=0.01)
- **Scheduler:** Cosine với warmup 10%
- **Metric:** Eval F1
- **Checkpointing:** Best model theo eval_f1

### 2.4. AUDIO MODELS

#### 2.4.1. Models được sử dụng

**1. WavLM (`microsoft/wavlm-base`)**
- **Kiến trúc:** Self-supervised speech model
- **Tham số:** ~95M

**2. WavLM Plus (`microsoft/wavlm-base-plus`)**
- **Tham số:** ~95M+ (enhanced)

**3. Wav2Vec2 (`facebook/wav2vec2-base`)**
- **Kiến trúc:** Self-supervised audio model
- **Tham số:** ~95M

#### 2.4.2. Phương pháp xử lý Audio

**Audio Preprocessing:**
1. **Extraction:** FFmpeg extract audio từ video MP4 → WAV
2. **Sampling Rate:** 16kHz
3. **Max Duration:** 10 seconds (truncate/pad)
4. **Feature Extraction:**
   - AutoFeatureExtractor từ HuggingFace
   - Raw audio waveform → Spectrogram features

**Config:**
- `sampling_rate: 16000`
- `max_duration_sec: 10.0`
- `batch_size: 4`
- `grad_accum: 8` (effective batch = 32)
- **Dropout OFF:** Tất cả dropout = 0.0 (giải quyết underfitting)

**Training Strategy:**
- **Loss:** CrossEntropyLoss
- **Metric:** Accuracy (không dùng F1 do data imbalance ít hơn)
- **Warmup:** 10%
- **Early Stopping:** Patience = 5

### 2.5. FUSION MODEL

#### 2.5.1. Kiến trúc Late Fusion

**Mô hình:**
```
Text Backbone (XLM-RoBERTa) → Text Features (768-dim)
Video Backbone (VideoMAE)    → Video Features (768-dim)
                                  ↓
                         Fusion Layer
                                  ↓
                        Classifier (2 classes)
```

#### 2.5.2. Chiến lược Fusion

**1. Concat Fusion (Simple):**
```python
combined = concat(text_feat * text_weight, video_feat * video_weight)
# Output: (B, 1536) → Classifier → (B, 2)
```
- **Weights:** `text_weight=0.5`, `video_weight=0.5`
- **Fusion hidden:** 256
- **Classifier:** Linear(1536 → 256 → 2)

**2. Attention Fusion (Advanced):**
```python
# Cross-Modal Attention
text_attended = CrossAttention(text_proj, video_proj)  # Text attends to Video
video_attended = CrossAttention(video_proj, text_proj) # Video attends to Text
# Gating mechanism
gate = Sigmoid(Linear(concat(text_attended, video_attended)))
combined = gate * text_attended + (1 - gate) * video_attended
```
- **Attention heads:** 4
- **Fusion hidden:** 256
- **Gating:** Adaptive weighting giữa text và video

#### 2.5.3. Fine-tuning Strategy

**Unfreeze Strategy:**
- **Text backbone:** Unfreeze last 2 layers (default: full freeze)
- **Video backbone:** Unfreeze last 2 layers (default: full freeze)
- **Classifier:** Always trainable

**Training Config:**
- `batch_size: 8`
- `grad_accum: 4` (effective batch = 32)
- `lr: 2e-5`
- `weight_decay: 0.05`
- `epochs: 10`
- `fusion_hidden: 256`
- `stop_patience: 5`

**Input Processing:**
- **Text:** 1 string đã concat (không cần CommentAggregator)
- **Video:** 16 frames, 224x224
- **Labels:** Binary (0=safe, 1=harmful)

**Model Implementation:**
```python
# File: fusion/src/model.py
class LateFusionModel(nn.Module):
    - text_backbone: AutoModel (frozen, last 2 layers unfrozen)
    - video_backbone: AutoModel (frozen, last 2 layers unfrozen)
    - fusion_layer: Concat or Attention
    - classifier: Sequential(Linear, BatchNorm, ReLU, Dropout, Linear)
```

---

## 3. PHÂN TÍCH CHI TIẾT STREAMING PIPELINE

### 3.1. Tổng quan Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AIRFLOW ORCHESTRATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DAG 1: ETL COLLECTOR                                         │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Check DB     │────────▶│ Crawl Links  │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                                   ▼                          │
│                         CSV: tiktok_links_viet.csv          │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DAG 2: STREAMING PIPELINE (Self-loop)                      │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐               │
│  │Prepare  │─▶│Check Infra│─▶│Ingestion    │               │
│  └─────────┘  └──────────┘  └──────┬──────┘               │
│                                     │                        │
│  ┌─────────┐  ┌──────────┐  ┌─────▼─────┐                 │
│  │Loop     │◀─│Wait 30s  │◀─│Verify Spark│                │
│  └─────────┘  └──────────┘  └────────────┘                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [1] INGESTION LAYER                                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │Download    │───▶│Extract Audio│───▶│Upload MinIO│        │
│  │(yt-dlp)    │    │(ffmpeg)     │    │(S3 API)    │        │
│  └────────────┘    └────────────┘    └──────┬─────┘        │
│                                               │              │
│                                               ▼              │
│  [2] KAFKA LAYER                                            │
│  ┌────────────────────────────────────────────┐             │
│  │ Topic: tiktok_raw_data                     │             │
│  │ Message: {video_id, minio_path, text, ...}│             │
│  └──────────────┬─────────────────────────────┘             │
│                 │                                            │
│                 ▼                                            │
│  [3] SPARK LAYER                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Spark Streaming Processor                        │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │       │
│  │  │Text Model│  │Video Model│  │Audio Model│      │       │
│  │  │(CafeBERT)│  │(VideoMAE)│  │(WavLM)    │      │       │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘      │       │
│  │       │              │              │             │       │
│  │       ▼              ▼              ▼             │       │
│  │  text_score    video_score    audio_score        │       │
│  │       │              │              │             │       │
│  │       └──────────────┴──────────────┘             │       │
│  │                    │                              │       │
│  │                    ▼                              │       │
│  │          avg_score = TEXT*0.3 + VIDEO*0.7        │       │
│  │          final_decision = (avg >= 0.5) ? harmful │       │
│  └────────────────────┬─────────────────────────────┘       │
│                       │                                      │
│                       ▼                                      │
│  [4] DATABASE LAYER                                         │
│  ┌──────────────────────────────────────────┐              │
│  │ Postgres: processed_results (UPSERT)     │              │
│  └──────────────┬───────────────────────────┘              │
│                 │                                           │
│                 ▼                                           │
│  [5] DASHBOARD LAYER                                       │
│  ┌──────────────────────────────────────────┐              │
│  │ Streamlit: Real-time visualization       │              │
│  │ - Metrics, confusion matrix, time series        │              │
│  └──────────────────────────────────────────┘              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. CHI TIẾT TỪNG LAYER

#### 3.2.1. INGESTION LAYER

**Vị trí:** `streaming/ingestion/`

**Components:**
1. **Crawler (`crawler.py`):**
   - Selenium + Chrome headless (Xvfb)
   - Crawl TikTok links từ hashtags
   - Output: CSV `tiktok_links_viet.csv`
   - Risky hashtags filter (blacklist keywords)

2. **Downloader (`downloader.py`):**
   - yt-dlp wrapper để download video
   - Retry logic với backoff
   - Extract video ID từ URL
   - Extract comments từ TikTok API

3. **Audio Processor (`audio_processor.py`):**
   - FFmpeg extract audio từ video MP4 → WAV
   - 16kHz sampling rate
   - Max duration 10s

4. **Main Worker (`main_worker.py`):**
   - Orchestrate: Download → Audio → MinIO → Kafka
   - ThreadPoolExecutor (max_workers=2) để parallel processing
   - Cleanup temp files sau upload

5. **Clients:**
   - **MinioClient (`clients/minio_kafka_clients.py`):**
     - Upload video: `raw/{label}/{video_id}.mp4`
     - Upload audio: `raw/{label}/{video_id}.wav`
     - Buckets: `tiktok-raw-videos`, `tiktok-raw-audios`
   - **KafkaClient (`clients/minio_kafka_clients.py`):**
     - Producer gửi message JSON:
       ```json
       {
         "video_id": "...",
         "minio_video_path": "bucket/object",
         "minio_audio_path": "bucket/object",
         "clean_text": "...",
         "csv_label": "harmful|safe",
         "timestamp": 1234567890.0
       }
       ```
   - **Data Cleaner (`clients/data_cleaner.py`):**
     - Text normalization
     - Remove emoji, special chars
     - Lowercase conversion

**Workflow:**
```
CSV Input → Download Video → Extract Audio → Upload MinIO → Send Kafka
```

**Đường dẫn quan trọng:**
- Input: `streaming/data/crawl/tiktok_links_viet.csv`
- Temp: `streaming/ingestion/temp_downloads/`
- MinIO: `s3://tiktok-raw-videos/raw/{label}/{video_id}.mp4`
- Kafka: Topic `tiktok_raw_data`

#### 3.2.2. SPARK LAYER

**Vị trí:** `streaming/processing/spark_processor.py`

**Kiến trúc Spark Streaming:**
- **Format:** Kafka Stream (Structured Streaming)
- **Checkpoint:** `streaming/state/spark_checkpoints/tiktok_multimodal`
- **Starting Offsets:** `latest` (mặc định) hoặc `earliest`
- **Max Offsets Per Trigger:** 5 messages/batch

**Models Loading (Lazy):**
- **Text Model:** CafeBERT (`/models/text/output/uitnlp_CafeBERT/train/best_checkpoint_FocalLoss`)
- **Video Model:** VideoMAE (`/models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint`)
- **Audio Model:** WavLM (`/models/audio/audio_model/checkpoint-2300`) - placeholder

**Processing Logic:**

**1. Text Processing (UDF):**
```python
def process_text_logic(text):
    # Rule-based: Check blacklist keywords
    if any(kw in text.lower() for kw in BLACKLIST_KEYWORDS):
        return {"risk_score": 0.85, "verdict": "harmful"}
    # AI Model: CafeBERT inference
    inputs = tokenizer(text, ...)
    outputs = model(**inputs)
    probs = softmax(outputs.logits)
    return {"risk_score": probs[0][1], "verdict": "harmful" if probs[0][1] > 0.5 else "safe"}
```

**2. Video Processing (UDF):**
```python
def process_video_logic(video_id, minio_path):
    # Download từ MinIO → temp file
    s3.download_file(...)
    # Extract 16 frames (uniform sampling)
    vr = VideoReader(temp_file)
    indices = np.linspace(0, len(vr)-1, 16).astype(int)
    frames = vr.get_batch(indices)
    # VideoMAE inference
    inputs = processor(frames, ...)
    outputs = model(**inputs)
    probs = softmax(outputs.logits)
    return {"risk_score": probs[0][1], "verdict": "harmful" if probs[0][1] > 0.5 else "safe"}
```

**3. Score Aggregation:**
```python
# Weighted average
text_weight = 0.3  # ENV: TEXT_WEIGHT
video_weight = 0.7  # = 1.0 - text_weight
avg_score = text_score * text_weight + video_score * video_weight
final_decision = "harmful" if avg_score >= threshold else "safe"
# threshold = 0.5 (ENV: DECISION_THRESHOLD)
```

**4. Database Write (UPSERT):**
```sql
INSERT INTO processed_results (...) VALUES (...)
ON CONFLICT (video_id) DO UPDATE SET
    text_verdict = EXCLUDED.text_verdict,
    video_verdict = EXCLUDED.video_verdict,
    avg_score = EXCLUDED.avg_score,
    final_decision = EXCLUDED.final_decision,
    processed_at = CURRENT_TIMESTAMP
```

**Tối ưu hóa:**
- **Lazy Model Loading:** Chỉ load model khi cần (singleton pattern)
- **Persist:** `StorageLevel.MEMORY_AND_DISK` để cache UDF results
- **Batch Processing:** Micro-batches (5 messages/trigger)
- **De-dup:** Remove duplicate video_id trong cùng batch trước khi UPSERT

#### 3.2.3. DATABASE LAYER

**Vị trí:** `streaming/infra/postgres/init.sql`

**Schema:**

**Table `processed_results`:**
```sql
CREATE TABLE processed_results (
    video_id VARCHAR(50) PRIMARY KEY,
    raw_text TEXT,
    human_label VARCHAR(20),
    text_verdict VARCHAR(20),
    text_score FLOAT,
    video_verdict VARCHAR(20),
    video_score FLOAT,
    avg_score FLOAT,
    threshold FLOAT,
    final_decision VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table `system_logs`:**
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    dag_id VARCHAR(50),
    task_name VARCHAR(50),
    log_level VARCHAR(10),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes:** (nên thêm để tối ưu queries)
- `processed_at` (time-series queries)
- `final_decision` (filtering)

#### 3.2.4. AIRFLOW LAYER

**Vị trí:** `streaming/airflow/dags/`

**DAG 1: `1_TIKTOK_ETL_COLLECTOR`**
- **Schedule:** None (manual trigger) hoặc `0 */6 * * *` (6h interval)
- **Tasks:**
  1. `monitor_db_health`: Check Postgres connection
  2. `crawl_tiktok_links`: Run crawler (Xvfb mode, timeout 45min)
- **Output:** CSV `tiktok_links_viet.csv`

**DAG 2: `2_TIKTOK_STREAMING_PIPELINE`**
- **Schedule:** None (self-loop trigger)
- **Tasks:**
  1. `prepare_environment`: Check CSV file exists
  2. `check_kafka_infra`: Check Kafka connectivity
  3. `run_ingestion_worker`: Run ingestion (timeout 30min)
  4. `verify_spark_ai_result`: SqlSensor check processed_results (poke mode, 20s interval, 300s timeout)
  5. `wait_30s_cooldown`: Cooldown để giải phóng tài nguyên
  6. `loop_self_trigger`: Trigger lại chính nó (self-loop)
- **Concurrency:** `max_active_runs=1` (chỉ 1 instance tại 1 thời điểm)

**Executor:** LocalExecutor (cho phép parallel tasks trong cùng DAG)

**Logs:** `streaming/state/airflow_logs/`

#### 3.2.5. DASHBOARD LAYER

**Vị trí:** `streaming/dashboard/`

**Tech Stack:**
- Streamlit
- Plotly (charts)
- Pandas (data processing)
- SQLAlchemy (database queries)

**Features:**
- Real-time metrics (accuracy, precision, recall, F1)
- Confusion matrix
- Time series charts (processed_at)
- Video preview (MinIO public URL)

**Config:**
- Postgres connection từ env vars
- MinIO public endpoint từ env vars

### 3.3. DOCKER DEPLOYMENT STRUCTURE

#### 3.3.1. Docker Compose Services

**Infrastructure Services:**
1. **Zookeeper:**
   - Image: `confluentinc/cp-zookeeper:7.4.0`
   - Port: 2181
   - Purpose: Kafka coordination

2. **Kafka:**
   - Image: `confluentinc/cp-kafka:7.4.0`
   - Ports: 9092 (external), 29092 (internal)
   - Health check: `kafka-topics --list`
   - Purpose: Message queue

3. **MinIO:**
   - Image: `minio/minio`
   - Ports: 9000 (API), 9001 (Console)
   - Volumes: `./state/minio_data:/data`
   - Buckets: `tiktok-raw-videos`, `tiktok-raw-audios`
   - Init job: `minio-init` container tạo buckets

4. **Postgres:**
   - Image: `postgres:15`
   - Port: 5432
   - Volumes: `./state/postgres_data:/var/lib/postgresql/data`
   - Init scripts: `./infra/postgres/init.sql`

**Processing Services:**
5. **Spark Master:**
   - Build: `./spark/Dockerfile`
   - Ports: 9090 (UI), 7077 (RPC)
   - Volumes: Models, processing code

6. **Spark Worker:**
   - Build: `./spark/Dockerfile`
   - Memory: 12g worker, 10g executor
   - Volumes: Models, processing code

7. **Spark Processor:**
   - Build: `./spark/Dockerfile`
   - Auto-start: Spark streaming job
   - Volumes: Checkpoints, ivy2 cache
   - Env vars: TEXT_WEIGHT, DECISION_THRESHOLD, KAFKA_STARTING_OFFSETS

**Orchestration Services:**
8. **Airflow DB:**
   - Image: `postgres:13`
   - Purpose: Airflow metadata

9. **Airflow Init:**
   - Build: `./airflow/Dockerfile.airflow`
   - One-shot: Initialize DB + create admin user

10. **Airflow Webserver:**
    - Build: `./airflow/Dockerfile.airflow`
    - Port: 8080
    - Volumes: DAGs, logs, ingestion code

11. **Airflow Scheduler:**
    - Build: `./airflow/Dockerfile.airflow`
    - Shm: 2gb (cho Chrome)
    - Volumes: DAGs, logs, chrome_profile

**UI Services:**
12. **Dashboard:**
    - Build: `./dashboard/Dockerfile.dashboard`
    - Port: 8501
    - Volumes: Dashboard code

13. **DB Migrator:**
    - Image: `postgres:15`
    - One-shot: Create `system_logs` table

#### 3.3.2. Dockerfile Optimizations

**Spark Dockerfile (`streaming/spark/Dockerfile`):**
```dockerfile
# LAYER 1: System deps (rarely changes)
RUN apt-get install ffmpeg libsndfile1 ...

# LAYER 2: Python constraints (rarely changes)
RUN pip install "typing-extensions<4.6.0" "zipp<3.16.0"

# LAYER 3: PyTorch CPU-only (LARGE, stable)
RUN pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

# LAYER 4: AI/ML libs (medium, stable)
RUN pip install transformers==4.30.2 decord av ...

# LAYER 5: Utils (small, may change)
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# LAYER 6: Permissions (always last)
RUN mkdir -p /tmp/.ivy /opt/spark/work /app/processing && chmod 777 ...

# LAYER 7: Application code (changes frequently - LAST)
COPY spark_processor.py /app/processing/
```

**Tối ưu:** Layers từ stable → volatile để tận dụng Docker cache

**Airflow Dockerfile (`streaming/airflow/Dockerfile.airflow`):**
- System: Chrome + XVFB
- Python deps: Selenium, webdriver-manager
- Copy DAGs và scripts

**Dashboard Dockerfile (`streaming/dashboard/Dockerfile.dashboard`):**
- Base: Python 3.10-slim
- Install: libpq-dev (Postgres client)
- Copy requirements → pip install
- Copy source code

#### 3.3.3. Volume Mounts

**Persistent Volumes (state/):**
- `./state/minio_data` → MinIO storage (~GB)
- `./state/postgres_data` → Postgres data (~MB)
- `./state/airflow_logs` → Airflow execution logs (~MB)
- `./state/spark_checkpoints` → Spark streaming state (~MB)
- `./state/ivy2` → Spark dependencies cache (~MB)
- `./state/chrome_profile` → Chrome cookies/session (~MB)

**Code Volumes:**
- `./processing` → `/app/processing` (Spark)
- `./ingestion` → `/app/ingestion` (Airflow tasks)
- `../train_eval_module` → `/models` (AI models)
- `./airflow/dags` → `/opt/airflow/dags` (Airflow DAGs)
- `./dashboard` → `/app` (Dashboard)

**Network:**
- Name: `tiktok-network` (bridge driver)
- All services trong cùng network → dùng service name để communicate

### 3.4. CONFIGURATIONS & ENVIRONMENT VARIABLES

#### 3.4.1. Environment Variables (.env)

```bash
# AI Model Weights
TEXT_WEIGHT=0.3          # Default 0.3 (30% text, 70% video)
DECISION_THRESHOLD=0.5   # Default 0.5

# Kafka
KAFKA_STARTING_OFFSETS=latest  # latest hoặc earliest

# Spark Checkpoint
SPARK_CHECKPOINT_DIR=/opt/spark/checkpoints/tiktok_multimodal

# Postgres
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=tiktok_safety_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MinIO
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=password123
MINIO_BUCKET_VIDEOS=tiktok-raw-videos
MINIO_BUCKET_AUDIOS=tiktok-raw-audios
MINIO_PUBLIC_ENDPOINT=http://localhost:9000  # External access

# Airflow
AIRFLOW_DB_USER=airflow
AIRFLOW_DB_PASSWORD=airflow
AIRFLOW_DB_NAME=airflow
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_WEBSERVER_SECRET_KEY=my_very_secret_key_123
```

#### 3.4.2. Spark Configurations

**Spark Session:**
```python
SparkSession.builder
    .config("spark.sql.streaming.checkpointLocation", SPARK_CHECKPOINT_DIR)
    .config("spark.executor.memory", "8g")
    .config("spark.python.worker.memory", "2g")
    .config("spark.network.timeout", "600s")
```

**Kafka Consumer:**
```python
spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:29092")
    .option("subscribe", "tiktok_raw_data")
    .option("startingOffsets", "latest")
    .option("maxOffsetsPerTrigger", 5)
```

### 3.5. TỐI ƯU HÓA & BEST PRACTICES

#### 3.5.1. Đã tối ưu

✅ **Docker Layer Caching:**
- Stable layers (system deps, PyTorch) trước
- Volatile layers (source code) cuối
- Giảm build time khi code thay đổi

✅ **Lazy Model Loading:**
- Models chỉ load khi cần (singleton pattern)
- Giảm memory footprint khi idle

✅ **Batch Processing:**
- Micro-batches (5 messages/trigger) để balance latency và throughput
- Persist UDF results để tránh recompute

✅ **UPSERT Strategy:**
- ON CONFLICT DO UPDATE để handle duplicates
- De-dup trong batch trước khi write

✅ **Checkpointing:**
- Spark checkpoint để resume sau restart
- Kafka offsets được track tự động

✅ **Health Checks:**
- Tất cả services có health checks
- Depends_on với conditions (service_healthy, service_completed_successfully)

#### 3.5.2. Có thể cải thiện

⚠️ **Database Indexes:**
- Thiếu indexes cho `processed_at`, `final_decision` → queries chậm hơn

⚠️ **Model Caching:**
- Models load mỗi Spark worker → memory overhead
- Có thể dùng Spark broadcast variables

⚠️ **Error Handling:**
- UDF exceptions được catch nhưng không retry
- Có thể implement exponential backoff

⚠️ **Monitoring:**
- Thiếu metrics (Prometheus/Grafana)
- Logging chưa structured (JSON format)

⚠️ **Scaling:**
- Spark worker cố định (1 worker)
- Có thể scale horizontal bằng docker-compose scale

---

## 📌 TỔNG KẾT

### Train Eval Module:
- **Text:** 3 models (CafeBERT, XLM-RoBERTa, DistilBERT) với class weights 6x boost
- **Video:** VideoMAE (16 frames, 224x224)
- **Audio:** WavLM (16kHz, 10s max)
- **Fusion:** Late fusion với attention mechanism

### Streaming Pipeline:
- **5 Layers:** Ingestion → Kafka → Spark → Database → Dashboard
- **13+ Docker Services:** Zookeeper, Kafka, MinIO, Postgres, Spark (Master/Worker/Processor), Airflow (DB/Init/Webserver/Scheduler), Dashboard, DB Migrator
- **Orchestration:** Airflow DAGs với self-loop
- **Models:** CafeBERT (text), VideoMAE (video), WavLM (audio - placeholder)

### Đường dẫn quan trọng:
- **Models:** `train_eval_module/output/{model_name}/train/best_checkpoint/`
- **Data:** `streaming/data/crawl/tiktok_links_viet.csv`
- **Storage:** MinIO buckets `tiktok-raw-videos`, `tiktok-raw-audios`
- **Database:** Postgres `tiktok_safety_db.processed_results`
- **Checkpoints:** `streaming/state/spark_checkpoints/`

---

**Tài liệu này cung cấp cái nhìn tổng quan chi tiết về toàn bộ hệ thống. Có thể dùng làm tài liệu tham khảo cho development và maintenance.**
