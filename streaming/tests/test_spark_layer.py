import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock pyspark modules BEFORE importing spark_processor
# because spark_processor imports them at top level
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
sys.modules["safetensors.torch"] = MagicMock() # Mock safetensors

# Now import the logic functions to test
from processing.spark_processor import process_text_logic, process_video_logic, process_fusion_logic

# --- TEST TEXT LOGIC ---
@patch("processing.spark_processor.get_text_model")
def test_process_text_logic_blacklist(mock_get_model):
    """Test rule-based blacklist detection"""
    # Should catch "đánh nhau" (blacklist)
    result = process_text_logic("hôm nay có vụ đánh nhau to")
    assert result["verdict"] == "harmful"
    assert result["risk_score"] == 0.85
    # Should NOT call AI model
    mock_get_model.assert_not_called()

@patch("processing.spark_processor.get_text_model")
def test_process_text_logic_ai_safe(mock_get_model):
    """Test AI model prediction (Safe)"""
    # Mock model output
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()
    mock_get_model.return_value = (mock_tokenizer, mock_model)
    
    # Mock torch.nn.functional.softmax return value
    # Needs to support probs[0][1].item()
    mock_tensor = MagicMock()
    mock_tensor[0][1].item.return_value = 0.1 # Return 0.1 (Safe)
    
    with patch("processing.spark_processor.torch.nn.functional.softmax") as mock_softmax:
        mock_softmax.return_value = mock_tensor
        
        with patch("processing.spark_processor.torch.no_grad"):
             result = process_text_logic("hôm nay trời đẹp")
             
    assert result["verdict"] == "safe"
    assert result["risk_score"] == 0.1

# --- TEST VIDEO LOGIC ---
@patch("processing.spark_processor.get_video_model")
@patch("processing.spark_processor.boto3.client")
@patch("processing.spark_processor.VideoReader")
@patch("processing.spark_processor.os.remove")
def test_process_video_logic_success(mock_remove, mock_vr, mock_boto, mock_get_model):
    """Test video processing logic"""
    # Mock S3 download
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    
    # Mock Video Reader
    mock_vr_instance = MagicMock()
    mock_vr_instance.__len__.return_value = 100
    mock_vr.return_value = mock_vr_instance
    
    # Mock Model
    mock_proc = MagicMock()
    mock_model = MagicMock()
    mock_get_model.return_value = (mock_proc, mock_model)
    
    mock_tensor = MagicMock()
    mock_tensor[0][1].item.return_value = 0.9 # Harmful
    
    with patch("processing.spark_processor.torch.nn.functional.softmax") as mock_softmax:
        mock_softmax.return_value = mock_tensor
        
        with patch("processing.spark_processor.torch.no_grad"):
             result = process_video_logic("vid1", "bucket/vid1.mp4")
    
    assert result["verdict"] == "harmful"
    assert result["risk_score"] == 0.9
    
# --- TEST FUSION LOGIC ---
def test_process_fusion_logic_missing_data():
    """Test fusion logic with missing data"""
    result = process_fusion_logic("vid1", None, "some text")
    assert result["verdict"] == "MissingData"
    
    result = process_fusion_logic("vid1", "path", None)
    assert result["verdict"] == "MissingData"
