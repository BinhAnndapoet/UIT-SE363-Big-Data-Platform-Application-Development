import os
import subprocess
import shutil


def check_ffmpeg():
    """Kiểm tra xem FFmpeg đã được cài đặt chưa"""
    if shutil.which("ffmpeg") is None:
        print("❌ LỖI: Không tìm thấy FFmpeg. Hãy cài đặt: sudo apt install ffmpeg")
        return False
    return True


def extract_audio_single(video_path, output_path):
    """
    Tách audio từ video, chuẩn hóa âm lượng và cắt khoảng lặng.
    Args:
        video_path: Đường dẫn file video đầu vào (.mp4)
        output_path: Đường dẫn file audio đầu ra (.wav)
    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    if not check_ffmpeg():
        return False

    if os.path.exists(output_path):
        os.remove(output_path)  # Xóa file cũ nếu tồn tại để ghi đè

    try:
        # -af loudnorm: Chuẩn hóa âm lượng (EBU R128)
        # -af silenceremove: Cắt bỏ đoạn im lặng đầu file (-50dB)
        # -ar 16000: Sampling rate 16kHz (Chuẩn cho Wav2Vec2)
        # -ac 1: Mono channel
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.1",
            "-vn",  # Không lấy hình ảnh
            "-acodec",
            "pcm_s16le",  # Codec Wav chuẩn
            "-ar",
            "16000",  # 16kHz
            "-ac",
            "1",  # Mono
            output_path,
            "-y",  # Overwrite
            "-loglevel",
            "error",  # Chỉ hiện lỗi
        ]

        subprocess.run(cmd, check=True)
        # Kiểm tra file sinh ra có dung lượng > 0 không
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False

    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Audio Extract Error: {e}")
        return False
