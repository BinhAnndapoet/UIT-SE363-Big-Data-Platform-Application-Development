from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf, struct, when, lit
from pyspark.sql.types import StructType, StructField, StringType, FloatType, DoubleType
from pyspark import StorageLevel
import boto3
import os
import tempfile
import torch
import numpy as np
import scipy.io.wavfile as wavfile
import re
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# --- HUGGING FACE IMPORTS ---
from transformers import AutoImageProcessor, VideoMAEForVideoClassification, VideoMAEImageProcessor
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
from decord import VideoReader, cpu
from safetensors.torch import load_file
import torch.nn as nn
from transformers import AutoModel

# --- MLFLOW AUTO-UPDATER ---
try:
    import sys
    import sys
    sys.path.insert(0, '/app/mlflow')  # Mounted volume
    from model_updater import init_model_updater, get_model_updater
    MLFLOW_ENABLED = True
except ImportError as e:
    MLFLOW_ENABLED = False
    print(f"⚠️ MLflow module not found, auto-update disabled. Error: {e}")
    import traceback
    traceback.print_exc()


# --- CẤU HÌNH ---
KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
KAFKA_TOPIC = "tiktok_raw_data"

# Kafka start offset (default: latest để tránh reprocess khi restart)
KAFKA_STARTING_OFFSETS = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

# Spark checkpoint (persist để tránh đọc lại dữ liệu khi restart container)
SPARK_CHECKPOINT_DIR = os.getenv(
    "SPARK_CHECKPOINT_DIR", "/opt/spark/checkpoints/tiktok_multimodal"
)

# Tuning (cho phép test thủ công qua env, không cần sửa code)
# NOTE: USE_FUSION_MODEL giờ là preference, không phải force mode
# Nếu FUSION model không load được, sẽ tự động fallback về LATE_SCORE
USE_FUSION_MODEL = os.getenv("USE_FUSION_MODEL", "true").lower() == "true"  # Mặc định thử fusion trước
FUSION_MODEL_AVAILABLE = False  # Sẽ được set True nếu load thành công
TEXT_WEIGHT = float(os.getenv("TEXT_WEIGHT", "0.3"))
TEXT_WEIGHT = max(0.0, min(1.0, TEXT_WEIGHT))
VIDEO_WEIGHT = 1.0 - TEXT_WEIGHT
DECISION_THRESHOLD = float(os.getenv("DECISION_THRESHOLD", "0.5"))
DECISION_THRESHOLD = max(0.0, min(1.0, DECISION_THRESHOLD))

# NOTE: đọc từ env để đồng bộ với docker-compose/.env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "password123")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tiktok_safety_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

DAG_ID = "2_TIKTOK_STREAMING_PIPELINE"
TASK_NAME = "spark_processor"


# --- FUSION MODEL CLASS (Copy từ train_eval_module/fusion/src/model.py) ---
class LateFusionModel(nn.Module):
    """Late Fusion Model - Multimodal fusion for text + video."""
    
    def __init__(self, config):
        super().__init__()
        text_path = config["text_model_path"]
        video_path = config["video_model_path"]
        
        # 1. Load Backbones
        self.text_backbone = AutoModel.from_pretrained(text_path)
        self.video_backbone = AutoModel.from_pretrained(video_path)
        
        # Freeze all backbones
        for p in self.text_backbone.parameters():
            p.requires_grad = False
        for p in self.video_backbone.parameters():
            p.requires_grad = False
        
        # 2. Fusion Strategy
        self.fusion_type = config.get("fusion_type", "attention")
        text_dim = config["text_feat_dim"]
        video_dim = config["video_feat_dim"]
        fusion_hidden = config["fusion_hidden"]
        
        if self.fusion_type == "attention":
            # Project to same dimension
            self.text_proj = nn.Linear(text_dim, fusion_hidden)
            self.video_proj = nn.Linear(video_dim, fusion_hidden)
            
            # Cross-Attention
            self.cross_attn_t2v = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )
            self.cross_attn_v2t = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )
            
            # Gating mechanism
            self.gate = nn.Sequential(
                nn.Linear(fusion_hidden * 2, fusion_hidden), nn.Sigmoid()
            )
            
            # Classifier
            self.classifier = nn.Sequential(
                nn.Linear(fusion_hidden, fusion_hidden // 2),
                nn.LayerNorm(fusion_hidden // 2),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden // 2, 2),
            )
        else:
            # Simple Concat Fusion
            input_dim = text_dim + video_dim
            self.classifier = nn.Sequential(
                nn.Linear(input_dim, fusion_hidden),
                nn.BatchNorm1d(fusion_hidden),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden, 2),
            )
        
        self.v_weight = config["video_weight"]
        self.t_weight = config["text_weight"]
        self.is_videomae = "videomae" in video_path.lower()
    
    def forward(self, text_input_ids, text_attention_mask, video_pixel_values, labels=None, **kwargs):
        # A. Text Features
        t_outputs = self.text_backbone(input_ids=text_input_ids, attention_mask=text_attention_mask)
        t_feat = t_outputs.last_hidden_state[:, 0, :]  # CLS token
        
        # B. Video Features
        v_outputs = self.video_backbone(video_pixel_values)
        if self.is_videomae:
            v_feat = v_outputs.last_hidden_state.mean(dim=1)
        else:
            v_feat = v_outputs.last_hidden_state[:, 0, :]
        
        # C. Fusion
        if self.fusion_type == "attention":
            t_proj = self.text_proj(t_feat).unsqueeze(1)
            v_proj = self.video_proj(v_feat).unsqueeze(1)
            
            t_attended, _ = self.cross_attn_t2v(t_proj, v_proj, v_proj)
            v_attended, _ = self.cross_attn_v2t(v_proj, t_proj, t_proj)
            
            t_attended = t_attended.squeeze(1)
            v_attended = v_attended.squeeze(1)
            
            t_weighted = t_attended * self.t_weight
            v_weighted = v_attended * self.v_weight
            
            concat_feat = torch.cat([t_weighted, v_weighted], dim=1)
            gate = self.gate(concat_feat)
            combined = gate * t_weighted + (1 - gate) * v_weighted
        else:
            combined = torch.cat((t_feat * self.t_weight, v_feat * self.v_weight), dim=1)
        
        # D. Classification
        logits = self.classifier(combined)
        
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))
            return {"loss": loss, "logits": logits}
        return {"logits": logits}


def log_to_db(message, level="INFO"):
    """Ghi log ra stdout + ghi vào Postgres (bảng system_logs) để Dashboard hiển thị."""
    ts = datetime.utcnow().isoformat(timespec="seconds")
    print(f"[{ts}] [{level}] {message}", flush=True)
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO system_logs (dag_id, task_name, log_level, message) VALUES (%s, %s, %s, %s)",
            (DAG_ID, TASK_NAME, level, message),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # Không làm fail streaming job chỉ vì lỗi ghi log
        print(f"[{ts}] [WARN] log_to_db failed: {e}", flush=True)


# --- HUGGINGFACE HUB MODEL PATHS (Priority over local paths) ---
# Set these env vars to load models directly from HuggingFace Hub
# Example: HF_MODEL_TEXT=your-username/tiktok-text-classifier
HF_MODEL_TEXT = os.getenv("HF_MODEL_TEXT", None)
HF_MODEL_VIDEO = os.getenv("HF_MODEL_VIDEO", None)
HF_MODEL_FUSION = os.getenv("HF_MODEL_FUSION", None)
HF_TOKEN = os.getenv("HF_TOKEN", None)  # For private repos

# --- PATH MODELS (Local fallback if HF env vars not set) ---
# --- PATH MODELS (Local fallback if HF env vars not set) ---
PATH_TEXT_MODEL = HF_MODEL_TEXT or "/models/text/output/uitnlp_CafeBERT/train/best_checkpoint"
PATH_VIDEO_MODEL = HF_MODEL_VIDEO or "/models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint"
PATH_AUDIO_MODEL = "/models/audio/audio_model/checkpoint-2300"
# Fusion Model Path
PATH_FUSION_MODEL = HF_MODEL_FUSION or "/models/fusion/output/fusion_videomae/best_checkpoint"
# Backbone paths cho fusion model (used when loading fusion from local)
PATH_FUSION_TEXT_BACKBONE = "/models/text/output/uitnlp_CafeBERT/train/best_checkpoint"
PATH_FUSION_VIDEO_BACKBONE = "/models/video/output/MCG-NJU_videomae-base-finetuned-kinetics/train/best_checkpoint"

TEXT_LABEL_MAP = {0: "safe", 1: "harmful"}
VIDEO_LABEL_MAP = {0: "safe", 1: "harmful"}

# --- [ĐỒNG BỘ] BLACKLIST KEYWORDS (Dựa trên RISKY_HASHTAGS của Crawler) ---
BLACKLIST_KEYWORDS = [
    # 1. Nhóm Gái xinh / Sexy / 18+
    "gaixinh",
    "gái xinh",
    "nhảy sexy",
    "nhay sexy",
    "khoe body",
    "khoe dáng",
    "bikini",
    "hở bạo",
    "sugar baby",
    "sugarbaby",
    "sgbb",
    "nuôi baby",
    "phòng the",
    "phong the",
    "chuyện người lớn",
    "18+",
    "lộ clip",
    "khoe hàng",
    # 2. Nhóm Bạo lực / Drama / Giang hồ
    "đánh nhau",
    "danh nhau",
    "đánh ghen",
    "danh ghen",
    "bóc phốt",
    "boc phot",
    "drama",
    "showbiz",
    "xăm trổ",
    "giang hồ",
    "biến căng",
    "check var",
    "hỗn chiến",
    "bạo lực học đường",
    "chửi bậy",
    # 3. Nhóm Cờ bạc / Lừa đảo / Tài chính đen
    "tài xỉu",
    "xóc đĩa",
    "xoc dia",
    "nổ hũ",
    "no hu",
    "bắn cá",
    "soi kèo",
    "cho vay",
    "bốc bát họ",
    "kiếm tiền online",
    "lừa đảo",
    "app vay tiền",
    "nhóm kéo",
    "kéo tài xỉu",
    "cá độ",
    "lô đề",
    # 4. Nhóm Tệ nạn / Chất kích thích
    "bay lắc",
    "dân chơi",
    "trà đá vỉa hè",
    "nhậu nhẹt",
    "say rượu",
    "hút thuốc",
    "vape",
    "pod",
    "cần sa",
    "ke",
    "kẹo",
    # 5. Nhóm Tâm linh / Mê tín
    "gọi vong",
    "xem bói",
    "bùa ngải",
    "kumathong",
    "kumanthong",
    "tâm linh",
]

# --- GLOBAL VARS ---
text_tokenizer = None
text_model = None
video_processor = None
video_model = None
audio_extractor = None
audio_model = None
device = "cpu"

# Fusion Model vars
fusion_model = None
fusion_text_tokenizer = None
fusion_video_processor = None


# --- FUSION MODEL CLASS (Copy từ train_eval_module/fusion/src/model.py) ---
class LateFusionModel(nn.Module):
    """Late Fusion Model - Multimodal fusion for text + video."""
    
    def __init__(self, config):
        super().__init__()
        text_path = config["text_model_path"]
        video_path = config["video_model_path"]
        
        # 1. Load Backbones
        self.text_backbone = AutoModel.from_pretrained(text_path)
        self.video_backbone = AutoModel.from_pretrained(video_path)
        
        # Freeze all backbones
        for p in self.text_backbone.parameters():
            p.requires_grad = False
        for p in self.video_backbone.parameters():
            p.requires_grad = False
        
        # 2. Fusion Strategy
        self.fusion_type = config.get("fusion_type", "attention")
        text_dim = config["text_feat_dim"]
        video_dim = config["video_feat_dim"]
        fusion_hidden = config["fusion_hidden"]
        
        if self.fusion_type == "attention":
            # Project to same dimension
            self.text_proj = nn.Linear(text_dim, fusion_hidden)
            self.video_proj = nn.Linear(video_dim, fusion_hidden)
            
            # Cross-Attention
            self.cross_attn_t2v = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )
            self.cross_attn_v2t = nn.MultiheadAttention(
                embed_dim=fusion_hidden, num_heads=4, dropout=0.1, batch_first=True
            )
            
            # Gating mechanism
            self.gate = nn.Sequential(
                nn.Linear(fusion_hidden * 2, fusion_hidden), nn.Sigmoid()
            )
            
            # Classifier
            self.classifier = nn.Sequential(
                nn.Linear(fusion_hidden, fusion_hidden // 2),
                nn.LayerNorm(fusion_hidden // 2),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden // 2, 2),
            )
        else:
            # Simple Concat Fusion
            input_dim = text_dim + video_dim
            self.classifier = nn.Sequential(
                nn.Linear(input_dim, fusion_hidden),
                nn.BatchNorm1d(fusion_hidden),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(fusion_hidden, 2),
            )
        
        self.v_weight = config["video_weight"]
        self.t_weight = config["text_weight"]
        self.is_videomae = "videomae" in video_path.lower()
    
    def forward(self, text_input_ids, text_attention_mask, video_pixel_values, labels=None, **kwargs):
        # A. Text Features
        t_outputs = self.text_backbone(input_ids=text_input_ids, attention_mask=text_attention_mask)
        t_feat = t_outputs.last_hidden_state[:, 0, :]  # CLS token
        
        # B. Video Features
        v_outputs = self.video_backbone(video_pixel_values)
        if self.is_videomae:
            v_feat = v_outputs.last_hidden_state.mean(dim=1)
        else:
            v_feat = v_outputs.last_hidden_state[:, 0, :]
        
        # C. Fusion
        if self.fusion_type == "attention":
            t_proj = self.text_proj(t_feat).unsqueeze(1)
            v_proj = self.video_proj(v_feat).unsqueeze(1)
            
            t_attended, _ = self.cross_attn_t2v(t_proj, v_proj, v_proj)
            v_attended, _ = self.cross_attn_v2t(v_proj, t_proj, t_proj)
            
            t_attended = t_attended.squeeze(1)
            v_attended = v_attended.squeeze(1)
            
            t_weighted = t_attended * self.t_weight
            v_weighted = v_attended * self.v_weight
            
            concat_feat = torch.cat([t_weighted, v_weighted], dim=1)
            gate = self.gate(concat_feat)
            combined = gate * t_weighted + (1 - gate) * v_weighted
        else:
            combined = torch.cat((t_feat * self.t_weight, v_feat * self.v_weight), dim=1)
        
        # D. Classification
        logits = self.classifier(combined)
        
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))
            return {"loss": loss, "logits": logits}
        return {"logits": logits}


# --- LAZY LOADING FUNCTIONS ---
def get_text_model():
    global text_tokenizer, text_model
    if text_model is None:
        print(f"📦 Loading Text Model...")
        text_tokenizer = AutoTokenizer.from_pretrained(PATH_TEXT_MODEL)
        text_model = AutoModelForSequenceClassification.from_pretrained(PATH_TEXT_MODEL)
        text_model.to(device)
        text_model.eval()
    return text_tokenizer, text_model


def get_video_model():
    global video_processor, video_model
    if video_model is None:
        print(f"📦 Loading Video Model...")
        video_processor = AutoImageProcessor.from_pretrained(PATH_VIDEO_MODEL)
        video_model = VideoMAEForVideoClassification.from_pretrained(PATH_VIDEO_MODEL)
        video_model.to(device)
        video_model.eval()
    return video_processor, video_model


def get_audio_model():
    global audio_extractor, audio_model
    if audio_model is None:
        print(f"📦 Loading Audio Model: {PATH_AUDIO_MODEL}")
        audio_extractor = AutoFeatureExtractor.from_pretrained(PATH_AUDIO_MODEL)
        audio_model = AutoModelForAudioClassification.from_pretrained(PATH_AUDIO_MODEL)
        audio_model.to(device)
        audio_model.eval()
    return audio_extractor, audio_model


def get_fusion_model():
    """Load Fusion Model (text + video fusion) - Lazy loading.
    
    Returns:
        tuple: (model, tokenizer, processor) if successful, (None, None, None) if failed
    """
    global fusion_model, fusion_text_tokenizer, fusion_video_processor, FUSION_MODEL_AVAILABLE
    
    if fusion_model is not None:
        return fusion_model, fusion_text_tokenizer, fusion_video_processor
    
    try:
        print(f"🔥 Loading Fusion Model from: {PATH_FUSION_MODEL}")
        
        # 1. Load processors (tokenizer và video processor)
        fusion_text_tokenizer = AutoTokenizer.from_pretrained(PATH_FUSION_TEXT_BACKBONE)
        fusion_video_processor = VideoMAEImageProcessor.from_pretrained(PATH_FUSION_VIDEO_BACKBONE)
        
        # 2. Fusion model config (theo fusion_configs.py)
        fusion_config = {
            "text_model_path": PATH_FUSION_TEXT_BACKBONE,
            "video_model_path": PATH_FUSION_VIDEO_BACKBONE,
            "fusion_type": "attention",  # hoặc "concat"
            "text_feat_dim": 768,
            "video_feat_dim": 768,
            "fusion_hidden": 256,
            "video_weight": 0.5,
            "text_weight": 0.5,
        }
        
        # 3. Initialize model architecture
        fusion_model = LateFusionModel(fusion_config)
        
        # 4. Load weights from checkpoint
        safetensors_path = os.path.join(PATH_FUSION_MODEL, "model.safetensors")
        if os.path.exists(safetensors_path):
            print(f"📥 Loading weights from: {safetensors_path}")
            state_dict = load_file(safetensors_path)
            fusion_model.load_state_dict(state_dict)
        else:
            pytorch_path = os.path.join(PATH_FUSION_MODEL, "pytorch_model.bin")
            if os.path.exists(pytorch_path):
                print(f"📥 Loading weights from: {pytorch_path}")
                state_dict = torch.load(pytorch_path, map_location="cpu")
                fusion_model.load_state_dict(state_dict)
            else:
                raise FileNotFoundError(f"Fusion model weights not found in {PATH_FUSION_MODEL}")
        
        fusion_model.to(device)
        fusion_model.eval()
        FUSION_MODEL_AVAILABLE = True
        print("✅ Fusion Model loaded successfully!")
        return fusion_model, fusion_text_tokenizer, fusion_video_processor
        
    except Exception as e:
        print(f"⚠️ Failed to load Fusion Model: {e}")
        print("⚠️ Will fallback to LATE_SCORE mode using separate text + video models")
        FUSION_MODEL_AVAILABLE = False
        fusion_model = None
        fusion_text_tokenizer = None
        fusion_video_processor = None
        return None, None, None


# --- UDF VIDEO ---
def process_video_logic(video_id, minio_path):
    temp_file = None
    try:
        if not minio_path:
            return {"risk_score": 0.0, "verdict": "NoVideo", "status": "Skip"}

        s3 = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
        )
        parts = minio_path.split("/", 1)

        fd, temp_name = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        temp_file = temp_name
        s3.download_file(parts[0], parts[1], temp_file)

        vr = VideoReader(temp_file, ctx=cpu(0))
        indices = np.linspace(0, len(vr) - 1, 16).astype(int)
        frames = list(vr.get_batch(indices).asnumpy())

        proc, model = get_video_model()
        inputs = proc(frames, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # Lấy score class 1 (Harmful)
            score = probs[0][1].item()
            verdict = "harmful" if score > 0.5 else "safe"

        if os.path.exists(temp_file):
            os.remove(temp_file)
        return {
            "risk_score": float(score),
            "verdict": str(verdict),
            "status": "Success",
        }
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        return {"risk_score": 0.0, "verdict": "Error", "status": str(e)}


# --- UDF TEXT (RULE-BASED + AI) ---
def process_text_logic(text):
    if not text:
        return {"risk_score": 0.0, "verdict": "Unknown"}

    # 1. RULE-BASED CHECK (Bắt dính các từ khóa từ Crawler)
    text_lower = text.lower()
    for kw in BLACKLIST_KEYWORDS:
        if kw in text_lower:
            # Nếu dính từ cấm -> Gán điểm cao ngay (0.85)
            return {"risk_score": 0.85, "verdict": "harmful"}

    # 2. AI MODEL CHECK (Nếu không dính từ cấm thì hỏi AI)
    try:
        tok, model = get_text_model()
        inputs = tok(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        ).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            score = probs[0][1].item()  # Class 1 = Harmful
            verdict = "harmful" if score > 0.5 else "safe"

        return {"risk_score": float(score), "verdict": str(verdict)}
    except Exception as e:
        return {"risk_score": 0.0, "verdict": "Error: " + str(e)}


# --- UDF AUDIO ---
def process_audio_logic(video_id, minio_audio_path):
    # Trả về mặc định để tránh lỗi pipeline, sau này tích hợp model audio sau
    return {"risk_score": 0.0, "verdict": "NoAudio", "status": "Skip"}


# --- UDF FUSION (TEXT + VIDEO FUSION MODEL) ---
def process_fusion_logic(video_id, minio_video_path, text):
    """Process với Fusion Model (text + video cùng lúc)."""
    temp_file = None
    try:
        if not minio_video_path or not text:
            return {"risk_score": 0.0, "verdict": "MissingData", "status": "Skip"}
        
        # 1. Rule-based check cho text (nhanh hơn)
        text_lower = text.lower()
        for kw in BLACKLIST_KEYWORDS:
            if kw in text_lower:
                return {"risk_score": 0.85, "verdict": "harmful", "status": "RuleBased"}
        
        # 2. Load fusion model (lazy)
        model, tokenizer, video_processor = get_fusion_model()
        
        # 3. Download video từ MinIO
        s3 = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
        )
        parts = minio_video_path.split("/", 1)
        fd, temp_name = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        temp_file = temp_name
        s3.download_file(parts[0], parts[1], temp_file)
        
        # 4. Extract video frames
        vr = VideoReader(temp_file, ctx=cpu(0))
        indices = np.linspace(0, len(vr) - 1, 16).astype(int)
        frames = list(vr.get_batch(indices).asnumpy())
        
        # 5. Preprocess video
        v_inputs = video_processor(list(frames), return_tensors="pt")
        video_pixel_values = v_inputs["pixel_values"].to(device)  # (1, C, T, H, W)
        
        # 6. Preprocess text
        t_inputs = tokenizer(
            text, truncation=True, padding="max_length", max_length=512, return_tensors="pt"
        )
        text_input_ids = t_inputs["input_ids"].to(device)  # (1, L)
        text_attention_mask = t_inputs["attention_mask"].to(device)  # (1, L)
        
        # 7. Fusion model inference
        with torch.no_grad():
            outputs = model(
                text_input_ids=text_input_ids,
                text_attention_mask=text_attention_mask,
                video_pixel_values=video_pixel_values,
            )
            logits = outputs["logits"]
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
            # Lấy score class 1 (Harmful)
            score = probs[0][1].item()
            verdict = "harmful" if score > DECISION_THRESHOLD else "safe"
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return {
            "risk_score": float(score),
            "verdict": str(verdict),
            "status": "Success",
        }
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        return {"risk_score": 0.0, "verdict": "Error", "status": str(e)}


# --- REGISTER ---
res_schema = StructType(
    [
        StructField("risk_score", FloatType(), False),
        StructField("verdict", StringType(), False),
        StructField("status", StringType(), False),
    ]
)
text_res_schema = StructType(
    [
        StructField("risk_score", FloatType(), False),
        StructField("verdict", StringType(), False),
    ]
)

process_video_udf = udf(process_video_logic, res_schema)
process_text_udf = udf(process_text_logic, text_res_schema)
process_audio_udf = udf(process_audio_logic, res_schema)
process_fusion_udf = udf(process_fusion_logic, res_schema)  # NEW: Fusion UDF


# --- DB WRITER ---
def write_to_postgres(batch_df, batch_id):
    log_to_db(f"--- PROCESSING BATCH {batch_id} ---", "INFO")

    # NOTE:
    # `processed_results` dùng `video_id` làm PRIMARY KEY. Khi consumer restart hoặc dùng startingOffsets=earliest,
    # Spark sẽ đọc lại message -> dễ bị duplicate video_id.
    # Vì vậy ta UPSERT (ON CONFLICT) để:
    #  - không crash streaming job
    #  - cập nhật `processed_at` để Dashboard thấy engine vẫn đang hoạt động
    cols = [
        "video_id",
        "raw_text",
        "human_label",
        "text_verdict",
        "text_score",
        "video_verdict",
        "video_score",
        "avg_score",
        "threshold",
        "final_decision",
    ]

    # Persist để tránh Spark chạy lại toàn bộ UDF (download video/model inference) nhiều lần
    batch_cached = batch_df.select(*cols).persist(StorageLevel.MEMORY_AND_DISK)
    try:
        # Tổng quan batch (để dễ hiểu đang streaming những gì)
        try:
            total_rows = batch_cached.count()
        except Exception:
            total_rows = None

        try:
            breakdown = (
                batch_cached.groupBy("final_decision")
                .count()
                .toPandas()
                .to_dict("records")
            )
        except Exception:
            breakdown = None

        if total_rows is not None:
            if breakdown is not None:
                log_to_db(
                    f"Batch {batch_id}: rows={total_rows} breakdown={breakdown}",
                    "INFO",
                )
            else:
                log_to_db(f"Batch {batch_id}: rows={total_rows}", "INFO")

        # In sample cả safe/harmful + score để debug nhanh
        batch_cached.select(
            "video_id",
            "final_decision",
            "avg_score",
            "text_verdict",
            "text_score",
            "video_verdict",
            "video_score",
            "raw_text",
        ).show(8, truncate=True)

        collected = batch_cached.collect()

        # Nếu trong 1 micro-batch có duplicate video_id (cùng PK) thì Postgres sẽ báo:
        # "ON CONFLICT DO UPDATE command cannot affect row a second time".
        # Ta de-dup theo video_id, giữ bản ghi cuối cùng.
        rows_by_video_id = {}
        for r in collected:
            rows_by_video_id[r["video_id"]] = tuple(r[c] for c in cols)
        rows = list(rows_by_video_id.values())
    except Exception as e:
        log_to_db(f"❌ Failed collecting batch {batch_id} rows: {e}", "ERROR")
        raise
    finally:
        try:
            batch_cached.unpersist()
        except Exception:
            pass

    if not rows:
        log_to_db(f"ℹ️ Batch {batch_id}: empty (nothing to write)", "INFO")
        return

    upsert_sql = """
        INSERT INTO processed_results
            (video_id, raw_text, human_label, text_verdict, text_score, video_verdict, video_score, avg_score, threshold, final_decision)
        VALUES %s
        ON CONFLICT (video_id) DO UPDATE SET
            raw_text = EXCLUDED.raw_text,
            human_label = EXCLUDED.human_label,
            text_verdict = EXCLUDED.text_verdict,
            text_score = EXCLUDED.text_score,
            video_verdict = EXCLUDED.video_verdict,
            video_score = EXCLUDED.video_score,
            avg_score = EXCLUDED.avg_score,
            threshold = EXCLUDED.threshold,
            final_decision = EXCLUDED.final_decision,
            processed_at = CURRENT_TIMESTAMP
    """

    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        )
        cur = conn.cursor()
        execute_values(cur, upsert_sql, rows, page_size=100)
        conn.commit()
        conn.close()
    except Exception as e:
        log_to_db(f"❌ Batch {batch_id}: upsert failed: {e}", "ERROR")
        raise

    log_to_db(f"✅ Saved Batch {batch_id} | rows={len(rows)}", "INFO")


def main():
    log_to_db("🚀 Spark Streaming Engine starting...", "INFO")
    mode_str = "FUSION" if USE_FUSION_MODEL else "LATE_SCORE"
    log_to_db(
        f"Config: Mode={mode_str}, startingOffsets={KAFKA_STARTING_OFFSETS}, checkpoint={SPARK_CHECKPOINT_DIR}, w_text={TEXT_WEIGHT:.2f}, w_video={VIDEO_WEIGHT:.2f}, thr={DECISION_THRESHOLD:.2f}",
        "INFO",
    )
    spark = (
        SparkSession.builder.appName("TikTokMultiModalAI")
        .config("spark.sql.streaming.checkpointLocation", SPARK_CHECKPOINT_DIR)
        .config("spark.executor.memory", "8g")
        .config("spark.python.worker.memory", "2g")
        .config("spark.network.timeout", "600s")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")  # Chỉ hiện lỗi thực sự

    # --- MLFLOW AUTO-UPDATER INITIALIZATION ---
    if MLFLOW_ENABLED:
        try:
            # Check every 2 minutes for better models in MLflow registry (TESTING MODE)
            # Current baseline F1 scores (will be updated when better models are found)
            updater = init_model_updater(
                tracking_uri="http://mlflow:5000",
                check_interval_minutes=2,  # Check every 2 minutes for testing
                model_paths={
                    "text": PATH_TEXT_MODEL,
                    "video": PATH_VIDEO_MODEL,
                    "fusion": PATH_FUSION_MODEL,
                },
                current_metrics={
                    "text": 0.75,   # Baseline F1 for text model
                    "video": 0.70,  # Baseline F1 for video model
                    "fusion": 0.80, # Baseline F1 for fusion model
                },
            )
            updater.start()
            log_to_db("✅ MLflow auto-updater started (interval: 2 min, metric: F1-score)", "INFO")
        except Exception as e:
            log_to_db(f"⚠️ MLflow auto-updater failed to start: {e}", "WARNING")

    json_schema = StructType(
        [
            StructField("video_id", StringType(), True),
            StructField("minio_video_path", StringType(), True),
            StructField("clean_text", StringType(), True),
            StructField("csv_label", StringType(), True),
            StructField("timestamp", DoubleType(), True),
        ]
    )

    df_kafka = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", KAFKA_STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", 5)
        .load()
    )

    df_parsed = (
        df_kafka.selectExpr("CAST(value AS STRING)")
        .select(from_json(col("value"), json_schema).alias("data"))
        .select("data.*")
    )

    # Chọn mode: Thử FUSION trước, nếu không được thì fallback về LATE_SCORE
    actual_use_fusion = USE_FUSION_MODEL  # Default từ env
    
    if USE_FUSION_MODEL:
        # Thử load FUSION model trước
        log_to_db("🔥 Attempting to load FUSION MODEL...", "INFO")
        model, tokenizer, processor = get_fusion_model()
        if model is None:
            log_to_db("⚠️ FUSION model not available, falling back to LATE_SCORE mode", "WARNING")
            actual_use_fusion = False
        else:
            log_to_db("✅ FUSION model loaded successfully!", "INFO")
    
    if actual_use_fusion:
        # --- MODE: FUSION MODEL (text + video cùng lúc) ---
        log_to_db("🔥 Using FUSION MODEL mode", "INFO")
        df_fusion = df_parsed.withColumn(
            "fusion_ai", process_fusion_udf(col("video_id"), col("minio_video_path"), col("clean_text"))
        )
        
        df_final = df_fusion.select(
            col("video_id"),
            col("clean_text").alias("raw_text"),
            col("csv_label").alias("human_label"),
            col("fusion_ai.verdict").alias("text_verdict"),  # Giữ tên cột để tương thích DB schema
            col("fusion_ai.risk_score").alias("text_score"),  # Giữ tên cột
            lit("fusion").alias("video_verdict"),  # Dummy cho video_verdict
            col("fusion_ai.risk_score").alias("video_score"),  # Dummy cho video_score
            col("fusion_ai.risk_score").alias("avg_score"),  # Fusion score = final score
            lit(DECISION_THRESHOLD).alias("threshold"),
            when(col("fusion_ai.risk_score") >= lit(DECISION_THRESHOLD), "harmful")
            .otherwise("safe")
            .alias("final_decision"),
        )
    else:
        # --- MODE: LATE SCORE (text + video riêng lẻ, tính trung bình có trọng số) ---
        log_to_db("📊 Using LATE_SCORE mode (text + video separate)", "INFO")
        df_analyzed = df_parsed.withColumn(
            "video_ai", process_video_udf(col("video_id"), col("minio_video_path"))
        ).withColumn("text_ai", process_text_udf(col("clean_text")))

        # Tính điểm: Text 30% + Video 70% (hoặc theo TEXT_WEIGHT, VIDEO_WEIGHT)
        df_scored = (
            df_analyzed.withColumn("text_score", col("text_ai.risk_score"))
            .withColumn("video_score", col("video_ai.risk_score"))
            .withColumn(
                "avg_score",
                (col("text_score") * lit(TEXT_WEIGHT))
                + (col("video_score") * lit(VIDEO_WEIGHT)),
            )
        )

        df_final = df_scored.select(
            col("video_id"),
            col("clean_text").alias("raw_text"),
            col("csv_label").alias("human_label"),
            col("text_ai.verdict").alias("text_verdict"),
            col("text_score"),
            col("video_ai.verdict").alias("video_verdict"),
            col("video_score"),
            col("avg_score"),
            lit(DECISION_THRESHOLD).alias("threshold"),
            when(col("avg_score") >= lit(DECISION_THRESHOLD), "harmful")
            .otherwise("safe")
            .alias("final_decision"),
        )

    query = df_final.writeStream.foreachBatch(write_to_postgres).start()
    log_to_db("✅ Spark query started. Waiting for Kafka messages...", "INFO")
    query.awaitTermination()


if __name__ == "__main__":
    main()
