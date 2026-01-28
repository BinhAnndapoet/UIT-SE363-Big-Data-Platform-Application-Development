import pandas as pd
import os
import time
import config
import argparse
from concurrent.futures import ThreadPoolExecutor
from clients.minio_kafka_clients import MinioClient, KafkaClient
from clients.data_cleaner import clean_text_advanced
from downloader import download_video_to_temp_mobile
from audio_processor import extract_audio_single


def process_single_video(url, label, minio, kafka):
    """Xử lý một video duy nhất: Download -> Audio -> MinIO -> Kafka"""
    print(f"\n▶️ Processing: {url}")

    # A. Download
    vid_id, video_local_path, raw_comments = download_video_to_temp_mobile(url)
    if not video_local_path:
        print(f"   ⚠️ Skip: Download failed cho video {url}")
        return

    # B. Extract Audio
    audio_local_path = os.path.join(config.TEMP_DOWNLOAD_DIR, f"{vid_id}.wav")
    has_audio = extract_audio_single(video_local_path, audio_local_path)

    if has_audio:
        print(f"   🎵 Extracted Audio: {os.path.basename(audio_local_path)}")
    else:
        print("   ⚠️ Audio extraction failed or empty.")

    try:
        # C. Upload Video & Audio lên MinIO
        minio_video_obj = f"raw/{label}/{vid_id}.mp4"
        minio_video_path = minio.upload_file(
            video_local_path,
            minio_video_obj,
            bucket_name=config.MINIO_BUCKET,
            content_type="video/mp4",
        )

        minio_audio_path = None
        if has_audio:
            minio_audio_obj = f"raw/{label}/{vid_id}.wav"
            minio_audio_path = minio.upload_file(
                audio_local_path,
                minio_audio_obj,
                bucket_name=config.MINIO_AUDIO_BUCKET,
                content_type="audio/wav",
            )

        if not minio_video_path:
            print("   ❌ Lỗi Upload Video MinIO.")
            return

        # D. Làm sạch text và gửi Kafka
        clean_comments = [clean_text_advanced(c) for c in raw_comments]
        full_text = " ".join(clean_comments)

        message = {
            "video_id": vid_id,
            "minio_video_path": minio_video_path,
            "minio_audio_path": minio_audio_path,
            "clean_text": full_text,
            "csv_label": label,
            "timestamp": time.time(),
        }

        kafka.send(message)
        print(f"   📡 Sent to Kafka (Multi-modal): {vid_id}")

    except Exception as e:
        print(f"   ❌ Lỗi xử lý pipeline: {e}")

    finally:
        # Cleanup file tạm sau khi đã đẩy lên MinIO
        if os.path.exists(video_local_path):
            os.remove(video_local_path)
        if has_audio and os.path.exists(audio_local_path):
            os.remove(audio_local_path)


def run():
    print("🚀 Starting Ingestion Worker (Multi-modal Mode)...")
    parser = argparse.ArgumentParser(description="Ingestion Worker CLI")
    parser.add_argument("--url", help="URL video TikTok")
    parser.add_argument("--label", default="unknown", help="Nhãn video")
    args = parser.parse_args()

    try:
        minio = MinioClient()
        kafka = KafkaClient()
    except Exception as e:
        print(f"❌ Kết nối Service thất bại: {e}")
        return

    if args.url:
        process_single_video(args.url, args.label, minio, kafka)
    else:

        if not os.path.exists(config.INPUT_CSV_PATH):
            print(f"❌ CSV not found: {config.INPUT_CSV_PATH}")
            return
        # Chế độ chạy theo Batch CSV
        df = pd.read_csv(config.INPUT_CSV_PATH)
        queue = df[df["link"].str.contains("/video/", na=False)]
        print(f"📋 Processing {len(queue)} videos from CSV...")

        # for idx, row in queue.iterrows():
        #     print(f"\n[{idx+1}/{len(queue)}] Đang xử lý hàng đợi...")
        #     process_single_video(row["link"], row.get("label", "unknown"), minio, kafka)

        #     # QUAN TRỌNG: Tăng thời gian nghỉ để tránh bị TikTok Captcha/Block
        #     print("⏳ Nghỉ 5s để tránh bị chặn...")
        #     time.sleep(5)

        # CHIẾN THUẬT: Chạy song song 2 luồng.
        # Đủ nhanh để Dashboard cập nhật liên tục, đủ chậm để không bị BAN.
        with ThreadPoolExecutor(max_workers=2) as executor:
            for idx, row in queue.iterrows():
                executor.submit(
                    process_single_video,
                    row["link"],
                    row.get("label", "unknown"),
                    minio,
                    kafka,
                )


if __name__ == "__main__":
    run()

    # df = pd.read_csv(config.INPUT_CSV_PATH)
    # # Lọc lấy các dòng có link video
    # queue = df[df["link"].str.contains("/video/", na=False)]

    # print(f"📋 Processing {len(queue)} videos...")

    # for _, row in queue.iterrows():
    #     url = row["link"]
    #     original_label = row.get("label", "unknown")

    #     print(f"\n▶️ Processing: {url}")

    #     # A. Download (Dùng logic yt-dlp mới)
    #     vid_id, video_local_path, raw_comments = download_video_to_temp(url)
    #     if not video_local_path:
    #         print("   ⚠️ Skip: Download failed.")
    #         continue

    #     # B. Extract Audio (Bước mới)
    #     audio_local_path = os.path.join(config.TEMP_DOWNLOAD_DIR, f"{vid_id}.wav")
    #     has_audio = extract_audio_single(video_local_path, audio_local_path)

    #     if has_audio:
    #         print(f"   🎵 Extracted Audio: {os.path.basename(audio_local_path)}")
    #     else:
    #         print("   ⚠️ Audio extraction failed or empty.")
    #     try:
    #         # C. Upload Video lên MinIO
    #         # Path lưu: raw/harmful/123.mp4
    #         minio_video_obj = f"raw/{original_label}/{vid_id}.mp4"
    #         minio_video_path = minio.upload_file(
    #             video_local_path,
    #             minio_video_obj,
    #             bucket_name=config.MINIO_BUCKET,
    #             content_type="video/mp4",
    #         )

    #         # D. Upload Audio lên MinIO (Nếu có)
    #         minio_audio_path = None
    #         if has_audio:
    #             minio_audio_obj = f"raw/{original_label}/{vid_id}.wav"
    #             minio_audio_path = minio.upload_file(
    #                 audio_local_path,
    #                 minio_audio_obj,
    #                 bucket_name=config.MINIO_AUDIO_BUCKET,
    #                 content_type="audio/wav",
    #             )

    #         if not minio_video_path:
    #             print("   ❌ Lỗi Upload Video MinIO.")
    #             continue

    #         # E. Process Text & Gửi Kafka (Chỉ làm sạch cơ bản, không chạy AI)
    #         clean_comments = [clean_text_advanced(c) for c in raw_comments]
    #         full_text = " ".join(clean_comments)

    #         # F.Message Kafka Cấu trúc Mới
    #         message = {
    #             "video_id": vid_id,
    #             "minio_video_path": minio_video_path,  # Path Video
    #             "minio_audio_path": minio_audio_path,  # Path Audio (có thể null)
    #             "clean_text": full_text,
    #             "csv_label": original_label,
    #             "timestamp": time.time(),
    #         }

    #         # Gửi dữ liệu thô sang Spark. Spark sẽ lo phần AI.
    #         kafka.send(message)
    #         print(f"   📡 Sent to Kafka (Multi-modal): {vid_id}")
    #     except Exception as e:
    #         print(f"   ❌ Lỗi xử lý pipeline: {e}")

    #     finally:
    #         # G. Cleanup
    #         if os.path.exists(video_local_path):
    #             os.remove(video_local_path)
    #         if os.path.exists(audio_local_path):
    #             os.remove(audio_local_path)

    #     # Nghỉ nhẹ
    #     time.sleep(2)

    # print("\n✅ Ingestion Job Finished!")


if __name__ == "__main__":
    run()
