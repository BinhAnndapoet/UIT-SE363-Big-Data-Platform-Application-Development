"""
MLflow Model Auto-Updater for Streaming
Check MLflow registry mỗi 30 phút và update models nếu F1-score cao hơn
"""

import os
import sys
import time
import threading
from datetime import datetime

# Import MLflowModelRegistry from same package
# Try relative import first, then absolute
try:
    from .client import MLflowModelRegistry, DEFAULT_F1_THRESHOLDS
except ImportError:
    try:
        # Try direct import (when folder is in sys.path)
        from client import MLflowModelRegistry, DEFAULT_F1_THRESHOLDS
    except ImportError:
        try:
            # If running as script, try adding parent to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from mlflow.client import MLflowModelRegistry, DEFAULT_F1_THRESHOLDS
        except ImportError:
            # Fallback: absolute import from container path
            sys.path.insert(0, '/app/processing')
            from mlflow.client import MLflowModelRegistry, DEFAULT_F1_THRESHOLDS


class ModelAutoUpdater:
    """Auto-update models trong streaming dựa trên F1-score từ MLflow"""
    
    def __init__(
        self,
        tracking_uri: str = None,
        check_interval_minutes: int = 30,
        model_paths: dict = None,
        current_metrics: dict = None,
    ):
        """
        Args:
            tracking_uri: MLflow tracking URI
            check_interval_minutes: Interval để check (default: 30)
            model_paths: Dict {model_type: model_path} của models hiện tại
            current_metrics: Dict {model_type: f1_score} của models hiện tại
        """
        self.registry = MLflowModelRegistry(tracking_uri)
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.model_paths = model_paths or {}
        self.current_metrics = current_metrics or {}
        self.running = False
        self.update_thread = None
    
    def start(self):
        """Start auto-update thread"""
        if self.running:
            print("⚠️ Auto-updater already running")
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print(f"🚀 Model auto-updater started (check interval: {self.check_interval/60:.0f} minutes)")
    
    def stop(self):
        """Stop auto-update thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("🛑 Model auto-updater stopped")
    
    def _update_loop(self):
        """Main loop để check và update models"""
        while self.running:
            try:
                self.check_and_update_models()
            except Exception as e:
                print(f"❌ Error in auto-update loop: {e}")
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def check_and_update_models(self):
        """Check MLflow registry và update models nếu tốt hơn"""
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking MLflow for model updates...")
        
        for model_type, current_f1 in self.current_metrics.items():
            try:
                latest_info = self.registry.get_latest_model_version(model_type)
                
                if not latest_info:
                    print(f"  ⚠️ {model_type}: No model found in registry")
                    continue
                
                new_f1 = latest_info.get("f1_score")
                if new_f1 is None:
                    print(f"  ⚠️ {model_type}: No F1 score found")
                    continue
                
                # Check threshold
                threshold = DEFAULT_F1_THRESHOLDS.get(model_type, 0.70)
                if new_f1 < threshold:
                    print(f"  ⚠️ {model_type}: New F1 ({new_f1:.3f}) < threshold ({threshold:.3f})")
                    continue
                
                # Compare với current
                if new_f1 > current_f1:
                    print(f"  ✅ {model_type}: New model better! F1: {new_f1:.3f} > {current_f1:.3f}")
                    print(f"     Model URI: {latest_info['model_uri']}")
                    print(f"     Version: {latest_info['version']}, Stage: {latest_info['stage']}")
                    
                    # Update model path
                    self._download_and_update_model(model_type, latest_info)
                    
                    # Update current F1
                    self.current_metrics[model_type] = new_f1
                else:
                    print(f"  ℹ️ {model_type}: Current model better. F1: {current_f1:.3f} >= {new_f1:.3f}")
            
            except Exception as e:
                print(f"  ❌ {model_type}: Error checking update: {e}")
        
        print("✅ Model check completed\n")
    
    def _download_and_update_model(self, model_type: str, model_info: dict):
        """Download model từ MLflow và update path"""
        try:
            model_uri = model_info["model_uri"]
            
            # Destination path: /models/{model_type}/mlflow/{model_type}_latest
            dest_path = f"/models/{model_type}/mlflow/{model_type}_latest"
            os.makedirs(dest_path, exist_ok=True)
            
            # Download model từ MLflow
            downloaded_path = self.registry.download_model(
                model_type=model_type,
                stage=model_info["stage"],
                dest_path=dest_path,
            )
            
            if downloaded_path:
                # Update model path
                self.model_paths[model_type] = downloaded_path
                print(f"     ✅ Model downloaded to: {downloaded_path}")
                
                # Signal để reload model (nếu cần)
                # Streaming sẽ tự động detect model path change khi restart
                return True
            else:
                print(f"     ❌ Failed to download model")
                return False
        
        except Exception as e:
            print(f"     ❌ Error downloading model: {e}")
            return False
    
    def get_model_path(self, model_type: str):
        """Get current model path cho model_type"""
        return self.model_paths.get(model_type)
    
    def update_current_metrics(self, metrics: dict):
        """Update current metrics (sau khi test model)"""
        self.current_metrics.update(metrics)


# Global instance (sẽ được init trong streaming)
_model_updater: ModelAutoUpdater = None


def init_model_updater(
    tracking_uri: str = None,
    check_interval_minutes: int = 30,
    model_paths: dict = None,
    current_metrics: dict = None,
):
    """Initialize global model updater"""
    global _model_updater
    _model_updater = ModelAutoUpdater(
        tracking_uri=tracking_uri,
        check_interval_minutes=check_interval_minutes,
        model_paths=model_paths,
        current_metrics=current_metrics,
    )
    return _model_updater


def get_model_updater() -> ModelAutoUpdater:
    """Get global model updater instance"""
    return _model_updater


if __name__ == "__main__":
    # Test auto-updater
    updater = ModelAutoUpdater(
        check_interval_minutes=1,  # Test với 1 phút
        current_metrics={
            "text": 0.80,
            "video": 0.75,
            "fusion": 0.85,
        },
    )
    
    print("Testing model updater (will check once, then exit)...")
    updater.check_and_update_models()
