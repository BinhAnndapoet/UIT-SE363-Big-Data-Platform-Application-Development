import pytest
from unittest.mock import patch, MagicMock
from processing.spark_processor import write_to_postgres
import pandas as pd

@patch("processing.spark_processor.log_to_db")
@patch("processing.spark_processor.execute_values")
@patch("processing.spark_processor.psycopg2.connect")
def test_write_to_postgres_upsert(mock_connect, mock_execute_values, mock_log_to_db):
    """Test SQL generation for UPSERT"""
    # Create mock cursor
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor
    
    # Create mock Spark DataFrame
    data = [{
        "video_id": "vid1", "raw_text": "text", "human_label": "safe",
        "text_verdict": "safe", "text_score": 0.1,
        "video_verdict": "safe", "video_score": 0.2,
        "avg_score": 0.15, "threshold": 0.5, "final_decision": "safe"
    }]
    # We mock pandas conversion within script or supply standard DF
    # Since write_to_postgres takes a Spark DataFrame, we need to mock it
    mock_df = MagicMock()
    mock_df.count.return_value = 1
    # Mock collect return list of Rows
    mock_collect = MagicMock()
    # Mock access by key
    mock_row = data[0] # Use dict
    # But spark_processor uses r['key'] access style or r.key ?
    # It uses r['video_id']
    
    mock_df.collect.return_value = [mock_row] # Mock simple dict access
    
    # We need to adjust write_to_postgres to handle dicts if we pass dicts, 
    # but the code expects Spark Row. Let's patch the caching logic to bypass weird spark stuff
    mock_df.select.return_value.persist.return_value = mock_df
    
    # Execute
    write_to_postgres(mock_df, 1)
    
    # Assert
    mock_connect.assert_called_once()
    mock_execute_values.assert_called_once()
    # Check if commit was called
    mock_connect.return_value.commit.assert_called_once()
