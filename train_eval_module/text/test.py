"""
Text Test Script - Phiên bản chuẩn HuggingFace.
"""

import torch
import sys
import os
import argparse
import json
import numpy as np

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from transformers import (
    Trainer,
    TrainingArguments,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from text.text_configs import TEXT_MODELS, TEXT_PARAMS, get_clean_model_name
from text.src.dataset import TextDataset, load_text_data
from shared_utils.logger import setup_logger
from shared_utils.file_utils import find_best_checkpoint

LABEL_MAP = {
    0: "Safe",
    1: "Harmful",
}


def test_text(model_idx, metric_type="eval_f1"):
    """
    Test text model trained with specific metric type.

    Args:
        model_idx: Index of model in TEXT_MODELS
        metric_type: One of "eval_f1_harmful", "eval_f1", "eval_loss", "loss" - must match training
    """
    raw_model_name = TEXT_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)

    # Use same folder structure as train
    metric_suffix = f"_{metric_type}"
    train_output_dir = os.path.join(
        current_dir, "output", clean_name, f"train{metric_suffix}"
    )
    best_ckpt = find_best_checkpoint(train_output_dir)

    test_log_dir = os.path.join(current_dir, "logs", clean_name, f"test{metric_suffix}")
    logger = setup_logger(f"Test_{clean_name}_{metric_type}", sub_dir=test_log_dir)

    logger.info(f"--- START EVALUATION (TEST SET ONLY): {raw_model_name} ---")
    logger.info(f"📊 METRIC TYPE: {metric_type}")
    logger.info(f"Log saved to: {test_log_dir}")

    if not best_ckpt:
        logger.error(f"Checkpoint not found in {train_output_dir}!")
        return

    logger.info(f"✅ Found 'best_checkpoint' folder.")
    logger.info(f"Loading checkpoint: {best_ckpt}")

    # Load chuẩn HuggingFace
    tokenizer = AutoTokenizer.from_pretrained(best_ckpt, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(best_ckpt)

    df_test = load_text_data(split="test")
    if df_test.empty:
        logger.error("No test data found!")
        return

    logger.info("🏷️ LABEL DEFINITION:")
    for k, v in LABEL_MAP.items():
        logger.info(f"  - {k} = {v}")

    test_dataset = TextDataset(df_test, tokenizer, max_len=TEXT_PARAMS["max_text_len"])

    test_output_dir = os.path.join(current_dir, "output", clean_name, "test")

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=test_output_dir, per_device_eval_batch_size=16
        ),
        # Không cần data_collator, dùng default
    )

    preds = trainer.predict(test_dataset)
    logits = preds.predictions
    y_true = preds.label_ids

    # ---- use probability threshold ----
    thr_path = os.path.join(
        current_dir, "output", clean_name, "train", "best_threshold.json"
    )
    if os.path.exists(thr_path):
        try:
            with open(thr_path, "r") as f:
                thr_info = json.load(f)
            if "best_threshold" in thr_info and isinstance(
                thr_info["best_threshold"], dict
            ):
                threshold = float(
                    thr_info["best_threshold"].get(
                        "threshold", thr_info["best_threshold"].get("thresh", 0.30)
                    )
                )
            else:
                threshold = float(
                    thr_info.get("threshold", thr_info.get("best_threshold", 0.30))
                )
        except Exception:
            threshold = float(TEXT_PARAMS.get("inference_threshold", 0.30))
    else:
        threshold = float(TEXT_PARAMS.get("inference_threshold", 0.30))

    probs = torch.softmax(torch.tensor(logits), dim=1).cpu().numpy()
    prob_harmful = probs[:, 1]
    y_preds = (prob_harmful >= threshold).astype(int)

    acc = accuracy_score(y_true, y_preds)
    f1 = f1_score(y_true, y_preds, average="weighted")

    target_names = [LABEL_MAP[0], LABEL_MAP[1]]

    cm = confusion_matrix(y_true, y_preds)
    report_dict = classification_report(
        y_true, y_preds, target_names=target_names, output_dict=True
    )

    logger.info("============================================================")
    logger.info(f"�� KẾT QUẢ CHI TIẾT (TEST SET - {clean_name})")
    logger.info("------------------------------------------------------------")
    logger.info(f"🎯 Accuracy : {acc:.4f}")
    logger.info(f"⚡ F1-Score : {f1:.4f}")
    logger.info("------------------------------------------------------------")

    if len(target_names) == 2:
        logger.info("🧩 CONFUSION MATRIX:")
        header = (
            f"{'':>25} " f"[Pred: {LABEL_MAP[0]:<12}] " f"[Pred: {LABEL_MAP[1]:<12}]"
        )
        logger.info(header)

        row0 = f"[Actual: {LABEL_MAP[0]}] {cm[0][0]:>15} {cm[0][1]:>15}"
        row1 = f"[Actual: {LABEL_MAP[1]}] {cm[1][0]:>15} {cm[1][1]:>15}"

        logger.info(row0)
        logger.info(row1)
    else:
        logger.info("🧩 CONFUSION MATRIX:")
        logger.info(f"\n{cm}")

    logger.info("------------------------------------------------------------")
    logger.info("📋 CLASSIFICATION REPORT:")
    logger.info(
        f"{'Class':<20} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Support':<10}"
    )

    for label in target_names:
        metrics = report_dict[label]
        logger.info(
            f"{label:<20}\t{metrics['precision']:.4f}\t{metrics['recall']:.4f}\t{metrics['f1-score']:.4f}\t{metrics['support']:.1f}"
        )

    macro = report_dict["macro avg"]
    logger.info(
        f"{'macro avg':<20}\t{macro['precision']:.4f}\t{macro['recall']:.4f}\t{macro['f1-score']:.4f}\t{macro['support']:.1f}"
    )

    weighted = report_dict["weighted avg"]
    logger.info(
        f"{'weighted avg':<20}\t{weighted['precision']:.4f}\t{weighted['recall']:.4f}\t{weighted['f1-score']:.4f}\t{weighted['support']:.1f}"
    )

    logger.info("============================================================")

    json_path = os.path.join(test_log_dir, f"test_result_{clean_name}.json")
    with open(json_path, "w") as f:
        json.dump(report_dict, f, indent=4)

    logger.info(f"✅ Đã lưu báo cáo chi tiết vào: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    parser.add_argument(
        "--metric_type",
        type=str,
        default="eval_f1",
        choices=["eval_f1", "eval_loss", "loss"],
        help="Metric type used during training (determines which checkpoint folder to use)",
    )
    args = parser.parse_args()
    test_text(args.model_idx, metric_type=args.metric_type)
