import sys
import os
import argparse
import torch
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from transformers import (
    AutoModelForVideoClassification,
    VideoMAEForVideoClassification,
    VivitForVideoClassification,
)

from transformers import Trainer, TrainingArguments
from video.video_configs import VIDEO_MODELS, VIDEO_PARAMS, get_clean_model_name
from video.src.dataset import VideoDataset, load_video_data
from video.src.model import get_video_model_and_processor
from shared_utils.logger import setup_logger
from shared_utils.file_utils import find_best_checkpoint


def test_video(model_idx):
    cfg = VIDEO_MODELS[model_idx]
    raw_model_name = cfg["name"]
    clean_name = get_clean_model_name(raw_model_name)

    train_output_dir = os.path.join(current_dir, "output", clean_name, "train")
    best_ckpt = find_best_checkpoint(train_output_dir)

    test_log_dir = os.path.join(current_dir, "logs", clean_name, "test")
    logger = setup_logger(f"Test_{clean_name}", sub_dir=test_log_dir)

    if not best_ckpt:
        logger.error(f"❌ Không tìm thấy checkpoint tại {train_output_dir}")
        return

    logger.info(f"--- START EVALUATION: {raw_model_name} ---")
    logger.info(f"Loading checkpoint: {best_ckpt}")
    logger.info(f"Saving test logs to: {test_log_dir}")

    PARAMS = VIDEO_PARAMS.copy()
    if "vivit" in raw_model_name.lower():
        PARAMS["num_frames"] = 32

    _, processor = get_video_model_and_processor(cfg, PARAMS)

    model_cls = AutoModelForVideoClassification
    if cfg["model_class"] == "VideoMAEForVideoClassification":
        model_cls = VideoMAEForVideoClassification
    elif cfg["model_class"] == "VivitForVideoClassification":
        model_cls = VivitForVideoClassification

    model = model_cls.from_pretrained(best_ckpt)

    data_test = load_video_data(split="test")
    if not data_test:
        logger.error("No test data found")
        return

    test_dataset = VideoDataset(
        data_test, processor, num_frames=PARAMS["num_frames"], augment=False
    )

    test_output_dir = os.path.join(current_dir, "output", clean_name, "test")

    training_args = TrainingArguments(
        output_dir=os.path.join(test_output_dir, "test_results"),
        per_device_eval_batch_size=PARAMS["batch_size"],
        dataloader_num_workers=PARAMS["num_workers"],
        bf16=PARAMS.get("bf16", False),
    )

    trainer = Trainer(model=model, args=training_args)

    logger.info("Running prediction on Test set...")
    preds_output = trainer.predict(test_dataset)

    logits = preds_output.predictions
    y_preds = np.argmax(logits, axis=1)
    y_true = preds_output.label_ids

    acc = accuracy_score(y_true, y_preds)
    f1 = f1_score(y_true, y_preds, average="weighted")

    logger.info(f"🎯 Accuracy: {acc:.4f}")
    logger.info(f"⚡ F1-Score: {f1:.4f}")

    report = classification_report(
        y_true, y_preds, target_names=["Not Harmful", "Harmful"], output_dict=True
    )
    cm = confusion_matrix(y_true, y_preds)

    result_file = os.path.join(test_log_dir, f"test_results_{clean_name}.json")
    with open(result_file, "w") as f:
        json.dump(
            {
                "accuracy": acc,
                "f1": f1,
                "report": report,
                "confusion_matrix": cm.tolist(),
            },
            f,
            indent=4,
        )

    logger.info(f"✅ Kết quả test đã lưu tại: {result_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    args = parser.parse_args()
    test_video(args.model_idx)
