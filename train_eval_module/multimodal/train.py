import sys
import os
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from transformers import Trainer, TrainingArguments, XCLIPProcessor
from multimodal.mm_configs import MULTIMODAL_MODELS, XCLIP_PARAMS, get_clean_model_name
from multimodal.src.dataset import XCLIPDataset
from fusion.src.dataset import load_fusion_data  # Reuse data loading
from multimodal.src.model import XCLIPClassificationModel
from shared_utils.logger import setup_logger, FileLoggingCallback


def train_xclip(model_idx):
    raw_model_name = MULTIMODAL_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)
    PARAMS = XCLIP_PARAMS

    log_folder = os.path.join(current_dir, "logs")
    logger = setup_logger(f"Train_{clean_name}", sub_dir=log_folder)
    output_dir = os.path.join(current_dir, "output", clean_name)

    logger.info(f"--- START X-CLIP TRAINING: {raw_model_name} ---")

    processor = XCLIPProcessor.from_pretrained(raw_model_name)
    model = XCLIPClassificationModel(raw_model_name)

    # X-CLIP cũng cần cặp Text-Video
    train_data = load_fusion_data("train")
    val_data = load_fusion_data("val")

    train_ds = XCLIPDataset(train_data, processor, num_frames=PARAMS["num_frames"])
    val_ds = XCLIPDataset(val_data, processor, num_frames=PARAMS["num_frames"])

    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=PARAMS["epochs"],
        per_device_train_batch_size=PARAMS["batch_size"],
        gradient_accumulation_steps=PARAMS["grad_accum"],
        learning_rate=PARAMS["lr"],
        weight_decay=PARAMS["weight_decay"],
        bf16=PARAMS.get("bf16", False),
        logging_dir=log_folder,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        dataloader_num_workers=PARAMS["num_workers"],
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        callbacks=[FileLoggingCallback(logger)],
    )

    trainer.train()
    trainer.save_model(os.path.join(output_dir, "best_checkpoint"))
    processor.save_pretrained(os.path.join(output_dir, "best_checkpoint"))
    logger.info("✅ X-CLIP training completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    args = parser.parse_args()
    train_xclip(args.model_idx)
