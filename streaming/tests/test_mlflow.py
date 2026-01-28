"""
MLflow / MLOps Unit Tests
Test MLflow client, model registry, and auto-updater functionality
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the mlflow package before any imports that might use it
# This is necessary because streaming/mlflow shadows the mlflow package
sys.modules["mlflow"] = MagicMock()
sys.modules["mlflow.tracking"] = MagicMock()
sys.modules["mlflow.pytorch"] = MagicMock()


# ============================================================================
# TEST: MLflow Client (Local Module)
# ============================================================================

class TestMLflowClient:
    """Test MLflowModelRegistry class functionality"""
    
    def test_registry_names_defined(self):
        """Test that registry names are properly defined"""
        # Use importlib to import from streaming/mlflow folder to avoid shadowing
        import importlib.util
        client_path = os.path.join(os.path.dirname(__file__), "../mlflow/client.py")
        spec = importlib.util.spec_from_file_location("mlflow_client", client_path)
        mlflow_client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mlflow_client)
        
        REGISTRY_NAMES = mlflow_client.REGISTRY_NAMES
        
        assert "text" in REGISTRY_NAMES
        assert "video" in REGISTRY_NAMES
        assert "fusion" in REGISTRY_NAMES
        assert REGISTRY_NAMES["text"] == "text_classification_model"
    
    def test_default_thresholds_defined(self):
        """Test that default F1 thresholds are defined"""
        import importlib.util
        client_path = os.path.join(os.path.dirname(__file__), "../mlflow/client.py")
        spec = importlib.util.spec_from_file_location("mlflow_client", client_path)
        mlflow_client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mlflow_client)
        
        DEFAULT_F1_THRESHOLDS = mlflow_client.DEFAULT_F1_THRESHOLDS
        
        assert "text" in DEFAULT_F1_THRESHOLDS
        assert "video" in DEFAULT_F1_THRESHOLDS
        assert "fusion" in DEFAULT_F1_THRESHOLDS
        assert DEFAULT_F1_THRESHOLDS["text"] == 0.75
        assert DEFAULT_F1_THRESHOLDS["video"] == 0.70
        assert DEFAULT_F1_THRESHOLDS["fusion"] == 0.80


# ============================================================================
# TEST: Model Auto-Updater
# ============================================================================

class TestModelAutoUpdater:
    """Test ModelAutoUpdater functionality"""
    
    def test_model_updater_file_exists(self):
        """Test that model_updater.py exists"""
        updater_path = os.path.join(os.path.dirname(__file__), "../mlflow/model_updater.py")
        assert os.path.exists(updater_path), "model_updater.py should exist"
    
    def test_model_updater_contains_class(self):
        """Test that ModelAutoUpdater class is defined in the file"""
        updater_path = os.path.join(os.path.dirname(__file__), "../mlflow/model_updater.py")
        with open(updater_path, "r") as f:
            content = f.read()
        
        assert "class ModelAutoUpdater" in content, "ModelAutoUpdater class should be defined"
        assert "def __init__" in content, "__init__ method should exist"
        assert "def start" in content, "start method should exist"
        assert "def stop" in content, "stop method should exist"
        assert "def check_and_update_models" in content, "check_and_update_models method should exist"
    
    def test_model_updater_contains_functions(self):
        """Test that helper functions exist in the file"""
        updater_path = os.path.join(os.path.dirname(__file__), "../mlflow/model_updater.py")
        with open(updater_path, "r") as f:
            content = f.read()
        
        assert "def init_model_updater" in content, "init_model_updater function should exist"
        assert "def get_model_updater" in content, "get_model_updater function should exist"
    
    def test_model_updater_imports(self):
        """Test that model_updater.py has correct imports"""
        updater_path = os.path.join(os.path.dirname(__file__), "../mlflow/model_updater.py")
        with open(updater_path, "r") as f:
            content = f.read()
        
        assert "import threading" in content, "Should import threading for background updates"
        assert "from datetime import datetime" in content, "Should import datetime"


# ============================================================================
# TEST: MLflow Logger (Training Side)
# ============================================================================

class TestMLflowLogger:
    """Test mlflow_logger functions for training scripts"""
    
    def test_logger_functions_exist(self):
        """Test that logger wrapper functions exist"""
        # Add training module to path
        train_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../../train_eval_module"
        ))
        sys.path.insert(0, train_path)
        
        try:
            from shared_utils.mlflow_logger import (
                log_model_to_mlflow,
                log_text_model,
                log_video_model,
                log_fusion_model
            )
            
            assert log_model_to_mlflow is not None
            assert log_text_model is not None
            assert log_video_model is not None
            assert log_fusion_model is not None
        except ImportError as e:
            pytest.skip(f"Could not import mlflow_logger: {e}")


# ============================================================================
# TEST: HuggingFace Hub Integration
# ============================================================================

class TestHuggingFaceHub:
    """Test HuggingFace Hub push functionality"""
    
    def test_push_script_exists(self):
        """Test that push_hf_model.py exists and is importable"""
        push_script_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../../train_eval_module/scripts/push_hf_model.py"
        ))
        
        assert os.path.exists(push_script_path), "push_hf_model.py should exist"
    
    def test_push_script_has_main_functions(self):
        """Test push script has required functions"""
        scripts_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../../train_eval_module/scripts"
        ))
        sys.path.insert(0, scripts_path)
        
        try:
            from push_hf_model import (
                get_available_checkpoints,
                push_text_model,
                push_video_model,
                push_fusion_model,
                interactive_menu
            )
            
            assert get_available_checkpoints is not None
            assert push_text_model is not None
            assert push_video_model is not None
            assert push_fusion_model is not None
        except ImportError as e:
            pytest.skip(f"Could not import push_hf_model: {e}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
