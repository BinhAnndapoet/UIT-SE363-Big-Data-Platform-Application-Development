# python tune_threshold.py --model_idx 0 --min_recall 0.85

# tune_threshold.py
import os
import sys
import json
import argparse
import numpy as np
import torch
from sklearn.metrics import (
    precision_recall_fscore_support,
    f1_score,
    recall_score,
    precision_score,
)
from transformers import (
    Trainer,
    TrainingArguments,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from text.text_configs import TEXT_MODELS, TEXT_PARAMS, get_clean_model_name
from text.src.dataset import load_text_data, TextDataset
from shared_utils.file_utils import find_best_checkpoint
from shared_utils.logger import setup_logger

LABEL_POS = 1  # harmful class index


def evaluate_thresholds(probs, y_true, thresholds):
    results = []
    for t in thresholds:
        y_pred = (probs >= t).astype(int)
        p = precision_score(y_true, y_pred, pos_label=LABEL_POS, zero_division=0)
        r = recall_score(y_true, y_pred, pos_label=LABEL_POS, zero_division=0)
        f1 = f1_score(y_true, y_pred, pos_label=LABEL_POS, zero_division=0)
        results.append(
            {
                "threshold": float(t),
                "precision": float(p),
                "recall": float(r),
                "f1": float(f1),
            }
        )
    return results


def find_best_by_rule(results, min_recall=None):
    # Prefer thresholds with recall >= min_recall then max f1; otherwise just max f1
    candidates = results
    if min_recall is not None:
        cand = [r for r in results if r["recall"] >= min_recall]
        if len(cand) > 0:
            candidates = cand
    # choose highest f1, tie-breaker highest recall, then highest precision
    best = max(candidates, key=lambda x: (x["f1"], x["recall"], x["precision"]))
    return best


def main(model_idx, min_recall=None, coarse=False):
    raw_model_name = TEXT_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)

    train_output_dir = os.path.join(current_dir, "output", clean_name, "train")
    best_ckpt = find_best_checkpoint(train_output_dir)
    if not best_ckpt:
        print(f"[ERR] No best checkpoint found in {train_output_dir}")
        return

    log_dir = os.path.join(current_dir, "logs", clean_name, "tune_threshold")
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logger(f"Tune_{clean_name}", sub_dir=log_dir)
    logger.info(f"--- THRESHOLD TUNING FOR {raw_model_name} ---")
    logger.info(f"Best checkpoint: {best_ckpt}")

    tokenizer = AutoTokenizer.from_pretrained(best_ckpt, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(best_ckpt)

    df_val = load_text_data(split="val")
    if df_val.empty:
        logger.error("No validation data found!")
        return

    val_dataset = TextDataset(df_val, tokenizer, max_len=TEXT_PARAMS["max_text_len"])
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir="/tmp/tune",
            per_device_eval_batch_size=TEXT_PARAMS.get(
                "per_device_eval_batch_size", 16
            ),
        ),
    )

    preds = trainer.predict(val_dataset)
    logits = preds.predictions
    # get prob for harmful (pos class)
    probs = torch.softmax(torch.tensor(logits), dim=1).cpu().numpy()[:, LABEL_POS]
    y_true = preds.label_ids

    # threshold grid
    if coarse:
        thresholds = np.arange(0.05, 0.91, 0.05)
    else:
        # fine grid around typical region
        thresholds = np.concatenate(
            [
                np.arange(0.05, 0.21, 0.01),
                np.arange(0.21, 0.41, 0.02),
                np.arange(0.41, 0.71, 0.05),
            ]
        )
    thresholds = np.unique(np.clip(thresholds, 0.0, 1.0))

    results = evaluate_thresholds(probs, y_true, thresholds)
    best = find_best_by_rule(results, min_recall=min_recall)

    # save all results and best choice
    out = {
        "model": raw_model_name,
        "best_checkpoint": best_ckpt,
        "min_recall_target": min_recall,
        "best_threshold": best,
        "all_results": results,
    }

    out_path = os.path.join(train_output_dir, "best_threshold.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    logger.info(f"Saved tuning result to: {out_path}")
    logger.info(f"Best threshold: {best}")
    print(json.dumps(best, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    parser.add_argument(
        "--min_recall",
        type=float,
        default=None,
        help="minimum recall target for pos class (e.g. 0.85). If set, choose threshold with recall>=min_recall and best f1 among them",
    )
    parser.add_argument("--coarse", action="store_true", help="use coarse grid")
    args = parser.parse_args()
    main(args.model_idx, min_recall=args.min_recall, coarse=args.coarse)
