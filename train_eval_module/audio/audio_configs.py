AUDIO_MODELS = {
    0: "microsoft/wavlm-base",
    1: "microsoft/wavlm-base-plus",
    2: "facebook/wav2vec2-base",
}

AUDIO_PARAMS = {
    "sampling_rate": 16000,
    "max_duration_sec": 10.0,
    "batch_size": 4,
    "grad_accum": 8,  # Effective Batch = 32
    "per_device_eval_batch_size": 8,
    "eval_accumulation_steps": 2,
    "lr": 1e-5,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "epochs": 15,
    "seed": 42,
    "bf16": True,
    "num_workers": 0,
    # [TẮT HẾT DROPOUT] Để model học đặc trưng gốc (giải quyết Underfitting)
    "hidden_dropout": 0.0,
    "attention_dropout": 0.0,
    "feat_proj_dropout": 0.0,
    "mask_time_prob": 0.0,
    "layerdrop": 0.0,
    "save_total_limit": 2,
    "logging_steps": 10,
    "eval_strategy": "epoch",
    "save_strategy": "epoch",
    "stop_patience": 5,
    "metric_for_best_model": "accuracy",
    # Warmup nhẹ để ổn định
    "warmup_ratio": 0.1,
}


def get_clean_model_name(raw_name):
    return raw_name.replace("/", "_")
