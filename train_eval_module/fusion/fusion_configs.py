import os

# 1. Xác định vị trí hiện tại (train_eval_module hoặc fusion)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Logic: Nếu file này nằm trong folder fusion, ta lùi ra ngoài để lấy root
if os.path.basename(CURRENT_DIR) == "fusion":
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
else:
    PROJECT_ROOT = CURRENT_DIR

# 2. Cấu hình
FUSION_PARAMS = {
    # --- MODEL PATHS (Chuẩn theo cấu trúc folder của bạn) ---
    # Text Model: XLM-RoBERTa (BEST model from text training)
    # Using User's Fine-Tuned Model from HF Hub (1024-dim CafeBERT)
    "text_model_path": "KhoiBui/tiktok-text-safety-classifier",
    
    # Video Model: VideoMAE (Thay vì Timesformer)
    # Using User's Fine-Tuned Model from HF Hub (768-dim)
    "video_model_path": "KhoiBui/tiktok-video-safety-classifier",
    
    # --- HYPERPARAMETERS ---
    "num_frames": 16,  # VideoMAE Base dùng 16 frames
    "max_text_len": 512,  # Match text config
    "batch_size": 8,  # Reduced for fusion (more memory)
    "grad_accum": 4,
    "lr": 2e-5,
    "weight_decay": 0.05,
    "epochs": 10,
    "seed": 42,
    "num_workers": 4,
    # --- CHIẾN THUẬT FUSION ---
    "video_weight": 0.5,  # Equal weights to avoid bias
    "text_weight": 0.5,  # Equal weights to avoid bias
    # Feature Dimension
    "text_feat_dim": 1024,  # User's Text Model is 1024-dim (CafeBERT)
    "video_feat_dim": 768,  # VideoMAE Base is 768-dim
    "fusion_hidden": 256,
    # --- UNFREEZE BACKBONE LAYERS ---
    "unfreeze_text_layers": 2,  # Unfreeze last 2 layers of text backbone
    "unfreeze_video_layers": 2,  # Unfreeze last 2 layers of video backbone
    # --- FUSION STRATEGY ---
    "fusion_type": "attention",  # "concat" or "attention"
    # --- OPTIMIZATION ---
    "metric_for_best_model": "eval_f1",
    "greater_is_better": True,
    "load_best_model_at_end": True,
    "stop_patience": 5,
    "class_weights": "balanced_boost_harmful",  # Will be computed from train data
}

# Debug in ra để kiểm tra
if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Text Path Exists: {os.path.exists(FUSION_PARAMS['text_model_path'])}")
    print(f"Video Path Exists: {os.path.exists(FUSION_PARAMS['video_model_path'])}")
