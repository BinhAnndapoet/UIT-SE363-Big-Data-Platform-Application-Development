# 🔥 TÍCH HỢP FUSION MODEL VÀO STREAMING - TÓM TẮT

## ✅ Đã hoàn thành:

### 1. Fix lỗi Docker Compose
- ✅ Xóa warning `version: "3.8"` trong docker-compose.yml
- ✅ Fix container conflict (docker compose down trước khi up)

### 2. Tìm đường dẫn Fusion Model
- ✅ Fusion model path: `/models/fusion/output/fusion_videomae/best_checkpoint`
- ✅ File weights: `model.safetensors` (1.4GB)

### 3. Tích hợp Fusion Model vào spark_processor.py

#### a. Thêm imports và dependencies:
- ✅ `from transformers import VideoMAEImageProcessor`
- ✅ `from safetensors.torch import load_file`
- ✅ `import torch.nn as nn`
- ✅ `from transformers import AutoModel`

#### b. Thêm class LateFusionModel:
- ✅ Copy từ `train_eval_module/fusion/src/model.py`
- ✅ Hỗ trợ attention-based fusion và concat fusion
- ✅ Tích hợp text backbone (XLM-RoBERTa) và video backbone (VideoMAE)

#### c. Thêm hàm get_fusion_model():
- ✅ Lazy loading fusion model
- ✅ Load text tokenizer từ `PATH_FUSION_TEXT_BACKBONE`
- ✅ Load video processor từ `PATH_FUSION_VIDEO_BACKBONE`
- ✅ Load weights từ `PATH_FUSION_MODEL/model.safetensors`

#### d. Thêm UDF process_fusion_logic():
- ✅ Nhận input: `video_id`, `minio_video_path`, `text`
- ✅ Rule-based check cho text (blacklist keywords)
- ✅ Download video từ MinIO
- ✅ Extract 16 frames (uniform sampling)
- ✅ Preprocess text (tokenizer, max_length=512)
- ✅ Preprocess video (VideoMAE processor)
- ✅ Fusion model inference
- ✅ Trả về risk_score, verdict, status

#### e. Cập nhật main():
- ✅ Thêm env var `USE_FUSION_MODEL` (mặc định: `true`)
- ✅ **Mode FUSION**: Dùng fusion model (text + video cùng lúc)
- ✅ **Mode LATE_SCORE**: Dùng late score (text + video riêng lẻ, tính trung bình có trọng số)
- ✅ Giữ nguyên các hàm cũ (không xóa)

#### f. Cập nhật docker-compose.yml:
- ✅ Thêm env var `USE_FUSION_MODEL=${USE_FUSION_MODEL:-true}` vào spark-processor service

## 📋 Cấu trúc code:

### Paths đã cấu hình:
```
PATH_FUSION_MODEL = "/models/fusion/output/fusion_videomae/best_checkpoint"
PATH_FUSION_TEXT_BACKBONE = "/models/text/output/xlm-roberta-base/train/best_checkpoint"
PATH_FUSION_VIDEO_BACKBONE = "/models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint"
```

### Environment Variables:
```bash
USE_FUSION_MODEL=true   # Mặc định dùng fusion model
TEXT_WEIGHT=0.3          # Chỉ dùng khi USE_FUSION_MODEL=false
DECISION_THRESHOLD=0.5
```

### Database Schema (giữ nguyên):
- `processed_results` table với các cột: `text_verdict`, `text_score`, `video_verdict`, `video_score`, `avg_score`, `final_decision`
- Khi dùng fusion mode: `text_verdict` = fusion verdict, `text_score` = fusion score, `video_verdict` = "fusion", `video_score` = fusion score, `avg_score` = fusion score

## 🚀 Cách chạy:

### 1. Với Fusion Model (mặc định):
```bash
cd /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming
conda activate SE363
./start_all.sh
```

### 2. Với Late Score (fallback):
```bash
cd /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming
export USE_FUSION_MODEL=false
conda activate SE363
./start_all.sh
```

## ⚠️ Lưu ý:

1. **Fusion model path phải tồn tại**: `/models/fusion/output/fusion_videomae/best_checkpoint/model.safetensors`
2. **Backbone paths phải tồn tại**: 
   - Text: `/models/text/output/xlm-roberta-base/train/best_checkpoint`
   - Video: `/models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint`
3. **Memory**: Fusion model lớn hơn (~1.4GB weights), cần đảm bảo Spark worker có đủ memory
4. **Performance**: Fusion model chậm hơn late score vì phải xử lý text + video cùng lúc trong 1 forward pass

## 📊 So sánh Mode:

| Feature | FUSION Mode | LATE_SCORE Mode |
|---------|-------------|-----------------|
| **Text Processing** | Fusion model (XLM-RoBERTa backbone) | CafeBERT riêng lẻ |
| **Video Processing** | Fusion model (VideoMAE backbone) | VideoMAE riêng lẻ |
| **Fusion Strategy** | Attention-based cross-modal fusion | Weighted average (text*0.3 + video*0.7) |
| **Performance** | Chậm hơn (1 forward pass cho cả 2) | Nhanh hơn (2 forward pass riêng biệt) |
| **Accuracy** | Tốt hơn (learned fusion) | Kém hơn (heuristic fusion) |

## 🔧 Troubleshooting:

### Nếu gặp lỗi "Fusion model weights not found":
- Kiểm tra đường dẫn `/models/fusion/output/fusion_videomae/best_checkpoint/model.safetensors` có tồn tại không
- Kiểm tra volume mount `../train_eval_module:/models` trong docker-compose.yml

### Nếu gặp lỗi "Out of memory":
- Tăng `SPARK_WORKER_MEMORY` trong docker-compose.yml
- Giảm `maxOffsetsPerTrigger` trong spark_processor.py (từ 5 xuống 2-3)

### Nếu muốn dùng lại late score:
- Set env var: `USE_FUSION_MODEL=false` hoặc không set (mặc định là true)
- Restart spark-processor container

## 📝 Files đã thay đổi:

1. `streaming/processing/spark_processor.py` - Thêm fusion model code
2. `streaming/docker-compose.yml` - Thêm env var `USE_FUSION_MODEL`, xóa version warning

---

**Tất cả code cũ đã được giữ nguyên. Fusion model được tích hợp như một option mới (mặc định enabled).**
