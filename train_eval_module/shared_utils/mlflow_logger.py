"""
MLflow Logger for Training Scripts
Wrapper để log models và metrics vào MLflow sau khi training xong
"""

import os
import sys
import mlflow
import mlflow.pytorch
from datetime import datetime
from pathlib import Path


# MLflow Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


def log_model_to_mlflow(
    model_type: str,  # "text", "video", "fusion", "audio"
    model_path: str,
    metrics: dict,
    params: dict = None,
    tags: dict = None,
    experiment_name: str = None,
):
    """
    Log model vào MLflow sau khi training xong
    
    Args:
        model_type: Loại model ("text", "video", "fusion", "audio")
        model_path: Đường dẫn đến best_checkpoint
        metrics: Dict metrics {eval_f1: 0.85, eval_accuracy: 0.90, ...}
        params: Dict hyperparameters
        tags: Dict tags {model_name: "xlm-roberta-base", ...}
        experiment_name: Tên experiment (nếu None, dùng default)
    """
    try:
        # Set tracking URI
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        # Experiment name
        if experiment_name is None:
            experiment_name = f"tiktok_safety_{model_type}"
        
        # Create experiment nếu chưa có
        try:
            exp_id = mlflow.create_experiment(experiment_name)
        except Exception:
            exp = mlflow.get_experiment_by_name(experiment_name)
            exp_id = exp.experiment_id if exp else None
        
        mlflow.set_experiment(experiment_name)
        
        # Run name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = tags.get("model_name", model_type) if tags else model_type
        run_name = f"{model_type}_{model_name}_{timestamp}"
        
        with mlflow.start_run(run_name=run_name):
            # Log metrics
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    mlflow.log_metric(key, value)
            
            # Log params
            if params:
                for key, value in params.items():
                    mlflow.log_param(key, str(value))
            
            # Log tags
            if tags:
                for key, value in tags.items():
                    mlflow.set_tag(key, str(value))
            
            # Log model
            if os.path.isdir(model_path):
                mlflow.pytorch.log_model(
                    pytorch_model=model_path,
                    artifact_path="model",
                    registered_model_name=f"{model_type}_classification_model",
                )
                print(f"✅ Model logged to MLflow: {run_name}")
                print(f"   Tracking URI: {MLFLOW_TRACKING_URI}")
                print(f"   Experiment: {experiment_name}")
                print(f"   Metrics: {metrics}")
                return True
            else:
                print(f"⚠️ Model path not found: {model_path}")
                return False
    
    except Exception as e:
        print(f"❌ Error logging to MLflow: {e}")
        return False


def log_text_model(model_path: str, metrics: dict, params: dict = None, model_name: str = None):
    """Wrapper để log text model"""
    tags = {"model_name": model_name} if model_name else None
    return log_model_to_mlflow(
        model_type="text",
        model_path=model_path,
        metrics=metrics,
        params=params,
        tags=tags,
    )


def log_video_model(model_path: str, metrics: dict, params: dict = None, model_name: str = None):
    """Wrapper để log video model"""
    tags = {"model_name": model_name} if model_name else None
    return log_model_to_mlflow(
        model_type="video",
        model_path=model_path,
        metrics=metrics,
        params=params,
        tags=tags,
    )


def log_fusion_model(model_path: str, metrics: dict, params: dict = None):
    """Wrapper để log fusion model"""
    return log_model_to_mlflow(
        model_type="fusion",
        model_path=model_path,
        metrics=metrics,
        params=params,
        tags={"model_name": "late_fusion_videomae"},
    )


if __name__ == "__main__":
    # Test MLflow connection
    print(f"Testing MLflow connection to: {MLFLOW_TRACKING_URI}")
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        experiments = mlflow.search_experiments()
        print(f"✅ Connected! Found {len(experiments)} experiments")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
