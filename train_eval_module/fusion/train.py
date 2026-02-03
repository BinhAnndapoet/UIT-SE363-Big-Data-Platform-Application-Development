import sys
import os
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score
from transformers import Trainer, TrainingArguments, EarlyStoppingCallback
from transformers import AutoTokenizer, VideoMAEImageProcessor, AutoImageProcessor

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import Modules
from fusion_configs import FUSION_PARAMS
from src.dataset import load_fusion_data, EnsembleDataset
from src.model import LateFusionModel
from shared_utils.logger import setup_logger, FileLoggingCallback


# --- TRAINER ---
class WeightedSmoothTrainer(Trainer):
    def __init__(self, class_weights=None, label_smoothing=0.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = (
            torch.tensor(class_weights, dtype=torch.float32) if class_weights else None
        )
        self.label_smoothing = label_smoothing

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        # Get device from logits instead of model
        device = logits.device
        if self.class_weights is not None and self.class_weights.device != device:
            self.class_weights = self.class_weights.to(device)

        loss_fct = nn.CrossEntropyLoss(
            weight=self.class_weights, label_smoothing=self.label_smoothing
        )
        loss = loss_fct(logits.view(-1, 2), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1": f1_score(labels, predictions, average="weighted"),
        "f1_harmful": f1_score(labels, predictions, pos_label=1, average="binary"),
        "recall_harmful": recall_score(
            labels, predictions, pos_label=1, average="binary"
        ),
    }


def compute_class_weights(train_data, boost_harmful=1.2):
    """Compute balanced class weights from training data"""
    labels = [item["label"] for item in train_data]
    from collections import Counter

    counts = Counter(labels)
    n_samples = len(labels)
    n_classes = 2
    weights = []
    for cls in range(n_classes):
        w = n_samples / (n_classes * counts[cls])
        if cls == 1:  # Harmful class
            w *= boost_harmful
        weights.append(w)
    return weights, counts


def train_fusion():
    PARAMS = FUSION_PARAMS
    log_dir = os.path.join(current_dir, "logs", "fusion_videomae")
    output_dir = os.path.join(current_dir, "output", "fusion_videomae")
    logger = setup_logger("Train_Fusion", sub_dir=log_dir)

    logger.info(f"🚀 START FUSION TRAINING (VideoMAE + XLM-RoBERTa)")
    logger.info("=" * 60)
    logger.info("🛠️  CONFIGURATION (FUSION):")
    logger.info(f"  - num_frames: {PARAMS['num_frames']}")
    logger.info(f"  - max_text_len: {PARAMS['max_text_len']}")
    logger.info(f"  - batch_size: {PARAMS['batch_size']}")
    logger.info(f"  - grad_accum: {PARAMS.get('grad_accum', 1)}")
    logger.info(f"  - lr: {PARAMS['lr']}")
    logger.info(f"  - weight_decay: {PARAMS['weight_decay']}")
    logger.info(f"  - epochs: {PARAMS['epochs']}")
    logger.info(f"  - seed: {PARAMS['seed']}")
    logger.info(f"  - num_workers: {PARAMS['num_workers']}")
    logger.info(f"  - video_weight: {PARAMS['video_weight']}")
    logger.info(f"  - text_weight: {PARAMS['text_weight']}")
    logger.info(f"  - text_feat_dim: {PARAMS['text_feat_dim']}")
    logger.info(f"  - video_feat_dim: {PARAMS['video_feat_dim']}")
    logger.info(f"  - fusion_hidden: {PARAMS['fusion_hidden']}")
    logger.info(
        f"  - metric_for_best_model: {PARAMS.get('metric_for_best_model', 'eval_f1')}"
    )
    logger.info(f"  - stop_patience: {PARAMS['stop_patience']}")
    logger.info(f"  - class_weights: {PARAMS['class_weights']}")
    logger.info("=" * 60)
    logger.info(f"Video Path: {PARAMS['video_model_path']}")
    logger.info(f"Text Path: {PARAMS['text_model_path']}")

    # 1. Load Processors
    text_tokenizer = AutoTokenizer.from_pretrained(PARAMS["text_model_path"])

    # [QUAN TRỌNG] Tự động chọn Processor phù hợp
    if "videomae" in PARAMS["video_model_path"].lower():
        logger.info("Using VideoMAEImageProcessor...")
        video_processor = VideoMAEImageProcessor.from_pretrained(
            PARAMS["video_model_path"]
        )
    else:
        logger.info("Using AutoImageProcessor...")
        video_processor = AutoImageProcessor.from_pretrained(PARAMS["video_model_path"])

    # 2. Load Model & Data
    model = LateFusionModel(PARAMS)
    train_data = load_fusion_data("train")
    val_data = load_fusion_data("val")

    if not train_data:
        logger.error("❌ No training data found!")
        return

    # Compute class weights
    if PARAMS["class_weights"] == "balanced_boost_harmful":
        class_weights, label_counts = compute_class_weights(
            train_data, boost_harmful=1.2
        )
        logger.info(
            f"⚖️  Auto class_weights (balanced + 20% boost harmful): {class_weights} | counts={dict(label_counts)}"
        )
    elif isinstance(PARAMS["class_weights"], list):
        class_weights = PARAMS["class_weights"]
        logger.info(f"⚖️  Using fixed class_weights: {class_weights}")
    else:
        class_weights = None
        logger.info("⚖️  No class_weights applied")

    train_ds = EnsembleDataset(
        train_data,
        video_processor,
        text_tokenizer,
        num_frames=PARAMS["num_frames"],
        max_len=PARAMS["max_text_len"],
    )
    val_ds = EnsembleDataset(
        val_data,
        video_processor,
        text_tokenizer,
        num_frames=PARAMS["num_frames"],
        max_len=PARAMS["max_text_len"],
    )

    # 3. Training Args
    args = TrainingArguments(
        output_dir=output_dir,
        logging_dir=log_dir,
        num_train_epochs=PARAMS["epochs"],
        per_device_train_batch_size=PARAMS["batch_size"],
        gradient_accumulation_steps=PARAMS.get("grad_accum", 1),
        learning_rate=PARAMS["lr"],
        weight_decay=PARAMS["weight_decay"],
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model=PARAMS.get("metric_for_best_model", "eval_f1"),
        greater_is_better=True,
        dataloader_num_workers=PARAMS["num_workers"],
        remove_unused_columns=False,
        report_to=["tensorboard"],
    )

    trainer = WeightedSmoothTrainer(
        class_weights=class_weights,
        label_smoothing=0.05,
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
        callbacks=[
            FileLoggingCallback(logger),
            EarlyStoppingCallback(early_stopping_patience=PARAMS["stop_patience"]),
        ],
    )

    trainer.train()
    trainer.save_model(os.path.join(output_dir, "best_checkpoint"))
    logger.info("✅ Fusion Training Finished.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow logging (for offline training without MLflow server)",
    )
    args = parser.parse_args()
    
    # Set ENABLE_MLFLOW env var based on --no-mlflow flag
    if args.no_mlflow:
        os.environ["ENABLE_MLFLOW"] = "false"
    
    train_fusion()
