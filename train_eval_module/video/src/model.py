from transformers import (
    AutoImageProcessor,
    AutoModelForVideoClassification,
    VideoMAEImageProcessor,
    VideoMAEForVideoClassification,
    VivitImageProcessor,
    VivitForVideoClassification,
)


def get_video_model_and_processor(model_config_entry, params):
    """
    Factory function để khởi tạo Processor và Model dựa trên config
    """
    raw_model_name = model_config_entry["name"]
    proc_class = model_config_entry["processor_class"]

    processor = None
    model = None

    print(f"🏗️ Initializing Model: {raw_model_name}")

    if proc_class == "VideoMAEImageProcessor":
        print("-> Using VideoMAE Processor")
        processor = VideoMAEImageProcessor.from_pretrained(raw_model_name)
        model = VideoMAEForVideoClassification.from_pretrained(
            raw_model_name,
            num_labels=2,
            ignore_mismatched_sizes=True,
            hidden_dropout_prob=params.get("hidden_dropout_prob", 0.1),
            attention_probs_dropout_prob=params.get(
                "attention_probs_dropout_prob", 0.1
            ),
        )
    elif proc_class == "VivitImageProcessor":
        print("-> Using ViViT Processor")
        processor = VivitImageProcessor.from_pretrained(raw_model_name)
        model = VivitForVideoClassification.from_pretrained(
            raw_model_name,
            num_labels=2,
            ignore_mismatched_sizes=True,
            hidden_dropout_prob=params.get("hidden_dropout_prob", 0.1),
            attention_probs_dropout_prob=params.get(
                "attention_probs_dropout_prob", 0.1
            ),
        )
    else:
        print("-> Using AutoImageProcessor")
        processor = AutoImageProcessor.from_pretrained(raw_model_name)
        model = AutoModelForVideoClassification.from_pretrained(
            raw_model_name,
            num_labels=2,
            ignore_mismatched_sizes=True,
            hidden_dropout_prob=params.get("hidden_dropout_prob", 0.1),
            attention_probs_dropout_prob=params.get(
                "attention_probs_dropout_prob", 0.1
            ),
        )

    return model, processor
