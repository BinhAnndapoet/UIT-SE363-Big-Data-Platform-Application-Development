# scripts/test_valid_videos.py
import sys
import os
import numpy as np
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.paths import get_video_paths, find_all_video_files, LOG_DIR
from shared_utils.processing import extract_frames


def check_video_integrity_sync(video_path):
    """
    Kiểm tra bằng cách CHẠY THỬ hàm extract_frames y hệt lúc train.
    """
    try:
        if os.path.getsize(video_path) == 0:
            return False, "File 0KB"

        frames = extract_frames(video_path, num_frames=16, resize=224)

        if frames is None:
            return False, "Decord không đọc được (Header lỗi hoặc file hỏng)"

        if len(frames) != 16:
            return False, f"Lỗi Logic: Chỉ lấy được {len(frames)} frames (Kỳ vọng 16)"

        if frames[0].shape != (224, 224, 3):
            return False, f"Sai kích thước ảnh: {frames[0].shape}"

        return True, "OK"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def main():
    print("=" * 80)
    print("KIỂM TRA ĐỒNG BỘ VỚI PROCESSING (SYNC CHECK)")
    print("=" * 80)

    print(">> Đang quét danh sách file...")
    harmful_dirs, not_harmful_dirs = get_video_paths()
    all_files = find_all_video_files(harmful_dirs) + find_all_video_files(
        not_harmful_dirs
    )

    if len(all_files) == 0:
        print("❌ Không tìm thấy video!")
        return

    print(f">> Tìm thấy: {len(all_files)} video.")
    print(">> Đang mô phỏng quá trình đọc dữ liệu Training...")

    corrupted_files = []
    progress_bar = tqdm(all_files, desc="Sync Validating", unit="video")

    for file_path in progress_bar:
        is_valid, reason = check_video_integrity_sync(file_path)

        if not is_valid:
            corrupted_files.append((file_path, reason))

    os.makedirs(LOG_DIR, exist_ok=True)
    output_log_file = os.path.join(LOG_DIR, "corrupted_videos_list.txt")

    print("\n" + "=" * 80)
    print("KẾT QUẢ KIỂM TRA:")

    with open(output_log_file, "w", encoding="utf-8") as f:
        f.write(
            f"SYNC CHECK REPORT - Timestamp: {os.path.getmtime(output_log_file) if os.path.exists(output_log_file) else 'New'}\n"
        )
        f.write(f"Total scanned: {len(all_files)}\n")
        f.write(f"Corrupted: {len(corrupted_files)}\n")
        f.write("=" * 80 + "\n")

        for i, (path, reason) in enumerate(corrupted_files, 1):
            f.write(f"{i}. [{reason}] | {path}\n")

    if len(corrupted_files) > 0:
        print(f"❌ PHÁT HIỆN {len(corrupted_files)} VIDEO KHÔNG THỂ TRAIN!")
        print("-" * 80)

        preview_limit = 10
        for i, (path, reason) in enumerate(corrupted_files[:preview_limit], 1):
            print(f"{i}. [{reason}]")
            print(f"   .../{os.path.basename(path)}")

        if len(corrupted_files) > preview_limit:
            remaining = len(corrupted_files) - preview_limit
            print(f"\n... và {remaining} file khác.")

        print("-" * 80)
        print(f"📝 Danh sách ĐẦY ĐỦ đã được lưu tại:")
        print(f"👉 {os.path.abspath(output_log_file)}")
    else:
        print("✅ TUYỆT VỜI! 100% Video đều vượt qua quy trình xử lý.")
        if os.path.exists(output_log_file):
            with open(output_log_file, "w") as f:
                f.write("No corrupted files found.")

    print("=" * 80)


if __name__ == "__main__":
    main()
