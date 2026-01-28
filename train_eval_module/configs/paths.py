import os


# 1. Xác định thư mục chứa code (train_eval_module)
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PROJECT_PATH = os.path.dirname(CURRENT_DIR)

# 2. Nguồn dữ liệu gốc (Raw)
DATA_SOURCES = ["data", "data_1", "data_viet"]
TEXT_LABEL_FILE = os.path.join(
    BASE_PROJECT_PATH,
    "processed_data",
    "text",
    "TRAINING_TEXT_DATA_FINAL_COMBINED.csv",
)

# 3. Định nghĩa thư mục Output/Logs
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")
LOG_DIR = os.path.join(CURRENT_DIR, "logs")

# 4. Processed Data (Audio & Text)
# Nơi chứa các file sinh ra từ bước preprocess (như audio wav)
PROCESSED_DIR = os.path.join(BASE_PROJECT_PATH, "processed_data")
AUDIO_DATA_DIR = os.path.join(PROCESSED_DIR, "audios")
TEXT_PROCESSED_DIR = os.path.join(PROCESSED_DIR, "text")

# 5. Đường dẫn 3 file Split Text cố định
TEXT_TRAIN_CSV = os.path.join(TEXT_PROCESSED_DIR, "train_split.csv")
TEXT_VAL_CSV = os.path.join(TEXT_PROCESSED_DIR, "eval_split.csv")  # eval = val
TEXT_TEST_CSV = os.path.join(TEXT_PROCESSED_DIR, "test_split.csv")

# 6. Master Index Splits (Video)
SPLIT_DIR = os.path.join(CURRENT_DIR, "data_splits")
MASTER_TRAIN_INDEX = os.path.join(SPLIT_DIR, "train_split.json")
MASTER_VAL_INDEX = os.path.join(SPLIT_DIR, "val_split.json")
MASTER_TEST_INDEX = os.path.join(SPLIT_DIR, "test_split.json")

# 7. [NEW] Fusion Data Configs
# Nơi chứa file JSON kết hợp Video Path + Text List
FUSION_DATA_DIR = os.path.join(PROCESSED_DIR, "fusion")
FUSION_TRAIN_JSON = os.path.join(FUSION_DATA_DIR, "train_fusion.json")
FUSION_VAL_JSON = os.path.join(FUSION_DATA_DIR, "val_fusion.json")
FUSION_TEST_JSON = os.path.join(FUSION_DATA_DIR, "test_fusion.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SPLIT_DIR, exist_ok=True)
os.makedirs(AUDIO_DATA_DIR, exist_ok=True)
os.makedirs(TEXT_PROCESSED_DIR, exist_ok=True)
os.makedirs(FUSION_DATA_DIR, exist_ok=True)


def get_video_paths():
    """
    Tự động quét tất cả folder harmful/not_harmful từ các nguồn data
    Trả về: (harmful_dirs, not_harmful_dirs)
    """
    harmful_dirs = []
    not_harmful_dirs = []

    for source in DATA_SOURCES:
        video_root = os.path.join(BASE_PROJECT_PATH, source, "videos")
        h_path = os.path.join(video_root, "harmful")
        nh_path = os.path.join(video_root, "not_harmful")

        if os.path.exists(h_path):
            harmful_dirs.append(h_path)
        if os.path.exists(nh_path):
            not_harmful_dirs.append(nh_path)

    return harmful_dirs, not_harmful_dirs


def find_all_video_files(dir_list):
    """
    Tìm đệ quy file video trong danh sách thư mục
    """
    video_files = []
    exts = (".mp4", ".MP4", ".avi", ".AVI", ".mov")

    for d in dir_list:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for file in files:
                    if file.endswith(exts):
                        video_files.append(os.path.join(root, file))
    return video_files
