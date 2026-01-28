import torch
from torch.utils.data import Dataset
import os
import json
import torchaudio
import random
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from configs.paths import (
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    BASE_PROJECT_PATH,
)


def load_audio_data(split="train"):
    paths = {
        "train": MASTER_TRAIN_INDEX,
        "val": MASTER_VAL_INDEX,
        "test": MASTER_TEST_INDEX,
    }
    if not os.path.exists(paths[split]):
        return []
    with open(paths[split], "r") as f:
        return json.load(f)


class AudioDataset(Dataset):
    def __init__(
        self,
        data_list,
        processor,
        split="train",
        sampling_rate=16000,
        max_duration=10.0,
    ):
        self.data = data_list
        self.processor = processor
        self.split = split
        self.sampling_rate = sampling_rate
        self.max_samples = int(max_duration * sampling_rate)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        rel_audio_path = item.get("audio_path", item["path"].replace(".mp4", ".wav"))
        full_audio_path = os.path.join(BASE_PROJECT_PATH, rel_audio_path)

        speech = torch.zeros(self.max_samples)  # Mặc định là im lặng

        if os.path.exists(full_audio_path):
            try:
                waveform, sr = torchaudio.load(full_audio_path)

                # Resample về 16k
                if sr != self.sampling_rate:
                    waveform = torchaudio.transforms.Resample(sr, self.sampling_rate)(
                        waveform
                    )

                # Chuyển về Mono
                if waveform.shape[0] > 1:
                    waveform = waveform.mean(dim=0)
                else:
                    waveform = waveform.squeeze()

                curr_len = waveform.size(0)

                # --- LOGIC MỚI: RANDOM CROP (Cắt liền mạch) ---
                # Thay vì nối đầu đuôi, ta cắt 1 đoạn 10s liên tục ngẫu nhiên
                if curr_len >= self.max_samples:
                    if self.split == "train":
                        # Train: Cắt ngẫu nhiên (Data Augmentation)
                        start = random.randint(0, curr_len - self.max_samples)
                    else:
                        # Val/Test: Luôn lấy đoạn giữa (Center Crop)
                        start = (curr_len - self.max_samples) // 2

                    speech = waveform[start : start + self.max_samples]

                else:
                    # Nếu ngắn hơn 10s: Lặp lại (Loop) cho đủ
                    # Loop tốt hơn Padding 0 vì model có nhiều tín hiệu để học hơn
                    if curr_len > 1000:  # Chỉ loop file hợp lệ (>0.06s)
                        repeat_times = (self.max_samples // curr_len) + 1
                        speech = waveform.repeat(repeat_times)[: self.max_samples]
                    else:
                        speech[:curr_len] = waveform

                # Chuẩn hóa Z-Score (Cực quan trọng để thoát Loss 0.69)
                if speech.std() > 0:
                    speech = (speech - speech.mean()) / (speech.std() + 1e-7)

            except Exception:
                pass

        inputs = self.processor(
            speech.numpy(), sampling_rate=self.sampling_rate, return_tensors="pt"
        )

        return {
            "input_values": inputs["input_values"].squeeze(0),
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }
