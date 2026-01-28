import sys
import os
import argparse
import json
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from transformers import (
    Trainer,
    TrainingArguments,
    AutoModelForAudioClassification,
    AutoFeatureExtractor,
)
from audio.audio_configs import AUDIO_MODELS, AUDIO_PARAMS, get_clean_model_name
from audio.src.dataset import AudioDataset, load_audio_data
from shared_utils.logger import setup_logger
from shared_utils.file_utils import find_best_checkpoint


def test_audio(model_idx):
    raw_model_name = AUDIO_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)

    train_output_dir = os.path.join(current_dir, "output", clean_name, "train")
    best_ckpt = find_best_checkpoint(train_output_dir)
    test_log_dir = os.path.join(current_dir, "logs", clean_name, "test")
    logger = setup_logger(f"Test_{clean_name}", sub_dir=test_log_dir)

    if not best_ckpt:
        logger.error(f"Checkpoint not found in {train_output_dir}!")
        return

    logger.info(f"Loading checkpoint: {best_ckpt}")
    processor = AutoFeatureExtractor.from_pretrained(best_ckpt)
    model = AutoModelForAudioClassification.from_pretrained(best_ckpt, num_labels=2)

    data_test = load_audio_data(split="test")
    test_dataset = AudioDataset(
        data_test, processor, max_duration=AUDIO_PARAMS["max_duration_sec"]
    )
    test_output_dir = os.path.join(current_dir, "output", clean_name, "test")

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=test_output_dir,
            per_device_eval_batch_size=AUDIO_PARAMS["per_device_eval_batch_size"],
            eval_accumulation_steps=AUDIO_PARAMS["eval_accumulation_steps"],
            dataloader_num_workers=AUDIO_PARAMS["num_workers"],
        ),
    )

    preds = trainer.predict(test_dataset)
    y_preds = np.argmax(preds.predictions, axis=1)
    y_true = preds.label_ids

    # Metrics
    acc = accuracy_score(y_true, y_preds)
    f1 = f1_score(y_true, y_preds, average="weighted")
    cm = confusion_matrix(y_true, y_preds)
    target_names = ["Not_Harmful (0)", "Harmful (1)"]
    report_dict = classification_report(
        y_true, y_preds, target_names=target_names, output_dict=True
    )

    # Log Pretty
    logger.info("=" * 60)
    logger.info(f"📊 KẾT QUẢ TEST AUDIO ({clean_name})")
    logger.info("-" * 60)
    logger.info(f"🎯 Accuracy: {acc:.4f}")
    logger.info(f"⚡ F1-Score: {f1:.4f}")
    logger.info("-" * 60)
    logger.info("🧩 CONFUSION MATRIX:")
    logger.info(f"{'':>20} [Pred: Not_Harmful (0)]      [Pred: Harmful (1)]")
    logger.info(f"[Actual: Not_Harmful (0)] {cm[0][0]:>10} {cm[0][1]:>15}")
    if len(cm) > 1:
        logger.info(f"[Actual: Harmful (1)] {cm[1][0]:>10} {cm[1][1]:>15}")
    logger.info("-" * 60)
    logger.info("📋 CLASSIFICATION REPORT:")
    logger.info(
        f"{'Class':<20} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Support':<10}"
    )
    for label in target_names:
        metrics = report_dict[label]
        logger.info(
            f"{label:<20} {metrics['precision']:.4f}     {metrics['recall']:.4f}     {metrics['f1-score']:.4f}     {metrics['support']:.0f}"
        )
    logger.info("=" * 60)

    with open(os.path.join(test_log_dir, f"test_result_{clean_name}.json"), "w") as f:
        json.dump(report_dict, f, indent=4)
    logger.info(f"✅ Kết quả Test đã lưu tại: {test_log_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    args = parser.parse_args()
    test_audio(args.model_idx)
