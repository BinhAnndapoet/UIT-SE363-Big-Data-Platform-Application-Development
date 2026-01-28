import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from configs.paths import (
    BASE_PROJECT_PATH,
    TEXT_LABEL_FILE,
    OUTPUT_DIR,
    LOG_DIR,
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    AUDIO_DATA_DIR,
    TEXT_PROCESSED_DIR,
    TEXT_TEST_CSV,
    TEXT_TRAIN_CSV,
    TEXT_VAL_CSV,
    FUSION_DATA_DIR,
    FUSION_TEST_JSON,
    FUSION_TRAIN_JSON,
    FUSION_VAL_JSON,
    get_video_paths,
)


def check_split_status():
    """Kiểm tra xem các file Master Index JSON đã có chưa."""
    missing = []
    if not os.path.exists(MASTER_TRAIN_INDEX):
        missing.append("Master Train JSON")
    if not os.path.exists(MASTER_VAL_INDEX):
        missing.append("Master Val JSON")
    if not os.path.exists(MASTER_TEST_INDEX):
        missing.append("Master Test JSON")

    if missing:
        return False, f"⚠️ Thiếu file định nghĩa tập dữ liệu: {', '.join(missing)}"

    try:
        with open(MASTER_TRAIN_INDEX, "r") as f:
            data = json.load(f)
            if not data:
                return False, "⚠️ File Master Train JSON bị rỗng."
            if len(data) > 0 and "audio_path" not in data[0]:
                return (
                    True,
                    "⚠️ JSON tồn tại nhưng thiếu trường 'audio_path' (Cần chạy lại split_data.py).",
                )
    except:
        return False, "⚠️ File Master Train JSON lỗi định dạng."

    return True, "✅ Đã tìm thấy 3 file Master Index (Train/Val/Test)."


def check_connection():
    print("=" * 80)
    print(f"🛠️  KIỂM TRA HỆ THỐNG (REFACTORED MODULE)")
    print("=" * 80)

    print(f"\n[0] KIỂM TRA ĐƯỜNG DẪN CƠ BẢN:")
    print(f"   - Project Base Path: {BASE_PROJECT_PATH}")
    print(f"   - Output Dir: {OUTPUT_DIR}")
    print(f"   - Log Dir: {LOG_DIR}")
    print(f"   - Audio Data Dir: {AUDIO_DATA_DIR}")
    print(f"   - Text Processed Dir: {TEXT_PROCESSED_DIR}")
    print(f"   - Text Train CSV: {TEXT_TRAIN_CSV}")
    print(f"   - Text Val CSV: {TEXT_VAL_CSV}")
    print(f"   - Text Test CSV: {TEXT_TEST_CSV}")

    #  PHẦN 1: KIỂM TRA NGUỒN DỮ LIỆU GỐC
    harmful_dirs, not_harmful_dirs = get_video_paths()

    print(f"\n[1] NGUỒN DỮ LIỆU ĐẦU VÀO (RAW INPUT):")
    print(f"   - Harmful Sources ({len(harmful_dirs)}):")
    for p in harmful_dirs:
        print(f"     + {p}")

    print(f"   - Not Harmful Sources ({len(not_harmful_dirs)}):")
    for p in not_harmful_dirs:
        print(f"     + {p}")

    #  PHẦN 2: KIỂM TRA AUDIO PROCESSED
    print("\n[2] KIỂM TRA AUDIO DATA (PROCESSED):")
    if os.path.exists(AUDIO_DATA_DIR):
        num_wav = len([f for f in os.listdir(AUDIO_DATA_DIR) if f.endswith(".wav")])
        print(f"   ✅ Thư mục tồn tại: {AUDIO_DATA_DIR}")
        print(f"   ℹ️  Số lượng file .wav: {num_wav}")
        if num_wav == 0:
            print(
                "   ⚠️  Chưa có file audio nào. Hãy chạy: python scripts/preprocess_audio.py"
            )
    else:
        print(f"   ❌ Không tìm thấy thư mục audio: {AUDIO_DATA_DIR}")

    #  PHẦN 3: KIỂM TRA TEXT LABELS
    print("\n[3] KIỂM TRA TEXT LABELS:")
    if os.path.exists(TEXT_LABEL_FILE):
        print(f"   ✅ Đã tìm thấy: {TEXT_LABEL_FILE}")
    else:
        print(
            f"   ❌ Không tìm thấy: {TEXT_LABEL_FILE} (Cảnh báo: Có thể lỗi trong quá trình tiền xử lý text!"
        )

    if os.path.exists(TEXT_PROCESSED_DIR):
        num_csv = len([f for f in os.listdir(TEXT_PROCESSED_DIR) if f.endswith(".csv")])
        print(f"   ✅ Thư mục tồn tại: {TEXT_PROCESSED_DIR}")
        print(f"   ℹ️  Số lượng file .csv: {num_csv}")

        if num_csv == 0:
            print(
                "   ⚠️  Chưa có file text nào. Hãy chạy: KIỂM TRA TRẠNG THÁI SPLIT DATA || PREPROCESS DATA"
            )

    else:
        print(f"   ❌ Không tìm thấy thư mục text: {TEXT_PROCESSED_DIR}")

    print("\n   KIỂM TRA CÁC FILE CSV SPLIT CHÍNH:")
    check = False
    if (
        not os.path.exists(TEXT_TRAIN_CSV)
        and not os.path.exists(TEXT_VAL_CSV)
        and not os.path.exists(TEXT_TEST_CSV)
    ):
        print(f"   ❌ Thiếu file: {TEXT_TRAIN_CSV}")
        print(f"   ❌ Thiếu file: {TEXT_TEST_CSV}")
        print(f"   ❌ Thiếu file: {TEXT_VAL_CSV}")
    else:
        check = True

    if (
        not os.path.exists(FUSION_TRAIN_JSON)
        and not os.path.exists(FUSION_VAL_JSON)
        and not os.path.exists(FUSION_TEST_JSON)
    ):
        print(f"   ❌ Thiếu file: {FUSION_TRAIN_JSON}")
        print(f"   ❌ Thiếu file: {FUSION_TEST_JSON}")
        print(f"   ❌ Thiếu file: {FUSION_VAL_JSON}")
    else:
        check = True

    if check:
        print("   ✅ Tất cả file CSV cần thiết đã có.")
        print(f"     - {TEXT_TRAIN_CSV}")
        print(f"     - {TEXT_VAL_CSV}")
        print(f"     - {TEXT_TEST_CSV}")
    else:
        print("   ⚠️  Chưa đủ file CSV cần thiết.")
        print("   ⚠️  Hãy chạy: python scripts/split_data.py")

    #  PHẦN 4: KIỂM TRA TRẠNG THÁI SPLIT DATA
    print("\n[4] KIỂM TRA MASTER INDEX (JSON):")
    is_split, msg = check_split_status()
    print(f"   {msg}")

    #  PHẦN 5: KẾT LUẬN
    print("-" * 80)
    print("📢  KẾT LUẬN & HÀNH ĐỘNG TIẾP THEO:")

    if is_split:
        print("🟢  Dữ liệu Index ĐÃ SẴN SÀNG.")
    else:
        print("🟡  Chưa có file chia dữ liệu Master Index.")
        print("🔨  Vui lòng chạy lệnh: python scripts/split_data.py")
    print("-" * 80)


if __name__ == "__main__":
    check_connection()
