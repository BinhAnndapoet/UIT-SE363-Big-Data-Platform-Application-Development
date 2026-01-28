# VIDEO MODELS
VIDEO_MODELS = {
    0: {
        "name": "MCG-NJU/videomae-base-finetuned-kinetics",
        "description": "VideoMAE Base - Good balance (87M params)",
        "processor_class": "VideoMAEImageProcessor",
        "model_class": "VideoMAEForVideoClassification",
    },
    1: {
        "name": "facebook/timesformer-base-finetuned-k400",
        "description": "TimeSformer - Efficient Space-Time Attention (121M params)",
        "processor_class": "AutoImageProcessor",
        "model_class": "AutoModelForVideoClassification",
    },
    2: {
        "name": "google/vivit-b-16x2-kinetics400",
        "description": "ViViT - High Accuracy but Heavy (Transformer based)",
        "processor_class": "VivitImageProcessor",
        "model_class": "VivitForVideoClassification",
    },
}

VIDEO_PARAMS = {
    "num_frames": 16,
    "image_size": 224,
    "batch_size": 4,
    "grad_accum": 16,
    "lr": 3e-5,
    "weight_decay": 0.01,
    "epochs": 10,
    "seed": 42,
    "bf16": True,
    "num_workers": 4,
    "eval_strategy": "epoch",
    "save_strategy": "epoch",
    "save_total_limit": 2,
    "gradient_checkpointing": False,
    "hidden_dropout_prob": 0.1,
    "attention_probs_dropout_prob": 0.1,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.1,
    "label_smoothing_factor": 0.0,
    "metric_for_best_model": "eval_f1",
    "load_best_model_at_end": True,
}


def get_clean_model_name(raw_name):
    return raw_name.replace("/", "_")
