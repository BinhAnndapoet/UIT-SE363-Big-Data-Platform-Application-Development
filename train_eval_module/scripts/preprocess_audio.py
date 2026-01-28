import sys
import os
import subprocess
import shutil
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from configs.paths import get_video_paths, find_all_video_files, AUDIO_DATA_DIR


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("❌ LỖI: Cần cài đặt ffmpeg (conda install -c conda-forge ffmpeg)")
        return False
    return True


def extract_audio_from_videos():
    if not check_ffmpeg():
        return
    print(
        f"🚀 TÁCH AUDIO: Loudnorm (Đồng bộ âm lượng) + Silence Remove (Cắt im lặng)..."
    )
    os.makedirs(AUDIO_DATA_DIR, exist_ok=True)

    harmful_dirs, not_harmful_dirs = get_video_paths()
    all_videos = find_all_video_files(harmful_dirs + not_harmful_dirs)

    success, skip, error = 0, 0, 0

    for video_path in tqdm(all_videos, desc="Processing"):
        filename = os.path.basename(video_path)
        wav_filename = os.path.splitext(filename)[0] + ".wav"
        output_path = os.path.join(AUDIO_DATA_DIR, wav_filename)

        if os.path.exists(output_path):
            skip += 1
            continue

        try:
            # -af loudnorm: Chuẩn hóa âm lượng to/nhỏ về mức chuẩn
            # -af silenceremove: Cắt bỏ đoạn im lặng đầu file để model vào đề ngay
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1",
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                output_path,
                "-y",
                "-loglevel",
                "error",
            ]
            subprocess.run(cmd, check=True)
            success += 1
        except:
            error += 1

    print(f"✅ Xong: Mới {success} | Skip {skip} | Lỗi {error}")


if __name__ == "__main__":
    extract_audio_from_videos()
