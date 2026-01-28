import sys
import os
import argparse
import torch
import numpy as np
import json
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir in sys.path:
    sys.path.remove(current_dir)

from transformers import Trainer, TrainingArguments, XCLIPProcessor

# [FIX] Import từ file config đã đổi tên
from multimodal.mm_configs import MULTIMODAL_MODELS, XCLIP_PARAMS, get_clean_model_name
from multimodal.src.dataset import XCLIPDataset, load_multimodal_data
from multimodal.src.model import XCLIPClassificationModel
from shared_utils.logger import setup_logger
from shared_utils.file_utils import find_best_checkpoint


def test_multimodal(model_idx):
    cfg_name = MULTIMODAL_MODELS[model_idx]
    clean_name = get_clean_model_name(cfg_name)
    PARAMS = XCLIP_PARAMS

    # Setup Logger
    log_folder = os.path.join(current_dir, "logs")
    logger = setup_logger(f"Test_{clean_name}", sub_dir=log_folder)

    # 1. Tìm Checkpoint
    output_dir = os.path.join(current_dir, "output", clean_name)
    best_ckpt = find_best_checkpoint(output_dir)

    if not best_ckpt:
        logger.error(f"❌ Không tìm thấy checkpoint tại {output_dir}")
        return

    logger.info(f"🚀 START MULTIMODAL TESTING: {cfg_name}")
    logger.info(f"📂 Loading Checkpoint: {best_ckpt}")

    # 2. Load Processor & Model
    # Processor load từ checkpoint để đảm bảo config đúng (vocab, image size)
    try:
        processor = XCLIPProcessor.from_pretrained(best_ckpt)
    except:
        logger.warning("Không load được processor từ ckpt, load từ base model.")
        processor = XCLIPProcessor.from_pretrained(cfg_name)

    # Init Model Class
    model = XCLIPClassificationModel(cfg_name)

    # Load Weights
    ckpt_file = os.path.join(best_ckpt, "pytorch_model.bin")
    if os.path.exists(ckpt_file):
        state_dict = torch.load(ckpt_file, map_location="cpu")
        model.load_state_dict(state_dict)
        logger.info("✅ Đã load weights thành công.")
    else:
        logger.warning("⚠️ Không thấy file pytorch_model.bin!")

    # 3. Load Data Test
    data_test = load_multimodal_data(split="test")
    if not data_test:
        logger.error("Không có dữ liệu Test!")
        return

    test_dataset = XCLIPDataset(data_test, processor, num_frames=PARAMS["num_frames"])

    # 4. Predict
    args = TrainingArguments(
        output_dir=os.path.join(output_dir, "test_results"),
        per_device_eval_batch_size=PARAMS["batch_size"],
        dataloader_num_workers=PARAMS["num_workers"],
        bf16=PARAMS.get("bf16", False),
    )

    trainer = Trainer(model=model, args=args)

    logger.info("Running Prediction...")
    preds_output = trainer.predict(test_dataset)

    logits = preds_output.predictions
    if isinstance(logits, tuple):
        logits = logits[0]

    y_preds = np.argmax(logits, axis=1)
    y_true = preds_output.label_ids

    # 5. Metrics & Save
    acc = accuracy_score(y_true, y_preds)
    f1 = f1_score(y_true, y_preds, average="weighted")
    report = classification_report(
        y_true, y_preds, target_names=["Not Harmful", "Harmful"], output_dict=True
    )
    cm = confusion_matrix(y_true, y_preds)

    logger.info(f"🎯 X-CLIP Accuracy: {acc:.4f}")
    logger.info(f"⚡ X-CLIP F1-Score: {f1:.4f}")

    result_file = os.path.join(log_folder, f"test_results_{clean_name}.json")
    with open(result_file, "w") as f:
        json.dump(
            {
                "accuracy": acc,
                "f1": f1,
                "confusion_matrix": cm.tolist(),
                "report": report,
            },
            f,
            indent=4,
        )

    logger.info(f"✅ Kết quả đã lưu: {result_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    args = parser.parse_args()
    test_multimodal(args.model_idx)
