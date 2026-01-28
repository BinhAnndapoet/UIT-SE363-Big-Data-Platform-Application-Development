import sys
import os
import argparse
import torch
import numpy as np
import json
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    recall_score,
    confusion_matrix,
    classification_report,
)
from transformers import AutoTokenizer, AutoImageProcessor, Trainer, TrainingArguments

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import Modules
from fusion_configs import FUSION_PARAMS
from fusion.src.dataset import load_fusion_data, EnsembleDataset
from fusion.src.model import LateFusionModel
from shared_utils.logger import setup_logger


def test_fusion():
    # 1. Setup Logger & Config
    PARAMS = FUSION_PARAMS
    # Đường dẫn output (nơi chứa best checkpoint sau khi train)
    checkpoint_dir = os.path.join(
        current_dir, "output", "fusion_videomae", "best_checkpoint"
    )
    log_dir = os.path.join(current_dir, "logs", "fusion_videomae")

    logger = setup_logger("Test_Fusion", sub_dir=log_dir)
    logger.info("--- START FUSION EVALUATION (TEST SET ONLY) ---")

    # Check checkpoint
    if not os.path.exists(checkpoint_dir):
        logger.error(f"❌ Không tìm thấy checkpoint tại: {checkpoint_dir}")
        logger.error("Vui lòng chạy train.py trước!")
        return

    # 2. Load Processors (Text Tokenizer & Video Processor)
    logger.info(f"Loading Text Tokenizer from: {PARAMS['text_model_path']}")
    text_tokenizer = AutoTokenizer.from_pretrained(PARAMS["text_model_path"])

    logger.info(f"Loading Video Processor from: {PARAMS['video_model_path']}")
    video_processor = AutoImageProcessor.from_pretrained(PARAMS["video_model_path"])

    # 3. Load Model & Weights
    logger.info("🏗️ Re-initializing Model architecture...")
    model = LateFusionModel(PARAMS)

    # Load State Dict từ best_checkpoint (hỗ trợ cả safetensors và pytorch_model.bin)
    safetensors_path = os.path.join(checkpoint_dir, "model.safetensors")
    pytorch_path = os.path.join(checkpoint_dir, "pytorch_model.bin")

    if os.path.exists(safetensors_path):
        logger.info(f"📥 Loading weights from: {safetensors_path}")
        from safetensors.torch import load_file

        state_dict = load_file(safetensors_path)
        model.load_state_dict(state_dict)
    elif os.path.exists(pytorch_path):
        logger.info(f"📥 Loading weights from: {pytorch_path}")
        state_dict = torch.load(pytorch_path, map_location="cpu")
        model.load_state_dict(state_dict)
    else:
        logger.error(
            "❌ Không tìm thấy file model weights (safetensors hoặc pytorch_model.bin)"
        )
        return

    # Chuyển model sang chế độ eval
    model.eval()

    # 4. Load Test Data
    test_data = load_fusion_data("test")
    if not test_data:
        logger.error("❌ Không tìm thấy dữ liệu Test!")
        return

    test_ds = EnsembleDataset(
        test_data,
        video_processor,
        text_tokenizer,
        num_frames=PARAMS["num_frames"],
        max_len=PARAMS["max_text_len"],
    )

    # 5. Predict bằng Trainer
    predict_args = TrainingArguments(
        output_dir=os.path.join(current_dir, "output", "temp_test"),
        per_device_eval_batch_size=PARAMS["batch_size"],
        dataloader_num_workers=PARAMS["num_workers"],
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=predict_args,
    )

    logger.info("🚀 Running Prediction on Test Set...")
    predict_output = trainer.predict(test_ds)

    # Lấy logits và labels
    logits = predict_output.predictions
    labels = predict_output.label_ids

    # Chuyển logits thành predictions (argmax)
    preds = np.argmax(logits, axis=1)

    # 6. Calculate Metrics
    acc = accuracy_score(labels, preds)
    f1_weighted = f1_score(labels, preds, average="weighted")

    # Các chỉ số lớp Harmful (quan trọng)
    f1_harmful = f1_score(labels, preds, pos_label=1, average="binary")
    recall_harmful = recall_score(labels, preds, pos_label=1, average="binary")

    cm = confusion_matrix(labels, preds)
    tn, fp, fn, tp = cm.ravel()

    # 7. Log Results (Format chuẩn Text/Video cũ)
    logger.info("=" * 60)
    logger.info("📊 KẾT QUẢ CHI TIẾT (TEST SET - FUSION VIDEO+TEXT)")
    logger.info("-" * 60)
    logger.info(f"🎯 Accuracy : {acc:.4f}")
    logger.info(f"⚡ F1-Score : {f1_weighted:.4f}")
    logger.info("-" * 60)

    logger.info("🧩 CONFUSION MATRIX:")
    logger.info("          ")
    logger.info(f"{'':>25} [Pred: Not Harmful ] [Pred: Harmful     ]")
    logger.info(f"[Actual: Not Harmful] {tn:>15} {fp:>15}")
    logger.info(f"[Actual: Harmful]     {fn:>15} {tp:>15}")
    logger.info("-" * 60)

    # Classification Report chi tiết
    report = classification_report(
        labels, preds, target_names=["Not Harmful", "Harmful"]
    )
    logger.info("📋 CLASSIFICATION REPORT:")
    logger.info(f"\n{report}")
    logger.info("=" * 60)

    # 8. Save Results to JSON
    result_file = os.path.join(log_dir, "test_results_fusion.json")
    results = {
        "accuracy": acc,
        "f1_weighted": f1_weighted,
        "f1_harmful": f1_harmful,
        "recall_harmful": recall_harmful,
        "confusion_matrix": cm.tolist(),
        "report": report,
    }

    with open(result_file, "w") as f:
        json.dump(results, f, indent=4)

    logger.info(f"✅ Đã lưu kết quả kiểm tra vào: {result_file}")


if __name__ == "__main__":
    test_fusion()
