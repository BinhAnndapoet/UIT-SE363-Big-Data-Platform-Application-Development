import torch
from torch.utils.data import Dataset
import os
import json
import numpy as np
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from configs.paths import (
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    LOG_DIR,
    BASE_PROJECT_PATH,
)
from shared_utils.processing import extract_frames, augment_frames

VIDEO_LOG_DIR = os.path.join(LOG_DIR, "video_errors")
os.makedirs(VIDEO_LOG_DIR, exist_ok=True)
ERROR_LOG_FILE = os.path.join(VIDEO_LOG_DIR, "missing_video_files.txt")


def log_error_file(file_path):
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(file_path + "\n")


def load_video_data(split="train"):
    json_file = None
    if split == "train":
        json_file = MASTER_TRAIN_INDEX
    elif split == "val":
        json_file = MASTER_VAL_INDEX
    elif split == "test":
        json_file = MASTER_TEST_INDEX

    if not json_file or not os.path.exists(json_file):
        return []

    print(f"📂 Loading VIDEO {split.upper()} data from: {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   -> Loaded {len(data)} samples.")
    return data


class VideoDataset(Dataset):
    def __init__(self, data_list, processor, num_frames=16, augment=False):
        self.data = data_list
        self.processor = processor
        self.num_frames = num_frames
        self.augment = augment

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        full_video_path = os.path.join(BASE_PROJECT_PATH, item["path"])
        frames = extract_frames(full_video_path, self.num_frames)

        if frames is None:
            log_error_file(item["path"])
            frames = [np.zeros((224, 224, 3), dtype="uint8")] * self.num_frames
        elif self.augment:
            frames = augment_frames(frames)

        inputs = self.processor(list(frames), return_tensors="pt")
        return {
            "pixel_values": inputs["pixel_values"].squeeze(0),
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }
