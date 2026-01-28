import sys
import os
import argparse
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from transformers import Trainer, TrainingArguments, EarlyStoppingCallback
from audio.audio_configs import AUDIO_MODELS, AUDIO_PARAMS, get_clean_model_name
from audio.src.dataset import AudioDataset, load_audio_data
from audio.src.model import get_audio_model_and_processor
from shared_utils.logger import setup_logger, FileLoggingCallback


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average="weighted")
    return {"accuracy": acc, "f1": f1}


def train_audio(model_idx):
    raw_model_name = AUDIO_MODELS[model_idx]
    clean_name = get_clean_model_name(raw_model_name)
    PARAMS = AUDIO_PARAMS

    full_log_dir = os.path.join(current_dir, "logs", clean_name, "train")
    full_output_dir = os.path.join(current_dir, "output", clean_name, "train")
    logger = setup_logger(f"Train_{clean_name}", sub_dir=full_log_dir)

    logger.info(f"--- START AUDIO TRAINING (Advanced): {raw_model_name} ---")

    # Chuẩn bị Params Dropout để truyền vào model
    dropout_params = {
        "hidden_dropout": PARAMS.get("hidden_dropout", 0.1),
        "attention_dropout": PARAMS.get("attention_dropout", 0.1),
        "feat_proj_dropout": PARAMS.get("feat_proj_dropout", 0.0),
        "layerdrop": PARAMS.get("layerdrop", 0.0),
        "mask_time_prob": PARAMS.get("mask_time_prob", 0.0),
    }

    # Load Model với Dropout
    model, processor = get_audio_model_and_processor(
        raw_model_name, dropout_params=dropout_params
    )

    data_train = load_audio_data(split="train")
    data_val = load_audio_data(split="val")

    if not data_train:
        logger.error("No training data found!")
        return

    train_dataset = AudioDataset(
        data_train, processor, max_duration=PARAMS["max_duration_sec"]
    )
    val_dataset = AudioDataset(
        data_val, processor, max_duration=PARAMS["max_duration_sec"]
    )

    args = TrainingArguments(
        output_dir=full_output_dir,
        logging_dir=full_log_dir,
        num_train_epochs=PARAMS["epochs"],
        per_device_train_batch_size=PARAMS["batch_size"],
        gradient_accumulation_steps=PARAMS["grad_accum"],
        per_device_eval_batch_size=PARAMS.get("per_device_eval_batch_size", 4),
        eval_accumulation_steps=PARAMS.get("eval_accumulation_steps", 1),
        learning_rate=PARAMS["lr"],
        weight_decay=PARAMS["weight_decay"],
        max_grad_norm=PARAMS.get("max_grad_norm", 1.0),
        bf16=PARAMS.get("bf16", False),
        logging_steps=PARAMS["logging_steps"],
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        dataloader_num_workers=PARAMS["num_workers"],
        warmup_ratio=PARAMS.get("warmup_ratio", 0.0),
        remove_unused_columns=False,
    )

    trainer = Trainer(
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

    save_path = os.path.join(full_output_dir, "best_checkpoint")
    trainer.save_model(save_path)
    processor.save_pretrained(save_path)
    logger.info(f"✅ Audio model saved to: {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_idx", type=int, default=0)
    args = parser.parse_args()
    train_audio(args.model_idx)
