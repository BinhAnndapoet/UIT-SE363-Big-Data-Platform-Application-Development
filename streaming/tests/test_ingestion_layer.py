import pytest
from unittest.mock import patch, MagicMock
import os
from ingestion.main_worker import process_single_video
import ingestion.config as config

@patch("ingestion.main_worker.download_video_to_temp_mobile")
@patch("ingestion.main_worker.extract_audio_single")
@patch("os.path.exists")
@patch("os.remove")
def test_process_single_video_success(
    mock_remove, mock_exists, mock_extract_audio, mock_download, mock_minio_client, mock_kafka_client
):
    """Test successful flow: Download -> Extract Audio -> Upload -> Kafka"""
    
    # Setup Mocks
    mock_download.return_value = ("video123", "/tmp/video123.mp4", ["comment1", "comment2"])
    mock_extract_audio.return_value = True
    mock_exists.return_value = True
    
    # Run function
    process_single_video("http://tiktok.com/video123", "harmful", mock_minio_client, mock_kafka_client)
    
    # Assertions
    # 1. Check Download called
    mock_download.assert_called_once_with("http://tiktok.com/video123")
    
    # 2. Check Extraction called
    mock_extract_audio.assert_called_once()
    
    # 3. Check MinIO Upload called twice (Video + Audio)
    assert mock_minio_client.upload_file.call_count == 2
    mock_minio_client.upload_file.assert_any_call(
        "/tmp/video123.mp4", 
        "raw/harmful/video123.mp4", 
        bucket_name=config.MINIO_BUCKET, 
        content_type="video/mp4"
    )
    
    # 4. Check Kafka sent
    mock_kafka_client.send.assert_called_once()
    call_args = mock_kafka_client.send.call_args[0][0]
    assert call_args["video_id"] == "video123"
    assert call_args["csv_label"] == "harmful"
    assert "clean_text" in call_args
    
    # 5. Check Cleanup
    assert mock_remove.call_count >= 2  # Remove video and audio temp files

@patch("ingestion.main_worker.download_video_to_temp_mobile")
def test_process_single_video_download_fail(mock_download, mock_minio_client, mock_kafka_client):
    """Test flow when download fails"""
    # Setup Mock return None (failure)
    mock_download.return_value = (None, None, None)
    
    process_single_video("http://tiktok.com/fail", "safe", mock_minio_client, mock_kafka_client)
    
    # Assertions
    mock_download.assert_called_once()
    mock_minio_client.upload_file.assert_not_called()
    mock_kafka_client.send.assert_not_called()
