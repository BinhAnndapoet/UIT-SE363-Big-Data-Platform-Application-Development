"""
Text Dataset - Phiên bản đơn giản, chuẩn HuggingFace.

Input: CSV với cột text (chuỗi text dài, đã gộp comments bằng [SEP])
Output: Dict chuẩn cho Trainer {input_ids, attention_mask, labels}
"""

import torch
import re
import unicodedata
from torch.utils.data import Dataset
import pandas as pd
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from configs.paths import TEXT_TRAIN_CSV, TEXT_VAL_CSV, TEXT_TEST_CSV


def clean_text(text):
    """
    Làm sạch text TikTok tiếng Việt trước khi tokenize.
    Giữ nguyên [SEP] để model hiểu ranh giới giữa các comment.
    """
    if not isinstance(text, str):
        return ""

    if not text.strip():
        return ""

    # 1. Unicode Normalize - Chuẩn hóa tiếng Việt
    text = unicodedata.normalize("NFC", text)

    # 2. Xóa zero-width characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\u00ad]", "", text)

    # 3. Xử lý URLs - Thay bằng token đặc biệt
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # 4. Xử lý mentions và hashtags
    text = re.sub(r"@[\w\.]+", " ", text)  # @username
    text = re.sub(r"#(\w+)", r" \1 ", text)  # #hashtag -> hashtag

    # 5. Xử lý emoji - Giữ lại emoji vì chúng mang ý nghĩa
    # Không xóa emoji, BERT tokenizer sẽ xử lý

    # 6. Xử lý ký tự lặp (ví dụ: "đẹpppp" -> "đẹpp")
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # 7. Xử lý dấu câu lặp
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)

    # 8. Xử lý số dài (số điện thoại, ID)
    text = re.sub(r"\b\d{7,}\b", " ", text)

    # 9. Chuẩn hóa khoảng trắng quanh [SEP]
    text = re.sub(r"\s*\[SEP\]\s*", " [SEP] ", text)

    # 10. Xử lý các ký tự đặc biệt không cần thiết
    text = re.sub(r"[\_\-\=\+\*\~\`\|\\\<\>]+", " ", text)

    # 11. Chuẩn hóa khoảng trắng cuối cùng
    text = re.sub(r"\s+", " ", text).strip()

    # 12. Xử lý text quá ngắn hoặc chỉ có [SEP]
    cleaned = text.replace("[SEP]", "").strip()
    if len(cleaned) < 2:
        return ""

    return text


def load_text_data(split="train"):
    """Load trực tiếp từ các file CSV đã split sẵn."""
    csv_file = None
    if split == "train":
        csv_file = TEXT_TRAIN_CSV
    elif split == "val":
        csv_file = TEXT_VAL_CSV
    elif split == "test":
        csv_file = TEXT_TEST_CSV

    if not csv_file or not os.path.exists(csv_file):
        print(f"❌ [Text] Không tìm thấy file split: {csv_file}")
        return pd.DataFrame()

    print(f"📂 [Text] Loading {split.upper()} from: {csv_file}")
    df = pd.read_csv(csv_file)

    # Đảm bảo format chuẩn
    df = df.dropna(subset=["text", "label"])
    df = df.reset_index(drop=True)
    df["label"] = df["label"].astype(int)
    df["text"] = df["text"].astype(str)

    return df


class TextDataset(Dataset):
    """
    Dataset đơn giản cho text classification.
    Input text đã là chuỗi dài (comments gộp bằng [SEP]).
    """

    def __init__(self, df, tokenizer, max_len=512):
        self.df = df
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        text = str(row["text"])
        label = int(row["label"])

        # Clean text
        text = clean_text(text)

        # Tokenize - Tokenizer sẽ tự truncate
        enc = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt",
        )

        return {
            "input_ids": enc["input_ids"].squeeze(0),  # (L,)
            "attention_mask": enc["attention_mask"].squeeze(0),  # (L,)
            "labels": torch.tensor(label, dtype=torch.long),
        }
