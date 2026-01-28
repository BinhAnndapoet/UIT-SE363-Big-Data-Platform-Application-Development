"""
MLflow Client Utilities - Model Registry & Tracking
Tích hợp MLflow để quản lý models và auto-update trong streaming
"""

import os
import mlflow
import mlflow.pytorch
from mlflow.tracking import MlflowClient
from pathlib import Path
from datetime import datetime
import shutil


# MLflow Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_ARTIFACT_ROOT = os.getenv("MLFLOW_ARTIFACT_ROOT", "file:/mlflow/artifacts")

# Model Registry Names
REGISTRY_NAMES = {
    "text": "text_classification_model",
    "video": "video_classification_model",
    "fusion": "fusion_multimodal_model",
}

# Default F1 thresholds (minimum để consider update)
DEFAULT_F1_THRESHOLDS = {
    "text": 0.75,
    "video": 0.70,
    "fusion": 0.80,
}


class MLflowModelRegistry:
    """MLflow Model Registry Manager cho TikTok Safety Models"""
    
    def __init__(self, tracking_uri=None):
        self.tracking_uri = tracking_uri or MLFLOW_TRACKING_URI
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
    
    def log_model(
        self,
        model_type: str,  # "text", "video", "fusion"
        model_path: str,
        run_name: str,
        metrics: dict,
        params: dict = None,
        tags: dict = None,
    ):
        """
        Log model vào MLflow và register vào Model Registry
        
        Args:
            model_type: Loại model ("text", "video", "fusion")
            model_path: Đường dẫn đến model checkpoint
            run_name: Tên run (e.g., "text_xlm_roberta_20250127")
            metrics: Dict metrics {f1: 0.85, accuracy: 0.90, ...}
            params: Dict hyperparameters
            tags: Dict tags
        """
        registry_name = REGISTRY_NAMES.get(model_type)
        if not registry_name:
            raise ValueError(f"Unknown model_type: {model_type}. Must be one of {list(REGISTRY_NAMES.keys())}")
        
        # Create experiment nếu chưa có
        exp_name = f"tiktok_safety_{model_type}"
        try:
            exp_id = self.client.create_experiment(exp_name)
        except Exception:
            exp = self.client.get_experiment_by_name(exp_name)
            exp_id = exp.experiment_id
        
        mlflow.set_experiment(exp_name)
        
        with mlflow.start_run(run_name=run_name):
            # Log metrics
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
            
            # Log params
            if params:
                for key, value in params.items():
                    mlflow.log_param(key, str(value))
            
            # Log tags
            if tags:
                for key, value in tags.items():
                    mlflow.set_tag(key, str(value))
            
            # Log model (copy vào MLflow artifacts)
            if os.path.isdir(model_path):
                mlflow.pytorch.log_model(
                    pytorch_model=model_path,
                    artifact_path="model",
                    registered_model_name=registry_name,
                )
                print(f"✅ Model logged to MLflow: {registry_name} | Run: {run_name} | F1: {metrics.get('eval_f1', 'N/A')}")
            else:
                print(f"⚠️ Model path not found: {model_path}")
    
    def get_latest_model_version(self, model_type: str):
        """
        Lấy version mới nhất của model từ registry
        
        Returns:
            dict với keys: version, stage, f1_score, model_uri
        """
        registry_name = REGISTRY_NAMES.get(model_type)
        if not registry_name:
            return None
        
        try:
            # Lấy latest version từ Production stage
            latest_versions = self.client.get_latest_versions(
                registry_name,
                stages=["Production", "Staging", "None"],
            )
            
            if not latest_versions:
                return None
            
            # Sort theo version number (descending)
            latest = max(latest_versions, key=lambda v: v.version)
            
            # Lấy F1 score từ run
            run = self.client.get_run(latest.run_id)
            f1_score = None
            for metric in run.data.metrics:
                if "f1" in metric.lower():
                    f1_score = run.data.metrics.get(metric)
                    break
            
            return {
                "version": latest.version,
                "stage": latest.current_stage,
                "f1_score": f1_score,
                "model_uri": f"models:/{registry_name}/{latest.current_stage}",
                "run_id": latest.run_id,
                "timestamp": latest.last_updated_timestamp,
            }
        except Exception as e:
            print(f"⚠️ Error getting latest model version: {e}")
            return None
    
    def compare_and_update_model(
        self,
        model_type: str,
        current_f1: float,
        new_model_path: str,
        min_f1_threshold: float = None,
    ):
        """
        So sánh F1 score và update model nếu tốt hơn
        
        Args:
            model_type: "text", "video", "fusion"
            current_f1: F1 score của model hiện tại trong streaming
            new_model_path: Đường dẫn đến model mới
            min_f1_threshold: Minimum F1 để consider update (default: theo DEFAULT_F1_THRESHOLDS)
        
        Returns:
            bool: True nếu nên update, False nếu không
        """
        latest_info = self.get_latest_model_version(model_type)
        
        if not latest_info:
            print(f"⚠️ No model found in registry for {model_type}, cannot compare")
            return False
        
        new_f1 = latest_info.get("f1_score")
        if new_f1 is None:
            print(f"⚠️ No F1 score found for latest model {model_type}")
            return False
        
        # Check threshold
        threshold = min_f1_threshold or DEFAULT_F1_THRESHOLDS.get(model_type, 0.70)
        if new_f1 < threshold:
            print(f"⚠️ New F1 ({new_f1:.3f}) < threshold ({threshold:.3f}), skip update")
            return False
        
        # Compare với current
        if new_f1 > current_f1:
            print(f"✅ New model better! F1: {new_f1:.3f} > {current_f1:.3f}")
            return True
        else:
            print(f"ℹ️ Current model is better. F1: {current_f1:.3f} >= {new_f1:.3f}")
            return False
    
    def download_model(self, model_type: str, stage: str = "Production", dest_path: str = None):
        """
        Download model từ MLflow registry về local path
        
        Args:
            model_type: "text", "video", "fusion"
            stage: "Production", "Staging", "None"
            dest_path: Đường dẫn đích (nếu None, dùng default trong /models)
        
        Returns:
            str: Đường dẫn đến model đã download
        """
        registry_name = REGISTRY_NAMES.get(model_type)
        if not registry_name:
            return None
        
        try:
            model_uri = f"models:/{registry_name}/{stage}"
            
            if dest_path is None:
                # Default: /models/{model_type}/mlflow/{model_type}_latest
                dest_path = f"/models/{model_type}/mlflow/{model_type}_latest"
            
            os.makedirs(dest_path, exist_ok=True)
            
            # Download model
            mlflow.pytorch.load_model(model_uri, dst_path=dest_path)
            
            print(f"✅ Model downloaded: {model_uri} -> {dest_path}")
            return dest_path
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            return None


def check_and_update_models(current_metrics: dict, check_interval_minutes: int = 30):
    """
    Check MLflow registry mỗi N phút và update models nếu tốt hơn
    
    Args:
        current_metrics: Dict {model_type: f1_score} của models hiện tại
        check_interval_minutes: Interval để check (default: 30)
    
    Returns:
        dict: Models cần update {model_type: model_uri}
    """
    registry = MLflowModelRegistry()
    models_to_update = {}
    
    for model_type, current_f1 in current_metrics.items():
        should_update = registry.compare_and_update_model(
            model_type=model_type,
            current_f1=current_f1,
            new_model_path=None,  # Không cần path khi chỉ check
        )
        
        if should_update:
            latest_info = registry.get_latest_model_version(model_type)
            models_to_update[model_type] = latest_info.get("model_uri")
    
    return models_to_update


if __name__ == "__main__":
    # Test MLflow connection
    registry = MLflowModelRegistry()
    print(f"✅ MLflow connected to: {MLFLOW_TRACKING_URI}")
    
    # Test get latest models
    for model_type in ["text", "video", "fusion"]:
        latest = registry.get_latest_model_version(model_type)
        if latest:
            print(f"{model_type}: version={latest['version']}, F1={latest['f1_score']}, stage={latest['stage']}")
        else:
            print(f"{model_type}: No model found in registry")
