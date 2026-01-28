# train_eval_module/text/text_configs.py
# ============================================
# CONFIG TỐI ƯU - KHÔI PHỤC CONFIG CHO KẾT QUẢ F1 0.8x
# max_text_len=128 (tránh overfitting), class_weights boost 6x
# ============================================

TEXT_MODELS = {
    0: "uitnlp/CafeBERT",  # Tốt cho data Tiếng Việt
    1: "xlm-roberta-base",  # Tốt cho data lẫn lộn Anh/Việt/Hàn...
    2: "distilbert-base-multilingual-cased",  # Nhẹ, nhanh, đa ngôn ngữ
}

# Per-model config overrides (merged on top of TEXT_PARAMS)
# max_text_len=128 (optimal, tránh overfitting với data nhỏ)
# batch_size=32, grad_accum=2 -> effective batch = 64
TEXT_MODEL_OVERRIDES = {
    0: {  # CafeBERT - Vietnamese BERT
        "max_text_len": 512,
        "batch_size": 8,
        "grad_accum": 8,
        "epochs": 10,
        "lr": 1.5e-5,
    },
    1: {  # XLM-RoBERTa - Multilingual
        "max_text_len": 512,
        "batch_size": 8,
        "grad_accum": 8,
        "epochs": 10,
        "lr": 1.5e-5,
    },
    2: {  # DistilBERT - Multilingual (lighter)
        "max_text_len": 512,
        "batch_size": 32,
        "grad_accum": 2,
        "epochs": 15,
        "warmup_ratio": 0.15,
        "lr": 3e-5,
    },
}

TEXT_PARAMS = {
    # Default params - CONFIG KHÔI PHỤC CHO F1 0.8x
    "max_text_len": 128,  # Optimal cho data nhỏ, tránh overfitting
    "batch_size": 32,
    "grad_accum": 2,  # Effective batch size = 64
    "per_device_eval_batch_size": 32,
    "eval_accumulation_steps": 2,
    "lr": 1.5e-5,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.15,
    "weight_decay": 0.1,  # Higher regularization
    "max_grad_norm": 1.0,
    "epochs": 10,
    "seed": 42,
    "bf16": True,
    "num_workers": 4,
    "save_total_limit": 2,
    "logging_steps": 50,
    "eval_strategy": "epoch",
    "save_strategy": "epoch",
    "stop_patience": 3,  # Faster early stopping
    # Lưu best model theo eval_f1 (weighted F1 tổng quát)
    "metric_for_best_model": "eval_f1",
    "greater_is_better": True,
    "load_best_model_at_end": True,
    "hidden_dropout_prob": 0.1,  # Higher dropout for regularization
    "attention_probs_dropout_prob": 0.1,
    "inference_threshold": 0.30,
    "label_smoothing": 0.05,  # Slightly higher smoothing
    # Class weights: [0.5808, 3.5942] = harmful boost ~6x (BEST CONFIG)
    # Giúp model tập trung vào harmful class (minority)
    "class_weights": "balanced_boost_harmful_6x",
    "focal_gamma": 2.0,  # Focusing parameter cho Focal Loss (nếu cần)
}


def get_clean_model_name(raw_name):
    return raw_name.replace("/", "_")
