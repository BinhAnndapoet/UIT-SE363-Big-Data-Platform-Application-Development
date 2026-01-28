# 📊 BÁO CÁO QUY TRÌNH ETL - HARMFUL TIKTOK DETECTION

> **Tác giả**: Auto-generated  
> **Ngày cập nhật**: 2026-01-02  
> **Dự án**: UIT-SE363 - Phát hiện nội dung độc hại trên TikTok

---

## 📑 MỤC LỤC

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Phase 1: Extract - Crawl dữ liệu](#2-phase-1-extract---crawl-dữ-liệu)
3. [Phase 2: Transform - Tiền xử lý và gán nhãn](#3-phase-2-transform---tiền-xử-lý-và-gán-nhãn)
4. [Phase 3: Load - Chia splits và nạp vào model](#4-phase-3-load---chia-splits-và-nạp-vào-model)
5. [Cấu trúc thư mục và file data](#5-cấu-trúc-thư-mục-và-file-data)
6. [Các vấn đề đã gặp và giải pháp](#6-các-vấn-đề-đã-gặp-và-giải-pháp)
7. [Kết luận và khuyến nghị](#7-kết-luận-và-khuyến-nghị)

---

## 1. TỔNG QUAN KIẾN TRÚC

### 1.1 Pipeline tổng thể

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ETL PIPELINE OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐   │
│  │  CRAWL     │───▶│  PREPROCESS  │───▶│   LABELING   │───▶│  COMBINE   │   │
│  │  TikTok    │    │  & Clean     │    │   (LLM AI)   │    │  Files     │   │
│  └────────────┘    └──────────────┘    └──────────────┘    └────────────┘   │
│        │                  │                   │                   │          │
│        │    FOLDER: preprocess/              │                   │          │
│        │    ─────────────────────────────────┼───────────────────┘          │
│        │                                      │                              │
│        ▼                                      ▼                              │
│  ┌────────────┐                        ┌──────────────┐                     │
│  │ data/      │                        │ processed_   │                     │
│  │ data_1/    │                        │ data/text/   │                     │
│  │ data_viet/ │                        │ COMBINED.csv │                     │
│  └────────────┘                        └──────────────┘                     │
│                                               │                              │
│                                               ▼                              │
│                             ┌─────────────────────────────┐                 │
│                             │    SPLIT DATA (80/10/10)    │                 │
│                             │    FOLDER: train_eval_module│                 │
│                             └─────────────────────────────┘                 │
│                                    │         │         │                    │
│                                    ▼         ▼         ▼                    │
│                              ┌────────┐ ┌────────┐ ┌────────┐               │
│                              │ TRAIN  │ │  VAL   │ │  TEST  │               │
│                              │ 80%    │ │  10%   │ │  10%   │               │
│                              └────────┘ └────────┘ └────────┘               │
│                                               │                              │
│                                               ▼                              │
│                             ┌─────────────────────────────┐                 │
│                             │    CLEAN TEXT (runtime)     │                 │
│                             │    + TOKENIZE → MODEL       │                 │
│                             └─────────────────────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Hai folder chính trong pipeline

| Folder | Mục đích | Input | Output |
|--------|----------|-------|--------|
| `preprocess/` | ETL offline (chạy 1 lần) | Videos + Comments từ crawl | `TRAINING_DATA_FINAL_*.csv` |
| `train_eval_module/` | Training & Evaluation | CSV đã gán nhãn | Model checkpoints |

---

## 2. PHASE 1: EXTRACT - CRAWL DỮ LIỆU

### 2.1 Quy trình crawl

**Folder nguồn**: `UIT-SE363-Big-Data-Platform-Application-Development/`

| File | Chức năng |
|------|-----------|
| `find_tiktok_links.py` | Tìm link TikTok theo hashtag |
| `create_sub_samples_tiktok_links.py` | Tạo subset links để crawl |
| `ScrapingVideoTiktok.py` | Download video + comments |
| `crawl_tiktok_links_update_v1.py` | Cập nhật crawl batch |
| `crawl_tiktok_links_update_viet.py` | Crawl riêng data tiếng Việt |

### 2.2 Cấu trúc data sau crawl

```
UIT-SE363.../
├── data/                          # Batch crawl 1
│   ├── videos/
│   │   ├── harmful/               # 435 videos
│   │   │   ├── video_001/
│   │   │   │   ├── 7522809443281669383.mp4
│   │   │   │   └── 7522809443281669383_comments.xlsx
│   │   │   └── ...
│   │   └── not_harmful/           # 524 videos
│   └── crawl/
│       └── tiktok_links.csv       # Links đã crawl
│
├── data_1/                        # Batch crawl 2
│   ├── videos/
│   │   ├── harmful/               # 540 videos
│   │   └── not_harmful/           # 298 videos
│   └── crawl/
│
└── data_viet/                     # Batch crawl 3 (tiếng Việt)
    ├── videos/
    │   ├── harmful/               # 540 videos
    │   └── not_harmful/           # 278 videos
    └── crawl/
```

### 2.3 Thống kê dữ liệu crawl

> **Lưu ý**: Các con số thống kê (Harmful/Not Harmful/Total) phụ thuộc vào thời điểm crawl và số file video hiện có.
> Khi chốt số liệu cho báo cáo cuối, nên lấy theo output thực tế của script split:
> `train_eval_module/scripts/split_data.py` (phần “🚀 Đang quét dữ liệu video…”).

| Source Folder | Harmful | Not Harmful | Total Videos |
|---------------|---------|-------------|--------------|
| `data/` | 435 | 524 | 959 |
| `data_1/` | 540 | 298 | 838 |
| `data_viet/` | 540 | 278 | 818 |
| **TỔNG (có trùng)** | 1,515 | 1,100 | **2,615** |
| **UNIQUE (sau dedupe)** | - | - | **1,950** |

---

## 3. PHASE 2: TRANSFORM - TIỀN XỬ LÝ VÀ GÁN NHÃN

### 3.1 Pipeline xử lý (folder `preprocess/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREPROCESS PIPELINE (STEP BY STEP)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: MERGE COMMENTS                                                  │
│  ─────────────────────                                                   │
│  File: merge_comments_new.py                                             │
│  Input:  data/videos/*_comments.xlsx                                     │
│  Output: output/data.csv                                                 │
│                                                                          │
│  Chức năng:                                                              │
│  - Quét tất cả file *_comments.xlsx trong folder videos/                 │
│  - Gộp tất cả comments vào 1 CSV với columns: video_id, text, path       │
│                                                                          │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐        │
│  │ data.csv      │      │ data_1.csv    │      │ data_viet.csv │        │
│  │ (raw comments)│      │ (raw comments)│      │ (raw comments)│        │
│  └───────────────┘      └───────────────┘      └───────────────┘        │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 2: PREPROCESS & AGGREGATE                                          │
│  ──────────────────────────────                                          │
│  File: preprocess_new.py                                                 │
│  Input:  output/data.csv                                                 │
│  Output: output/preprocessed_data.csv                                    │
│                                                                          │
│  Chức năng:                                                              │
│  - Clean text: lowercase, remove URLs, fix teencode                      │
│  - AGGREGATE: Gộp TẤT CẢ comments của cùng video_id thành 1 row          │
│  - Giới hạn max 50 comments/video (random sample)                        │
│  - Nối các comments bằng " . " separator                                 │
│                                                                          │
│  ⚠️ QUAN TRỌNG: Đây là nơi comments được gộp theo video_id               │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 3: LABELING (AI/LLM)                                               │
│  ─────────────────────────                                               │
│  File: label_comments_new.py                                             │
│  Input:  output/preprocessed_data.csv                                    │
│  Output: output/TRAINING_TEXT_DATA_NEW_data.csv                          │
│                                                                          │
│  Chức năng:                                                              │
│  - Sử dụng LLM local để gán nhãn (pipeline.sh đang gọi label_comments_new.py)│
│    - Model mặc định hiện set trong preprocess/config.py: Qwen/Qwen2.5-7B-Instruct
│  - Nhãn: 0 (Safe/Not Harmful) hoặc 1 (Harmful)                          │
│  - Confidence score kèm theo                                             │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 4: CLEAN & VERIFY                                                  │
│  ──────────────────────                                                  │
│  File: clean_final_dataset.py + check_label_results.py                   │
│  Input:  output/TRAINING_TEXT_DATA_NEW_data.csv                          │
│  Output: output/TRAINING_DATA_FINAL_data.csv                             │
│                                                                          │
│  Chức năng:                                                              │
│  - (Tuỳ config) Loại bỏ các row có confidence thấp (ngưỡng có thể thay đổi)│
│  - Kiểm tra và sửa label không nhất quán                                 │
│  - Lọc text quá ngắn hoặc rỗng                                          │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 5: COMBINE FILES                                                   │
│  ─────────────────────                                                   │
│  File: combine_file.py                                                   │
│  Input:  TRAINING_DATA_FINAL_data.csv                                    │
│          TRAINING_DATA_FINAL_data_1.csv                                  │
│          TRAINING_DATA_FINAL_data_viet.csv                               │
│  Output: processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv       │
│                                                                          │
│  Chức năng:                                                              │
│  - Gộp 3 file từ 3 batch crawl thành 1 file duy nhất                    │
│  - Shuffle random                                                        │
│  - (Theo preprocess_pipeline.sh) bước này được gọi ở **BƯỚC 6: GỘP DỮ LIỆU**
│  - Output path là đường dẫn tương đối khi chạy trong folder preprocess/
│    (mặc định: processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv)
│  - Sau đó cần đảm bảo file COMBINED nằm trong repo chính để training đọc được:
│    UIT-SE363-Big-Data-Platform-Application-Development/processed_data/text/
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Chi tiết các file xử lý

| File | Input | Output | Chức năng chính |
|------|-------|--------|-----------------|
| `merge_comments_new.py` | `*_comments.xlsx` | `data.csv` | Gộp comments từ Excel |
| `preprocess_new.py` | `data.csv` | `preprocessed_data.csv` | Clean + Aggregate theo video_id |
| `label_comments_new.py` | `preprocessed_data.csv` | `TRAINING_TEXT_DATA_NEW_*.csv` | Gán nhãn bằng LLM |
| `clean_final_dataset.py` | `TRAINING_TEXT_DATA_NEW_*.csv` | `TRAINING_DATA_FINAL_*.csv` | Lọc confidence thấp |
| `combine_file.py` | Multiple CSVs | `COMBINED.csv` | Gộp nhiều file |

### 3.3 Cấu trúc dữ liệu sau mỗi step

**Step 1 (Merge) - `data.csv`:**
```csv
video_id,text,path
7522809443281669383,"dream body",not_harmful/video_844/7522809443281669383.mp4
7522809443281669383,"cleaning my fyp",not_harmful/video_844/7522809443281669383.mp4
7516567349839858952,"mình lấy lại được rồi",harmful/video_292/7516567349839858952.mp4
```
→ Mỗi comment là 1 row riêng

**Step 2 (Preprocess) - `preprocessed_data.csv`:**
```csv
video_id,path,text_clean,filename
7522809443281669383,not_harmful/video_844/...,dream body . cleaning my fyp . ...,7522809443281669383.mp4
```
→ Gộp thành 1 row/video với separator " . "

**Step 3 (Label) - `TRAINING_TEXT_DATA_NEW_*.csv`:**
```csv
video_id,path,filename,text,label,confidence
7522809443281669383,not_harmful/...,7522809443281669383.mp4,"dream body . ...",0,0.95
```
→ Thêm label và confidence từ LLM

---

## 4. PHASE 3: LOAD - CHIA SPLITS VÀ NẠP VÀO MODEL

### 4.1 Pipeline trong `train_eval_module/`

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRAIN_EVAL_MODULE PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT: processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv        │
│                                                                          │
│  STEP 1: SPLIT DATA                                                      │
│  ─────────────────                                                       │
│  File: scripts/split_data.py                                             │
│  Config: configs/paths.py (DATA_SOURCES = ["data", "data_1", "data_viet"])│
│                                                                          │
│  Chức năng:                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ 1. Tạo MASTER INDEX từ video files:                              │    │
│  │    - Quét data/, data_1/, data_viet/ tìm tất cả .mp4             │    │
│  │    - De-duplicate theo video_id                                   │    │
│  │    - Stratified split 80/10/10                                    │    │
│  │    → Output: data_splits/train_split.json, val_split.json,        │    │
│  │              test_split.json                                      │    │
│  │                                                                   │    │
│  │ 2. Tạo TEXT SPLITS align với MASTER:                             │    │
│  │    - Đọc TRAINING_TEXT_DATA_FINAL_COMBINED.csv                   │    │
│  │    - Map video_id với MASTER splits                               │    │
│  │    - Re-aggregate text theo video_id (1 row/video)               │    │
│  │    → Output: processed_data/text/train_split.csv, eval_split.csv,│    │
│  │              test_split.csv                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 2: RUNTIME CLEAN TEXT (khi load vào model)                         │
│  ───────────────────────────────────────────────────────────────         │
│  File: text/src/dataset.py → clean_text()                                │
│                                                                          │
│  Chức năng (áp dụng lúc tokenize):                                       │
│  - Unicode normalize (NFKC)                                              │
│  - Replace URLs → [url], @mentions → [user]                              │
│  - Reduce character repetition (quáaaa → quá)                            │
│  - ⭐ Split by " . " hoặc newlines → De-duplicate → Join với " [cmt] "   │
│  - Hard cap 20,000 chars                                                 │
│                                                                          │
│  ⚠️ QUAN TRỌNG: Separator " . " từ preprocessing được convert sang       │
│     "[cmt]" token để model có thể học ranh giới comment                  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 3: TRAINING                                                        │
│  ─────────────────                                                       │
│  File: text/train.py                                                     │
│  Config: text/text_configs.py                                            │
│                                                                          │
│  Models available:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ idx │ Model Name                        │ Best for             │     │
│  ├─────┼───────────────────────────────────┼──────────────────────┤     │
│  │  0  │ uitnlp/CafeBERT                   │ Text 90%+ Tiếng Việt │     │
│  │  1  │ xlm-roberta-base                  │ Multilingual mixed   │     │
│  │  2  │ distilbert-base-multilingual-cased│ Fast, lightweight    │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 File cấu hình quan trọng

**`configs/paths.py`:**
```python
# DATA SOURCES - Phải bao gồm TẤT CẢ folder chứa video
DATA_SOURCES = ["data", "data_1", "data_viet"]  # ⚠️ Thiếu folder sẽ mất data!

# Input cho text splits
TEXT_LABEL_FILE = ".../processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv"

# Output splits
TEXT_TRAIN_CSV = ".../processed_data/text/train_split.csv"
TEXT_VAL_CSV   = ".../processed_data/text/eval_split.csv"
TEXT_TEST_CSV  = ".../processed_data/text/test_split.csv"
```

### 4.3 Thống kê splits cuối cùng

| Split | Videos | Label 0 (Not Harmful) | Label 1 (Harmful) |
|-------|--------|----------------------|-------------------|
| Train | 1,456 | 616 (42.3%) | 840 (57.7%) |
| Val | 185 | 79 (42.7%) | 106 (57.3%) |
| Test | 179 | 79 (44.1%) | 100 (55.9%) |
| **Total** | **1,820** | - | - |

---

## 5. CẤU TRÚC THƯ MỤC VÀ FILE DATA

### 5.1 Tổng quan

```
/home/guest/Projects/SE363/
│
├── preprocess/                              # ETL offline
│   ├── config.py                            # Cấu hình paths
│   ├── preprocess_pipeline.sh               # Script chạy pipeline
│   ├── merge_comments_new.py                # Step 1: Merge
│   ├── preprocess_new.py                    # Step 2: Clean + Aggregate
│   ├── label_comments_new.py                # Step 3: AI Labeling
│   ├── clean_final_dataset.py               # Step 4: Filter
│   ├── combine_file.py                      # Step 5: Combine
│   │
│   └── output/                              # Output của mỗi step
│       ├── data.csv                         # Step 1 output
│       ├── data_1.csv
│       ├── data_viet.csv
│       ├── preprocessed_data.csv            # Step 2 output
│       ├── preprocessed_data_1.csv
│       ├── preprocessed_data_viet.csv
│       ├── TRAINING_TEXT_DATA_NEW_data.csv  # Step 3 output
│       ├── TRAINING_TEXT_DATA_NEW_data_1.csv
│       ├── TRAINING_TEXT_DATA_NEW_data_viet.csv
│       ├── TRAINING_DATA_FINAL_data.csv     # Step 4 output
│       ├── TRAINING_DATA_FINAL_data_1.csv
│       └── TRAINING_DATA_FINAL_data_viet.csv
│
└── UIT-SE363-Big-Data-Platform-Application-Development/
    │
    ├── data/videos/                         # Video files batch 1
    ├── data_1/videos/                       # Video files batch 2
    ├── data_viet/videos/                    # Video files batch 3
    │
    ├── processed_data/text/                 # Data đã xử lý cho training
    │   ├── TRAINING_TEXT_DATA_FINAL_COMBINED.csv  # ⭐ Input cho split
    │   ├── train_split.csv                  # Output train
    │   ├── eval_split.csv                   # Output validation
    │   └── test_split.csv                   # Output test
    │
    └── train_eval_module/
        ├── configs/
        │   └── paths.py                     # ⚠️ DATA_SOURCES config
        │
        ├── scripts/
        │   ├── split_data.py                # Chia train/val/test
        │   └── analyze_text_splits.py       # Tool phân tích data
        │
        ├── data_splits/                     # MASTER index (video-based)
        │   ├── train_split.json
        │   ├── val_split.json
        │   └── test_split.json
        │
        └── text/
            ├── text_configs.py              # Model configs
            ├── train.py                     # Training script
            ├── test.py                      # Test script
            └── src/
                └── dataset.py               # clean_text(), load_text_data()
```

### 5.2 Flow dữ liệu chi tiết

```
VIDEO FILES                          TEXT/COMMENTS
───────────                          ─────────────
data/videos/*.mp4         ──────────▶  *_comments.xlsx
data_1/videos/*.mp4       ──────────▶  *_comments.xlsx  
data_viet/videos/*.mp4    ──────────▶  *_comments.xlsx
        │                                    │
        │                                    ▼
        │                        ┌───────────────────────┐
        │                        │ merge_comments_new.py │
        │                        └───────────────────────┘
        │                                    │
        │                                    ▼
        │                           preprocess/output/
        │                        ├── data.csv
        │                        ├── data_1.csv
        │                        └── data_viet.csv
        │                                    │
        │                                    ▼
        │                        ┌───────────────────────┐
        │                        │  preprocess_new.py    │
        │                        │  (Aggregate by vid_id)│
        │                        └───────────────────────┘
        │                                    │
        │                                    ▼
        │                        ├── preprocessed_data.csv
        │                        ├── preprocessed_data_1.csv
        │                        └── preprocessed_data_viet.csv
        │                                    │
        │                                    ▼
        │                        ┌───────────────────────┐
        │                        │ label_comments_new.py │
        │                        │    (Qwen2.5 LLM)      │
        │                        └───────────────────────┘
        │                                    │
        │                                    ▼
        │                        ├── TRAINING_DATA_FINAL_data.csv
        │                        ├── TRAINING_DATA_FINAL_data_1.csv
        │                        └── TRAINING_DATA_FINAL_data_viet.csv
        │                                    │
        │                                    ▼
        │                        ┌───────────────────────┐
        │                        │    combine_file.py    │
        │                        └───────────────────────┘
        │                                    │
        │                                    ▼
        │                        TRAINING_TEXT_DATA_FINAL_COMBINED.csv
        │                                    │
        │                                    │
        ▼                                    ▼
┌───────────────────────────────────────────────────────────────┐
│                      split_data.py                             │
│  1. Scan video files → MASTER INDEX (dedupe by video_id)       │
│  2. Stratified split 80/10/10                                  │
│  3. Align TEXT CSV to MASTER → TEXT SPLITS                     │
└───────────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
data_splits/*.json              processed_data/text/*_split.csv
(Video/Audio index)             (Text splits for training)
```

---

## 6. CÁC VẤN ĐỀ ĐÃ GẶP VÀ GIẢI PHÁP

### 6.1 Issue #1: DATA_SOURCES thiếu `data_viet`

**Vấn đề:**
```python
# configs/paths.py (CŨ)
DATA_SOURCES = ["data", "data_1"]  # Thiếu data_viet!
```

**Hậu quả:**
- MASTER INDEX chỉ có 1,133 videos (từ data/ và data_1/)
- TEXT CSV có 1,820 videos (bao gồm cả data_viet/)
- **768 videos bị DROP** vì không match với MASTER

**Giải pháp:**
```python
# configs/paths.py (MỚI)
DATA_SOURCES = ["data", "data_1", "data_viet"]
```

**Kết quả sau fix:**
| Metric | Trước | Sau |
|--------|-------|-----|
| MASTER videos | 1,133 | 1,950 |
| Text videos in splits | 1,052 | 1,820 |
| Dropped videos | 768 | 0 |

---

### 6.2 Issue #2: Separator " . " không được xử lý đúng

**Vấn đề:**
- `preprocess_new.py` gộp comments bằng `" . "` separator
- `dataset.py::clean_text()` chỉ split theo `[\r\n]+` (newlines)
- Kết quả: Comments không được tách ra, `[cmt]` token không được thêm

**Code cũ (SAI):**
```python
# dataset.py
lines = re.split(r"[\r\n]+", text)  # Chỉ split theo newlines
```

**Code mới (ĐÚNG):**
```python
# dataset.py  
lines = re.split(r"[\r\n]+|\s+\.\s+", text)  # Split theo newlines HOẶC " . "
```

**Kết quả:**
| Metric | Trước fix | Sau fix |
|--------|-----------|---------|
| Mean comments/video | 1.0 | ~15-20 |
| `[cmt]` tokens added | ❌ No | ✅ Yes |

---

### 6.3 Issue #3: DistilBERT over-regularized config

**Vấn đề:**
- Ban đầu config DistilBERT quá regularized (dropout cao, weight_decay cao)
- Model bị bias, predict 100% Harmful

**Config cũ (SAI):**
```python
TEXT_MODEL_OVERRIDES = {
    2: {
        "epochs": 15,
        "hidden_dropout_prob": 0.3,  # Quá cao!
        "weight_decay": 0.15,        # Quá cao!
    }
}
```

**Config mới (ĐÚNG):**
```python
TEXT_MODEL_OVERRIDES = {
    2: {
        "epochs": 12,
        "warmup_ratio": 0.15,
        "lr": 3e-5,
        # Giữ dropout và weight_decay mặc định (0.1, 0.05)
    }
}
```

---

### 6.4 Issue #4: Video ID precision loss

**Vấn đề:**
- TikTok video_id có 18-19 digits
- Pandas đọc CSV mặc định là float64 → precision loss
- `7522809443281669383` có thể thành `7.52280944e+18`

**Giải pháp:**
```python
df = pd.read_csv(TEXT_LABEL_FILE, dtype=str, low_memory=False)
# Đọc tất cả columns as string để giữ precision
```

---

### 6.5 Tổng hợp các vấn đề

| # | Issue | Root Cause | Fix | Impact |
|---|-------|------------|-----|--------|
| 1 | 768 videos dropped | `DATA_SOURCES` thiếu `data_viet` | Thêm vào config | +73% data |
| 2 | `[cmt]` không hoạt động | `clean_text()` không split " . " | Fix regex pattern | Better tokenization |
| 3 | Model bias | Over-regularization | Reset to defaults | +20% accuracy |
| 4 | video_id mismatch | Float precision loss | Read as string | Proper alignment |

---

## 7. KẾT LUẬN VÀ KHUYẾN NGHỊ

### 7.1 Kết quả training với data đầy đủ

| Model | Accuracy | F1-Score | Notes |
|-------|----------|----------|-------|
| **CafeBERT** | **82.12%** | **81.99%** | Best cho Vietnamese-heavy data |
| **XLM-RoBERTa** | **82.12%** | **81.84%** | Good multilingual support |
| DistilBERT | 74.30% | 73.71% | Lightweight, fast inference |

### 7.2 Có nên crawl thêm dữ liệu?

**✅ CÓ - Crawl thêm sẽ TĂNG kết quả vì:**

1. **Dataset hiện tại còn nhỏ**: 1,820 videos là khá ít cho deep learning
2. **DistilBERT cải thiện đáng kể khi có thêm data**: +12% khi thêm `data_viet`
3. **Class imbalance**: Harmful (57.7%) vs Not Harmful (42.3%) - cần balance hơn

**Khuyến nghị crawl:**
- Thêm ~1,000-2,000 videos nữa
- Ưu tiên class Not Harmful để balance
- Đa dạng hashtags và categories

### 7.3 Cách gộp comments theo video_id có đúng không?

**✅ ĐÚNG - Đây là hướng xử lý TỐT vì:**

1. **Tránh data leakage**: Nếu không gộp, cùng 1 video có thể xuất hiện ở cả train và test
2. **Context đầy đủ hơn**: Model nhìn thấy nhiều comments cùng lúc, hiểu "không khí chung"
3. **Phù hợp multimodal**: Text và Video được align theo video_id
4. **Giảm noise**: De-duplicate comments trùng lặp

**Cải tiến có thể:**
- Sử dụng sliding window cho texts > 512 tokens (hiện có ~57% texts dài hơn)
- Thử nghiệm `max_comments = 30` thay vì 50 để giảm truncation

### 7.4 Pipeline tối ưu đề xuất

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. CRAWL: Mở rộng dataset đến 3,000-5,000 videos                       │
│     - Balance harmful/not_harmful ratio (50/50)                          │
│     - Đa dạng nguồn: hashtags, trending, user reports                   │
│                                                                          │
│  2. PREPROCESS:                                                          │
│     - Giữ nguyên pipeline hiện tại (đã hoạt động tốt)                   │
│     - Cân nhắc giảm max_comments từ 50 → 30                             │
│                                                                          │
│  3. SPLIT:                                                               │
│     - ⚠️ LUÔN kiểm tra DATA_SOURCES có đầy đủ folders                   │
│     - Chạy analyze_text_splits.py sau mỗi lần split                     │
│                                                                          │
│  4. TRAIN:                                                               │
│     - CafeBERT cho data chủ yếu tiếng Việt                              │
│     - XLM-RoBERTa cho data đa ngôn ngữ                                  │
│     - Thử nghiệm sliding window cho long texts                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📎 PHỤ LỤC

### A. Chạy toàn bộ pipeline

```bash
# 1. Chạy preprocess cho từng batch
cd /home/guest/Projects/SE363/preprocess
./preprocess_pipeline.sh  # Chọn mode 1, folder data/data_1/data_viet

# 2. Combine files
python combine_file.py \
  --inputs TRAINING_DATA_FINAL_data.csv TRAINING_DATA_FINAL_data_1.csv TRAINING_DATA_FINAL_data_viet.csv \
    --output processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv

# (Lưu ý) split_data.py trong repo chính sẽ đọc file tại:
# UIT-SE363-Big-Data-Platform-Application-Development/processed_data/text/TRAINING_TEXT_DATA_FINAL_COMBINED.csv
# Vì vậy sau khi combine trong preprocess/, hãy copy/sync file COMBINED sang đúng vị trí trên.

# 3. Split data
cd ../UIT-SE363.../train_eval_module
python scripts/split_data.py

# 4. Analyze splits (kiểm tra)
python scripts/analyze_text_splits.py

# 5. Train models
cd text
python train.py --model_idx 0  # CafeBERT
python train.py --model_idx 1  # XLM-RoBERTa
python train.py --model_idx 2  # DistilBERT

# 6. Test models
python test.py --model_idx 0
python test.py --model_idx 1
python test.py --model_idx 2
```

### B. Checklist khi crawl thêm data

- [ ] Đảm bảo video files nằm trong `harmful/` hoặc `not_harmful/` folder
- [ ] Comments file đặt cùng folder với video: `{video_id}_comments.xlsx`
- [ ] Cập nhật `DATA_SOURCES` trong `configs/paths.py` nếu thêm folder mới
- [ ] Chạy lại toàn bộ pipeline từ merge đến train
- [ ] Verify bằng `analyze_text_splits.py` - kiểm tra không có videos bị drop

### C. Data contract (để tránh lỗi align/split)

- [ ] `video_id` phải đọc/ghi dạng **string** (tránh float scientific notation)
- [ ] CSV phải có tối thiểu: `video_id`, `text`, `label`, và (`filename` hoặc `path`)
- [ ] Nếu file COMBINED là gộp nhiều source (data/data_1/data_viet) thì mọi bước “check tồn tại video” phải xét đủ các source

---

*End of ETL Report*
