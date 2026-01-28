import sys
import os
import argparse

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)
if current_dir in sys.path:
    sys.path.remove(current_dir)


os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

from regex import P
from transformers import Trainer, TrainingArguments
from video.video_configs import (
    VIDEO_MODELS,
    VIDEO_PARAMS,
    get_clean_model_name,
)
from video.src.dataset import VideoDataset, load_video_data
from video.src.model import get_video_model_and_processor
from shared_utils.logger import setup_logger, FileLoggingCallback


def train_video(model_idx):
    cfg = VIDEO_MODELS[model_idx]
    raw_model_name = cfg["name"]
    PARAMS = VIDEO_PARAMS.copy()

    # Custom Override cho ViViT nếu cần
    if "vivit" in raw_model_name.lower():
        print("⚠️ ViViT detected: Forcing num_frames=32, batch_size=4")
        PARAMS["num_frames"] = 32
        PARAMS["batch_size"] = 4
        PARAMS["grad_accum"] = 16

    clean_name = get_clean_model_name(raw_model_name)

    full_log_dir = os.path.join(current_dir, "logs", clean_name, "train")
    full_output_dir = os.path.join(current_dir, "output", clean_name, "train")

    logger = setup_logger(f"Train_{clean_name}", sub_dir=full_log_dir)

    logger.info(f"--- START VIDEO TRAINING: {raw_model_name} ---")
    logger.info(f"Params: {PARAMS}")
    logger.info(f"Log Dir (Tensorboard): {full_log_dir}")
    logger.info(f"Output Dir (Checkpoints): {full_output_dir}")

    model, processor = get_video_model_and_processor(cfg, PARAMS)

    data_train = load_video_data(split="train")
    data_val = load_video_data(split="val")

    if not data_train:
        logger.error("No training data found!")
        return

    train_dataset = VideoDataset(
        data_train, processor, num_frames=PARAMS["num_frames"], augment=True
    )
    val_dataset = (
        VideoDataset(
            data_val, processor, num_frames=PARAMS["num_frames"], augment=False
        )
        if data_val
        else None
    )

    args = TrainingArguments(
        output_dir=full_output_dir,
        logging_dir=full_log_dir,
        num_train_epochs=PARAMS["epochs"],
        per_device_train_batch_size=PARAMS["batch_size"],
        gradient_accumulation_steps=PARAMS["grad_accum"],
        learning_rate=PARAMS["lr"],
        weight_decay=PARAMS["weight_decay"],
        bf16=PARAMS.get("bf16", False),
        gradient_checkpointing=PARAMS.get("gradient_checkpointing", False),
        lr_scheduler_type=PARAMS.get("lr_scheduler_type", "linear"),
        warmup_ratio=PARAMS.get("warmup_ratio", 0.0),
        label_smoothing_factor=PARAMS.get("label_smoothing_factor", 0.0),
        logging_steps=10,
        eval_strategy=PARAMS.get("eval_strategy", "no"),
        save_strategy=PARAMS.get("save_strategy", "no"),
        save_total_limit=PARAMS.get("save_total_limit", None),
        load_best_model_at_end=PARAMS.get("load_best_model_at_end", False),
        metric_for_best_model=PARAMS.get("metric_for_best_model", "eval_loss"),
        dataloader_num_workers=PARAMS["num_workers"],
        dataloader_pin_memory=PARAMS.get("dataloader_pin_memory", False),
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        callbacks=[FileLoggingCallback(logger)],
    )

    trainer.train()

    final_save_path = os.path.join(full_output_dir, "best_checkpoint")
    trainer.save_model(final_save_path)
    processor.save_pretrained(final_save_path)

    logger.info(f"✅ Training completed. Model saved to: {final_save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_idx", type=int, default=0, help="Index trong VIDEO_MODELS"
    )
    args = parser.parse_args()
    train_video(args.model_idx)
