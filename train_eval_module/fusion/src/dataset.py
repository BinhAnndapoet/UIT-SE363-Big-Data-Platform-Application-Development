"""
Fusion Dataset - Đơn giản hóa text handling.
Text đã được concat thành 1 string dài với [SEP] separator.
"""
import torch
from torch.utils.data import Dataset
import os
import sys
import numpy as np
import pandas as pd
import json
import re
import unicodedata

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)

from configs.paths import (
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    TEXT_TRAIN_CSV,
    TEXT_VAL_CSV,
    TEXT_TEST_CSV,
    BASE_PROJECT_PATH,
)
from shared_utils.processing import extract_frames


def clean_text(text):
    """Làm sạch text đã được concat."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"http\S+|www\S+|https\S+", " [url] ", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    text = re.sub(r"@\S+", " [user] ", text)
    text = re.sub(r"\b\d{5,}\b", " [num] ", text)
    text = re.sub(r"[\.]{3,}", "..", text)
    text = re.sub(r"[!]{3,}", "!!", text)
    text = re.sub(r"[?]{3,}", "??", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_fusion_data(split="train"):
    # 1. Xác định file nguồn
    if split == "train":
        json_file, csv_file = MASTER_TRAIN_INDEX, TEXT_TRAIN_CSV
    elif split == "val":
        json_file, csv_file = MASTER_VAL_INDEX, TEXT_VAL_CSV
    elif split == "test":
        json_file, csv_file = MASTER_TEST_INDEX, TEXT_TEST_CSV
    else:
        return []

    # 2. Load Video Index
    if not os.path.exists(json_file):
        print(f"❌ [Fusion] Missing Video Index: {json_file}")
        return []
    with open(json_file, "r") as f:
        video_data = json.load(f)

    # 3. Load Text CSV
    if not os.path.exists(csv_file):
        print(f"❌ [Fusion] Missing Text CSV: {csv_file}")
        return []
    df = pd.read_csv(csv_file)

    if "filename" not in df.columns:
        print("❌ CSV thiếu cột 'filename'")
        return []
    
    df["text"] = df["text"].fillna("")
    text_dict = dict(zip(df["filename"], df["text"]))

    # 4. Alignment
    aligned_data = []
    for item in video_data:
        fname = item["filename"]
        if fname in text_dict:
            aligned_data.append(
                {
                    "path": item["path"],
                    "text": str(text_dict[fname]),  # Text đã concat với [SEP]
                    "label": item["label"],
                    "filename": fname,
                }
            )

    print(f"🔗 [Fusion] Split '{split}': Found {len(aligned_data)} aligned samples.")
    return aligned_data


class EnsembleDataset(Dataset):
    """
    Fusion Dataset - Text đã được concat thành string dài.
    Không cần xử lý JSON List nữa.
    """
    def __init__(
        self,
        data_list,
        video_processor,
        text_tokenizer,
        num_frames=16,
        max_len=512,
    ):
        self.data = data_list
        self.video_processor = video_processor
        self.text_tokenizer = text_tokenizer
        self.num_frames = num_frames
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # 1. Xử lý Video
        full_video_path = (
            os.path.join(BASE_PROJECT_PATH, item["path"])
            if not os.path.isabs(item["path"])
            else item["path"]
        )

        frames = extract_frames(full_video_path, self.num_frames)
        if frames is None or len(frames) == 0:
            frames = [np.zeros((224, 224, 3), dtype="uint8")] * self.num_frames

        v_inputs = self.video_processor(list(frames), return_tensors="pt")

        # 2. Xử lý Text - Đơn giản, text đã concat
        raw_text = str(item["text"])
        cleaned_text = clean_text(raw_text)
        
        if not cleaned_text:
            cleaned_text = "[empty]"

        # Tokenize 1 string duy nhất
        t_inputs = self.text_tokenizer(
            cleaned_text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )

        return {
            "video_pixel_values": v_inputs["pixel_values"].squeeze(0),
            "text_input_ids": t_inputs["input_ids"].squeeze(0),  # (L,)
            "text_attention_mask": t_inputs["attention_mask"].squeeze(0),  # (L,)
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }


# Không cần custom collate_fn nữa - default PyTorch collate xử lý được
