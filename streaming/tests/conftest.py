import pytest
import os
import sys
from unittest.mock import MagicMock

# Add streaming directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ingestion")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../processing")))

# Mock external modules BEFORE they are imported by app code during collection
sys.modules["minio"] = MagicMock()
mock_kafka = MagicMock()
sys.modules["kafka"] = mock_kafka
sys.modules["kafka.admin"] = MagicMock()
sys.modules["selenium"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()

# Mock Spark & AI libs
sys.modules["pyspark"] = MagicMock()
sys.modules["pyspark.sql"] = MagicMock()
sys.modules["pyspark.sql.functions"] = MagicMock()
sys.modules["pyspark.sql.types"] = MagicMock()
sys.modules["boto3"] = MagicMock()
mock_torch = MagicMock()
sys.modules["torch"] = mock_torch
sys.modules["torch.nn"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["decord"] = MagicMock()
sys.modules["safetensors"] = MagicMock()
sys.modules["safetensors.torch"] = MagicMock()

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set default environment variables for testing"""
    monkeypatch.setenv("MINIO_ENDPOINT", "http://mock-minio:9000")
    monkeypatch.setenv("MINIO_ROOT_USER", "admin")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "password123")
    monkeypatch.setenv("MINIO_BUCKET", "tiktok-raw-videos")
    monkeypatch.setenv("MINIO_AUDIO_BUCKET", "tiktok-raw-audios")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    monkeypatch.setenv("KAFKA_TOPIC", "tiktok_raw_data")
    monkeypatch.setenv("INPUT_CSV_PATH", "mock_data.csv")
    monkeypatch.setenv("TEMP_DOWNLOAD_DIR", "/tmp/mock_downloads")
    # For Spark
    monkeypatch.setenv("TEXT_WEIGHT", "0.3")
    monkeypatch.setenv("DECISION_THRESHOLD", "0.5")

@pytest.fixture
def mock_minio_client():
    """Mock MinIO Client"""
    mock = MagicMock()
    mock.upload_file.return_value = "raw/mock/video.mp4"
    return mock

@pytest.fixture
def mock_kafka_client():
    """Mock Kafka Client"""
    mock = MagicMock()
    return mock
