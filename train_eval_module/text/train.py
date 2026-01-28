"""
Text Training Script - Phiên bản chuẩn HuggingFace Trainer.
Dùng AutoModelForSequenceClassification, không custom architecture.
"""

import sys
import os
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from collections import Counter

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir in sys.path:
    sys.path.remove(current_dir)

from transformers import (
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
    AutoModelForSequenceClassification,
    set_seed,
)
from text.text_configs import (
    TEXT_MODELS,
    TEXT_PARAMS,
    TEXT_MODEL_OVERRIDES,
    get_clean_model_name,
)
from text.src.dataset import TextDataset, load_text_data
from text.src.model import get_text_model_and_tokenizer
from shared_utils.logger import setup_logger, FileLoggingCallback


# --------------------------------------------------
# Focal Loss for imbalanced classification
# --------------------------------------------------
class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction="mean"):
        """
        Focal Loss for imbalanced classification.

        Args:
            alpha: Class weights tensor [weight_class_0, weight_class_1]
            gamma: Focusing parameter (default 2.0)
            reduction: 'mean', 'sum', or 'none'
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction="none")
        pt = torch.exp(-ce_loss)  # p_t = probability of correct class

        focal_loss = (1 - pt) ** self.gamma * ce_loss

        if self.alpha is not None:
            if self.alpha.device != inputs.device:
                self.alpha = self.alpha.to(inputs.device)
            alpha_t = self.alpha[targets]
            focal_loss = alpha_t * focal_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


# --------------------------------------------------
# Focal Loss Trainer for highly imbalanced data
# --------------------------------------------------
class FocalLossTrainer(Trainer):
    def __init__(self, alpha=None, gamma=2.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha = torch.tensor(alpha, dtype=torch.float32) if alpha else None
        self.gamma = gamma
        self.focal_loss = FocalLoss(alpha=self.alpha, gamma=self.gamma)

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss = self.focal_loss(logits.view(-1, 2), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


# --------------------------------------------------
# Weighted Cross-Entropy + Label Smoothing Trainer
# --------------------------------------------------
class WeightedSmoothTrainer(Trainer):
    def __init__(self, class_weights=None, label_smoothing=0.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = (
            torch.tensor(class_weights, dtype=torch.float32) if class_weights else None
        )
        self.label_smoothing = label_smoothing

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")

        if self.class_weights is not None and self.class_weights.device != model.device:
            self.class_weights = self.class_weights.to(model.device)

        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = nn.CrossEntropyLoss(
            weight=self.class_weights, label_smoothing=self.label_smoothing
        )
        loss = loss_fct(logits.view(-1, 2), labels.view(-1))

        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)

    acc = accuracy_score(labels, predictions)
    f1_weighted = f1_score(labels, predictions, average="weighted")
    f1_harmful = f1_score(labels, predictions, pos_label=1, average="binary")
    prec_harmful = precision_score(labels, predictions, pos_label=1, zero_division=0)
    rec_harmful = recall_score(labels, predictions, pos_label=1, zero_division=0)

    return {
        "accuracy": acc,
        "f1": f1_weighted,
        "f1_harmful": f1_harmful,
        "precision_harmful": prec_harmful,
        "recall_harmful": rec_harmful,
    }


def train_text(model_idx, metric_type="eval_f1"):
    """
    Train text model with configurable best model selection metric.

    Args:
        model_idx: Index of model in TEXT_MODELS
        metric_type: One of "eval_f1_harmful", "eval_f1", "eval_loss", "loss"
            - eval_f1_harmful: Save best model by highest F1 on harmful class (RECOMMENDED)
            - eval_f1: Save best model by highest weighted F1
            - eval_loss: Save best model by lowest eval loss
            - loss: Save best model by lowest training loss
    """
    raw_model_name = TEXT_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)

    # Merge Params
    PARAMS = TEXT_PARAMS.copy()
    if model_idx in TEXT_MODEL_OVERRIDES:
        PARAMS.update(TEXT_MODEL_OVERRIDES[model_idx])

    # Override metric based on argument
    if metric_type == "eval_loss":
        PARAMS["metric_for_best_model"] = "eval_loss"
        PARAMS["greater_is_better"] = False
    elif metric_type == "loss":
        PARAMS["metric_for_best_model"] = "loss"
        PARAMS["greater_is_better"] = False
    elif metric_type == "eval_f1":
        PARAMS["metric_for_best_model"] = "eval_f1"
        PARAMS["greater_is_better"] = True
    else:  # eval_f1_harmful (default - BEST for imbalanced data)
        PARAMS["metric_for_best_model"] = "eval_f1_harmful"
        PARAMS["greater_is_better"] = True

    # Set seed for reproducibility BEFORE any model initialization
    seed = PARAMS.get("seed", 42)
    set_seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

    # Create separate folder for each metric type to avoid overwriting
    metric_suffix = f"_{metric_type}"
    full_log_dir = os.path.join(
        current_dir, "logs", clean_name, f"train{metric_suffix}"
    )
    full_output_dir = os.path.join(
        current_dir, "output", clean_name, f"train{metric_suffix}"
    )
    logger = setup_logger(f"Train_{clean_name}_{metric_type}", sub_dir=full_log_dir)

    logger.info(f"--- START TEXT TRAINING: {raw_model_name} ---")
    logger.info(f"📊 METRIC TYPE: {metric_type}")
    logger.info("=" * 30)
    logger.info("🛠️  CONFIGURATION (TEXT):")
    logger.info(f"  🎲 SEED: {seed} (fixed for reproducibility)")
    for key, value in PARAMS.items():
        logger.info(f"  - {key}: {value}")
    logger.info("=" * 30)

    logger.info(f"Tensorboard Log Dir: {full_log_dir}")
    logger.info(f"Output Directory: {full_output_dir}")
    logger.info(f"Training Text Model: {raw_model_name}")
    logger.info("-> Using AutoModelForSequenceClassification (Standard HF)")

    # Load model và tokenizer chuẩn HuggingFace
    dropout_rate = PARAMS.get("hidden_dropout_prob", 0.1)
    model, tokenizer = get_text_model_and_tokenizer(
        raw_model_name, dropout_rate=dropout_rate
    )

    # 3. Load Data
    df_train = load_text_data(split="train")
    df_val = load_text_data(split="val")

    if df_train.empty:
        logger.error("No training data found!")
        return

    # 4. Class Weights and Loss Type
    loss_type = PARAMS.get("loss_type", "weighted_ce")  # "weighted_ce" or "focal"
    class_weights = PARAMS.get("class_weights", None)
    focal_gamma = PARAMS.get("focal_gamma", 2.0)
    resolved_class_weights = None

    if isinstance(class_weights, str):
        class_weights_lower = class_weights.lower()
        if class_weights_lower in [
            "balanced",
            "balanced_boost_harmful",
            "balanced_boost_harmful_2x",
            "balanced_boost_harmful_3x",
            "focal",
        ]:
            counts = Counter(df_train["label"].tolist())
            n = len(df_train)
            c0 = max(counts.get(0, 0), 1)
            c1 = max(counts.get(1, 0), 1)
            w0 = n / (2.0 * c0)
            w1 = n / (2.0 * c1)

            # Nếu focal loss, tự động set loss_type
            if class_weights_lower == "focal":
                loss_type = "focal"
                logger.info(
                    f"🎯 Using Focal Loss (gamma={focal_gamma}) with balanced weights: [{w0:.4f}, {w1:.4f}] | counts={dict(counts)}"
                )
            elif class_weights_lower == "balanced_boost_harmful":
                w1 = w1 * 1.2  # Boost harmful class weight by 20%
                logger.info(
                    f"⚖️  Auto class_weights (balanced + 20% boost harmful, from TRAIN): [{w0:.4f}, {w1:.4f}] | counts={dict(counts)}"
                )
            elif class_weights_lower == "balanced_boost_harmful_2x":
                w1 = w1 * 2.0  # Boost harmful class weight by 100% (2x)
                logger.info(
                    f"⚖️  Auto class_weights (balanced + 2x boost harmful, from TRAIN): [{w0:.4f}, {w1:.4f}] | counts={dict(counts)}"
                )
            elif class_weights_lower == "balanced_boost_harmful_3x":
                w1 = w1 * 3.0  # Boost harmful class weight by 200% (3x)
                logger.info(
                    f"⚖️  Auto class_weights (balanced + 3x boost harmful, from TRAIN): [{w0:.4f}, {w1:.4f}] | counts={dict(counts)}"
                )
            else:
                logger.info(
                    f"⚖️  Auto class_weights (balanced, from TRAIN): [{w0:.4f}, {w1:.4f}] | counts={dict(counts)}"
                )

            resolved_class_weights = [w0, w1]
    elif isinstance(class_weights, (list, tuple)):
        resolved_class_weights = [float(class_weights[0]), float(class_weights[1])]
    else:
        resolved_class_weights = None

    # 5. Dataset Init - Đơn giản, không cần max_comments
    train_dataset = TextDataset(df_train, tokenizer, max_len=PARAMS["max_text_len"])
    val_dataset = TextDataset(df_val, tokenizer, max_len=PARAMS["max_text_len"])

    args = TrainingArguments(
        output_dir=full_output_dir,
        logging_dir=full_log_dir,
        num_train_epochs=PARAMS["epochs"],
        per_device_train_batch_size=PARAMS["batch_size"],
        gradient_accumulation_steps=PARAMS["grad_accum"],
        learning_rate=PARAMS["lr"],
        weight_decay=PARAMS["weight_decay"],
        bf16=PARAMS["bf16"],
        logging_steps=PARAMS["logging_steps"],
        eval_strategy=PARAMS["eval_strategy"],
        save_strategy=PARAMS["save_strategy"],
        save_total_limit=PARAMS["save_total_limit"],
        max_grad_norm=PARAMS.get("max_grad_norm", 1.0),
        load_best_model_at_end=PARAMS["load_best_model_at_end"],
        metric_for_best_model=PARAMS["metric_for_best_model"],  # eval_f1
        greater_is_better=PARAMS["greater_is_better"],  # True
        dataloader_num_workers=PARAMS["num_workers"],
        warmup_ratio=PARAMS.get("warmup_ratio", 0.0),
        lr_scheduler_type=PARAMS.get("lr_scheduler_type", "linear"),
        per_device_eval_batch_size=PARAMS.get("per_device_eval_batch_size", 16),
        eval_accumulation_steps=PARAMS.get("eval_accumulation_steps", 1),
        # NOTE: label_smoothing_factor removed - we use WeightedSmoothTrainer's label_smoothing instead
        report_to=["tensorboard"],
    )

    # Select trainer based on loss type
    if loss_type == "focal":
        logger.info(
            f"🎯 Using FocalLossTrainer (Weights={resolved_class_weights}, Gamma={focal_gamma})"
        )
        trainer = FocalLossTrainer(
            alpha=resolved_class_weights,
            gamma=focal_gamma,
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
            callbacks=[
                FileLoggingCallback(logger),
                EarlyStoppingCallback(early_stopping_patience=PARAMS["stop_patience"]),
            ],
        )
    else:
        logger.info(
            f"🔆 Using WeightedSmoothTrainer (Weights={resolved_class_weights}, Smoothing={PARAMS['label_smoothing']})"
        )
        trainer = WeightedSmoothTrainer(
            class_weights=resolved_class_weights,
            label_smoothing=PARAMS["label_smoothing"],
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
            callbacks=[
                FileLoggingCallback(logger),
                EarlyStoppingCallback(early_stopping_patience=PARAMS["stop_patience"]),
            ],
        )

    trainer.train()

    # Save best checkpoint - Dùng AutoModelForSequenceClassification
    save_path = os.path.join(full_output_dir, "best_checkpoint")
    best_ckpt = trainer.state.best_model_checkpoint
    if best_ckpt:
        logger.info(
            f"✅ Found best checkpoint at: {best_ckpt} -> saving to: {save_path}"
        )
        best_model = AutoModelForSequenceClassification.from_pretrained(best_ckpt)
        best_model.save_pretrained(save_path)
        tokenizer.save_pretrained(save_path)
    else:
        logger.info(
            "⚠️ No best_model_checkpoint found, saving current model as fallback"
        )
        trainer.save_model(save_path)
        tokenizer.save_pretrained(save_path)

    logger.info(f"✅ Training Finished. Best checkpoint saved to: {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    parser.add_argument(
        "--metric_type",
        type=str,
        default="eval_f1",
        choices=["eval_f1", "eval_loss", "loss"],
        help="Metric to use for best model selection: eval_f1 (weighted F1), eval_loss, or loss",
    )
    args = parser.parse_args()
    train_text(args.model_idx, metric_type=args.metric_type)
