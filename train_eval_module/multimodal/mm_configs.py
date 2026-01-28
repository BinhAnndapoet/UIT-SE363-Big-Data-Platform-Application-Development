MULTIMODAL_MODELS = {
    0: "microsoft/xclip-base-patch32",
    1: "microsoft/xclip-large-patch14",
}

XCLIP_PARAMS = {
    "num_frames": 8,  # X-CLIP chuẩn thường dùng 8 hoặc 32 frames
    "image_size": 224,
    "max_text_len": 77,  # CLIP giới hạn text token
    "batch_size": 16,  # X-CLIP base khá nhẹ
    "grad_accum": 2,
    "lr": 2e-5,
    "weight_decay": 0.01,
    "epochs": 10,
    "seed": 42,
    "bf16": True,
    "num_workers": 4,
}


def get_clean_model_name(raw_name):
    return raw_name.replace("/", "_")
