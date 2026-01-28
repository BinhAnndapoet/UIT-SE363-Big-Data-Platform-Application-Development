import torch
from torch.utils.data import Dataset
import os
import sys
import numpy as np
import pandas as pd
import json

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from configs.paths import (
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    TEXT_LABEL_FILE,
    BASE_PROJECT_PATH,
)
from fusion.src.dataset import load_fusion_data
from shared_utils.processing import extract_frames


# Hàm load data wrapper cho multimodal
def load_multimodal_data(split="train"):
    return load_fusion_data(split)


class XCLIPDataset(Dataset):
    def __init__(self, data_list, processor, num_frames=8):
        """
        Dataset cho X-CLIP.
        Args:
            data_list: List các dict chứa {path, text, label}
            processor: XCLIPProcessor (xử lý cả text và video)
            num_frames: Số lượng frame lấy mẫu từ video
        """
        self.data = data_list
        self.processor = processor
        self.num_frames = num_frames

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # [FIX] Tạo đường dẫn tuyệt đối
        full_video_path = os.path.join(BASE_PROJECT_PATH, item["path"])

        # 1. Xử lý Video (Extract Frames)
        frames = extract_frames(full_video_path, self.num_frames)

        if frames is None:
            # Fallback: Trả về khung hình đen nếu lỗi đọc video
            frames = [np.zeros((224, 224, 3), dtype="uint8")] * self.num_frames

        # 2. Xử lý Text & Video qua Processor của X-CLIP
        # Processor này sẽ tự động Tokenize Text và Normalize Video pixel values
        inputs = self.processor(
            text=[item["text"]],
            videos=list(frames),
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=77,  # Giới hạn token chuẩn của CLIP
        )

        return {
            "input_ids": inputs["input_ids"].squeeze(0),
            "attention_mask": inputs["attention_mask"].squeeze(0),
            "pixel_values": inputs["pixel_values"].squeeze(0),
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }
