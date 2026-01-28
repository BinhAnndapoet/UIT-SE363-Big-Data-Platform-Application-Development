# File: train_eval_module/scripts/check_audio_stats.py
import sys
import os
import json
import numpy as np

# Setup path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.paths import MASTER_TRAIN_INDEX


def check_stats():
    if not os.path.exists(MASTER_TRAIN_INDEX):
        print(f"❌ Không tìm thấy file index: {MASTER_TRAIN_INDEX}")
        return

    print(f"📂 Đang đọc dữ liệu từ: {MASTER_TRAIN_INDEX}")
    with open(MASTER_TRAIN_INDEX, "r") as f:
        data = json.load(f)

    # Lấy danh sách nhãn
    labels = [item["label"] for item in data]
    total = len(labels)

    count_0 = labels.count(0)  # Safe
    count_1 = labels.count(1)  # Harmful

    print("=" * 40)
    print("📊 THỐNG KÊ AUDIO DATASET (TRAIN)")
    print("=" * 40)
    print(f"🔹 Tổng số mẫu: {total}")
    print(f"✅ Safe (0):    {count_0} ({count_0/total*100:.2f}%)")
    print(f"❌ Harmful (1): {count_1} ({count_1/total*100:.2f}%)")

    if count_1 == 0:
        print("❌ LỖI NGHIÊM TRỌNG: Không có mẫu Harmful nào!")
        return

    # --- TÍNH TOÁN TRỌNG SỐ (CLASS WEIGHTS) ---
    # Công thức Balanced: Weight = Total / (n_classes * Count)
    w0 = total / (2 * count_0)
    w1 = total / (2 * count_1)

    print("-" * 40)
    print("⚖️  GỢI Ý CLASS WEIGHTS (Copy vào Config):")
    print(f"   [ {w0:.4f}, {w1:.4f} ]")
    print("-" * 40)


if __name__ == "__main__":
    check_stats()
