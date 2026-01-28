from transformers import (
    AutoFeatureExtractor,
    AutoModelForAudioClassification,
    AutoConfig,
)


def get_audio_model_and_processor(model_name, num_labels=2, dropout_params=None):
    print(f"🔊 Initializing Audio Model: {model_name}")

    # 1. Load Config trước để chỉnh sửa params
    config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)

    # 2. Inject Regularization Params (Nếu có)
    if dropout_params:
        print(f"⚙️  Injecting Dropout Params: {dropout_params}")
        # Các tham số chuẩn của WavLM/Wav2Vec2
        config.hidden_dropout = dropout_params.get("hidden_dropout", 0.0)
        config.attention_dropout = dropout_params.get("attention_dropout", 0.0)
        config.feat_proj_dropout = dropout_params.get("feat_proj_dropout", 0.0)
        config.layerdrop = dropout_params.get("layerdrop", 0.0)
        config.mask_time_prob = dropout_params.get("mask_time_prob", 0.0)

    # 3. Load Processor
    processor = AutoFeatureExtractor.from_pretrained(model_name)

    # 4. Load Model với Config đã chỉnh
    model = AutoModelForAudioClassification.from_pretrained(
        model_name, config=config, ignore_mismatched_sizes=True
    )

    return model, processor
