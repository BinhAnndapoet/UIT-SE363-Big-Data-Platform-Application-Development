import sys
import os
import json
import pandas as pd
from collections import Counter
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs.paths import (
    get_video_paths,
    find_all_video_files,
    BASE_PROJECT_PATH,
    MASTER_TRAIN_INDEX,
    MASTER_VAL_INDEX,
    MASTER_TEST_INDEX,
    AUDIO_DATA_DIR,
    TEXT_LABEL_FILE,
    TEXT_TRAIN_CSV,
    TEXT_VAL_CSV,
    TEXT_TEST_CSV,
    FUSION_TRAIN_JSON,
    FUSION_VAL_JSON,
    FUSION_TEST_JSON,
)

# Split ratios (must sum to 1.0)
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

if abs((TRAIN_RATIO + VAL_RATIO + TEST_RATIO) - 1.0) > 1e-9:
    raise ValueError("TRAIN_RATIO + VAL_RATIO + TEST_RATIO must sum to 1.0")


def load_text_labels():
    """
    Load labels từ file CSV gốc (được gán bởi LLM API).
    Returns: dict {video_id: label}
    """
    if not os.path.exists(TEXT_LABEL_FILE):
        print(f"❌ Không tìm thấy file gốc: {TEXT_LABEL_FILE}")
        return {}

    df = pd.read_csv(TEXT_LABEL_FILE, dtype=str, low_memory=False)

    # Xử lý video_id từ filename hoặc path
    if "video_id" not in df.columns:
        if "filename" in df.columns:
            df["video_id"] = df["filename"].apply(lambda f: os.path.splitext(str(f))[0])
        elif "path" in df.columns:
            df["video_id"] = df["path"].apply(
                lambda p: os.path.splitext(os.path.basename(str(p)))[0]
            )

    # Clean label
    label_map = {
        "harmful": 1,
        "not_harmful": 0,
        "safe": 0,
        "0": 0,
        "1": 1,
        "0.0": 0,
        "1.0": 1,
    }
    df["label"] = (
        df["label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(label_map)
        .fillna(0)
        .astype(int)
    )

    # Return dict: {video_id: label}
    label_dict = {}
    for vid, group in df.groupby("video_id"):
        # Nếu cùng video_id có nhiều label, lấy max (ưu tiên harmful=1)
        label_dict[str(vid)] = int(group["label"].max())

    print(f"📋 Loaded {len(label_dict)} labels from CSV gốc")
    return label_dict


def print_distribution(name, data, is_dict_list=False):
    """
    Hàm in thống kê số lượng label 0 và 1.
    :param data: List of Dict (Video) hoặc DataFrame (Text)
    :param is_dict_list: True nếu data là list of dict, False nếu là DataFrame
    """
    if is_dict_list:
        labels = [x["label"] for x in data]
        total = len(data)
    else:
        labels = data["label"]
        total = len(data)

    counts = Counter(labels)
    c0 = counts.get(0, 0)
    c1 = counts.get(1, 0)

    p0 = (c0 / total * 100) if total > 0 else 0
    p1 = (c1 / total * 100) if total > 0 else 0

    print(
        f"  - {name:<5}: Total={total:<5} | Label 0: {c0:<4} ({p0:.1f}%) | Label 1: {c1:<4} ({p1:.1f}%)"
    )


def prepare_data_splits():
    """
    BƯỚC 1: QUÉT VIDEO GỐC -> TẠO MASTER SPLIT (JSON)
    Label được lấy từ CSV gốc (LLM annotation), KHÔNG phải từ folder.
    """
    print("🚀 Đang quét dữ liệu video để tạo Master Index...")

    # Load labels từ CSV gốc (LLM annotation)
    label_dict = load_text_labels()
    if not label_dict:
        print("❌ Không load được labels từ CSV. Dừng.")
        return

    harmful_dirs, not_harmful_dirs = get_video_paths()
    harmful_files = find_all_video_files(harmful_dirs)
    not_harmful_files = find_all_video_files(not_harmful_dirs)

    print(f"   - Files from harmful folders: {len(harmful_files)}")
    print(f"   - Files from not_harmful folders: {len(not_harmful_files)}")

    def create_entry(path):
        """Tạo entry với label từ CSV gốc, không phải từ folder."""
        filename = os.path.basename(path)
        video_id = os.path.splitext(filename)[0]

        # Lấy label từ CSV gốc (LLM annotation)
        label = label_dict.get(video_id, None)
        if label is None:
            return None  # Bỏ qua video không có label trong CSV

        wav_name = os.path.splitext(filename)[0] + ".wav"
        abs_audio_path = os.path.join(AUDIO_DATA_DIR, wav_name)
        rel_video_path = os.path.relpath(path, BASE_PROJECT_PATH)
        rel_audio_path = os.path.relpath(abs_audio_path, BASE_PROJECT_PATH)

        return {
            "path": rel_video_path,
            "audio_path": rel_audio_path,
            "label": label,  # Label từ CSV gốc
            "filename": filename,
            "video_id": video_id,
        }

    data = []
    all_files = harmful_files + not_harmful_files

    for p in all_files:
        entry = create_entry(p)
        if entry is not None:
            data.append(entry)

    # --------------------------------------------------
    # IMPORTANT: De-duplicate / group by video_id
    # Some sources may contain the same video filename in multiple folders (e.g., data/ and data_1/).
    # If we split by raw file entries, the same video_id can leak across splits.
    # De-duplicate theo video_id (Ưu tiên file đầu tiên tìm thấy)
    # --------------------------------------------------
    by_video_id = {}
    duplicates = 0
    label_conflicts = 0
    for item in data:
        vid = item.get("video_id")
        if not vid:
            continue
        if vid not in by_video_id:
            by_video_id[vid] = item
            continue

        duplicates += 1
        # If conflict in label, log and keep the first occurrence (deterministic)
        if by_video_id[vid].get("label") != item.get("label"):
            label_conflicts += 1

    if duplicates > 0:
        print(
            f"⚠️ Detected {duplicates} duplicate entries by video_id; {label_conflicts} label conflicts."
        )
        if label_conflicts > 0:
            print(
                "   ⚠️ Conflicting labels for the same video_id were found. Keeping the first occurrence (deterministic)."
            )

    data = list(by_video_id.values())

    # Stratified split by label with explicit ratios.
    # Step 1: train vs temp
    temp_ratio = 1.0 - TRAIN_RATIO
    train_data, temp_data = train_test_split(
        data,
        test_size=temp_ratio,
        stratify=[x["label"] for x in data],
        random_state=42,
    )
    # Step 2: temp -> val/test
    # Among temp, allocate TEST_RATIO and VAL_RATIO proportionally
    test_within_temp = TEST_RATIO / (VAL_RATIO + TEST_RATIO)
    val_data, test_data = train_test_split(
        temp_data,
        test_size=test_within_temp,
        stratify=[x["label"] for x in temp_data],
        random_state=42,
    )

    print(f"📊 Thống kê phân bố nhãn (Video/Audio):")
    print_distribution("Train", train_data, is_dict_list=True)
    print_distribution("Val", val_data, is_dict_list=True)
    print_distribution("Test", test_data, is_dict_list=True)

    with open(MASTER_TRAIN_INDEX, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=4)
    with open(MASTER_VAL_INDEX, "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=4)
    with open(MASTER_TEST_INDEX, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=4)

    print("✅ Đã lưu Master Index vào data_splits/")


def prepare_text_splits():
    """
    BƯỚC 2: XỬ LÝ TEXT DỰA TRÊN MASTER SPLIT
    """
    print("\n🚀 [Text] Đang xử lý Text Splits...")

    if not os.path.exists(TEXT_LABEL_FILE):
        print(f"❌ Không tìm thấy file gốc: {TEXT_LABEL_FILE}")
        return

    df = pd.read_csv(TEXT_LABEL_FILE, dtype=str, low_memory=False)

    # 1. Clean Label
    label_map = {
        "harmful": 1,
        "not_harmful": 0,
        "safe": 0,
        "0": 0,
        "1": 1,
        "0.0": 0,
        "1.0": 1,
    }
    df["label"] = (
        df["label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(label_map)
        .fillna(0)
        .astype(int)
    )

    # 2. Clean Video ID
    if "video_id" not in df.columns:
        df["video_id"] = df["path"].apply(
            lambda p: os.path.splitext(os.path.basename(str(p)))[0]
        )
    df["video_id"] = df["video_id"].astype(str).str.strip()
    df["text"] = df["text"].astype(str).str.strip()

    # 3. Load Master IDs và Labels (Ground Truth từ folder gốc)
    if not (os.path.exists(MASTER_TRAIN_INDEX) and os.path.exists(MASTER_TEST_INDEX)):
        print("⚠️ Cần chạy prepare_data_splits() trước.")
        return

    with open(MASTER_TRAIN_INDEX, "r") as f:
        train_data = json.load(f)
        train_ids = {str(x["video_id"]) for x in train_data}
    with open(MASTER_VAL_INDEX, "r") as f:
        val_data = json.load(f)
        val_ids = {str(x["video_id"]) for x in val_data}
    with open(MASTER_TEST_INDEX, "r") as f:
        test_data = json.load(f)
        test_ids = {str(x["video_id"]) for x in test_data}

    # Filter DF
    df_train = df[df["video_id"].isin(train_ids)].copy()
    df_val = df[df["video_id"].isin(val_ids)].copy()
    df_test = df[df["video_id"].isin(test_ids)].copy()

    # --- HÀM GỘP: CONCAT TEXT VỚI [SEP] ---
    def _aggregate_to_concat(df_split):
        """
        Gộp tất cả text của 1 video thành 1 string dài.
        Text đã được concat sẵn với [SEP] từ preprocess.
        Nếu có nhiều dòng (từ nhiều folder), nối thêm với [SEP].

        Label lấy từ CSV (LLM annotation) - phân tích nội dung text.
        """
        if df_split.empty:
            return pd.DataFrame(columns=["video_id", "filename", "label", "text"])

        rows = []
        for vid, group in df_split.groupby("video_id"):
            # Lấy toàn bộ các dòng text thuộc video này
            raw_texts = [
                str(t).strip() for t in group["text"].tolist() if str(t).strip()
            ]

            # Nối các text strings với [SEP]
            # Text đã có [SEP] sẵn, nên chỉ cần nối các dòng khác nhau
            text_concat = " [SEP] ".join(raw_texts)

            # Chuẩn hóa: loại bỏ [SEP] thừa ở đầu/cuối và double [SEP]
            text_concat = text_concat.strip()
            while " [SEP]  [SEP] " in text_concat:
                text_concat = text_concat.replace(" [SEP]  [SEP] ", " [SEP] ")
            text_concat = text_concat.strip(" [SEP]").strip()

            # Lấy label từ CSV (LLM annotation cho text content)
            # Nếu có nhiều dòng với label khác nhau, lấy max (ưu tiên harmful=1)
            label = int(group["label"].max())

            # Tạo filename từ video_id
            filename = f"{vid}.mp4"

            rows.append(
                {
                    "video_id": vid,
                    "filename": filename,
                    "label": label,
                    "text": text_concat,
                }
            )

        return pd.DataFrame(rows)

    df_train_agg = _aggregate_to_concat(df_train)
    df_val_agg = _aggregate_to_concat(df_val)
    df_test_agg = _aggregate_to_concat(df_test)

    # Lưu CSV
    df_train_agg.to_csv(TEXT_TRAIN_CSV, index=False)
    df_val_agg.to_csv(TEXT_VAL_CSV, index=False)
    df_test_agg.to_csv(TEXT_TEST_CSV, index=False)

    print(f"✅ [Text] Đã lưu CSV Splits vào processed_data/text/")
    print_distribution("Train", df_train_agg)
    print_distribution("Val", df_val_agg)
    print_distribution("Test", df_test_agg)


def prepare_fusion_splits():
    """
    BƯỚC 3: TẠO FUSION DATASET (JSON)
    - Load Video Info từ Master Index.
    - Load Text Info từ CSV (text đã được concat với [SEP]).
    - Lưu vào JSON cho fusion model.
    """
    print("\n🚀 [Fusion] Đang tạo Dataset cho Fusion Model...")

    def create_fusion_json(master_json, text_csv, output_json, split_name):
        if not os.path.exists(master_json) or not os.path.exists(text_csv):
            print(f"⚠️ Thiếu file nguồn cho {split_name}")
            return

        with open(master_json, "r") as f:
            video_data = json.load(f)

        # Đọc file CSV text
        text_df = pd.read_csv(text_csv, dtype={"video_id": str})
        # Map: video_id -> text (đã là string concat với [SEP])
        text_map = text_df.set_index("video_id")["text"].to_dict()

        fusion_list = []

        for item in video_data:
            vid = str(item["video_id"])
            video_path = item["path"]

            # Text đã là string concat, không cần parse JSON
            raw_text = text_map.get(vid, "")
            if pd.isna(raw_text):
                raw_text = ""

            entry = {
                "video_id": vid,
                "video_path": video_path,
                "text": str(raw_text),  # String concat với [SEP]
                "label": int(item["label"]),
            }
            fusion_list.append(entry)

        # Lưu file JSON cuối cùng
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(fusion_list, f, ensure_ascii=False, indent=4)

        print(
            f"   - {split_name:<5}: Saved {len(fusion_list)} samples to {os.path.basename(output_json)}"
        )

    create_fusion_json(MASTER_TRAIN_INDEX, TEXT_TRAIN_CSV, FUSION_TRAIN_JSON, "Train")
    create_fusion_json(MASTER_VAL_INDEX, TEXT_VAL_CSV, FUSION_VAL_JSON, "Val")
    create_fusion_json(MASTER_TEST_INDEX, TEXT_TEST_CSV, FUSION_TEST_JSON, "Test")

    print(f"✅ [Fusion] Hoàn tất tạo dữ liệu tại: {os.path.dirname(FUSION_TRAIN_JSON)}")


if __name__ == "__main__":
    prepare_data_splits()  # 1. Master Splits (Video)
    prepare_text_splits()  # 2. Text Splits (CSV with JSON List)
    prepare_fusion_splits()  # 3. Fusion Splits (JSON with Path & List)
