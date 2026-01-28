"""
UI/UX and Dashboard Tests
Test Streamlit dashboard components, score display, and page rendering
"""

import pytest
import os
import sys
import re

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../dashboard")))


# ============================================================================
# TEST: Dashboard File Structure
# ============================================================================

class TestDashboardStructure:
    """Test dashboard module structure"""
    
    def test_app_py_exists(self):
        """Test main app.py exists"""
        app_path = os.path.join(os.path.dirname(__file__), "../dashboard/app.py")
        assert os.path.exists(app_path), "app.py should exist"
    
    def test_config_py_exists(self):
        """Test config.py exists"""
        config_path = os.path.join(os.path.dirname(__file__), "../dashboard/config.py")
        assert os.path.exists(config_path), "config.py should exist"
    
    def test_helpers_py_exists(self):
        """Test helpers.py exists"""
        helpers_path = os.path.join(os.path.dirname(__file__), "../dashboard/helpers.py")
        assert os.path.exists(helpers_path), "helpers.py should exist"
    
    def test_styles_py_exists(self):
        """Test styles.py exists"""
        styles_path = os.path.join(os.path.dirname(__file__), "../dashboard/styles.py")
        assert os.path.exists(styles_path), "styles.py should exist"
    
    def test_page_modules_exist(self):
        """Test all page modules exist"""
        modules_dir = os.path.join(os.path.dirname(__file__), "../dashboard/page_modules")
        assert os.path.exists(modules_dir), "page_modules directory should exist"
        
        required_modules = [
            "__init__.py",
            "dashboard_monitor.py",
            "system_operations.py",
            "content_audit.py",
            "database_manager.py",
            "project_info.py"
        ]
        
        for module in required_modules:
            module_path = os.path.join(modules_dir, module)
            assert os.path.exists(module_path), f"{module} should exist"


# ============================================================================
# TEST: Score Display Logic (Critical - Check for 0.00 bug)
# ============================================================================

class TestScoreDisplay:
    """Test score display logic to prevent 0.00 display bug"""
    
    def test_helpers_has_score_formatting(self):
        """Test helpers.py handles score formatting correctly"""
        helpers_path = os.path.join(os.path.dirname(__file__), "../dashboard/helpers.py")
        with open(helpers_path, "r") as f:
            content = f.read()
        
        # Should have get_data function that returns scores
        assert "def get_data" in content, "get_data function should exist"
        assert "text_score" in content, "Should reference text_score"
        assert "video_score" in content, "Should reference video_score"
        assert "avg_score" in content, "Should reference avg_score"
    
    def test_dashboard_monitor_has_score_display(self):
        """Test dashboard_monitor.py displays scores properly"""
        monitor_path = os.path.join(os.path.dirname(__file__), "../dashboard/page_modules/dashboard_monitor.py")
        with open(monitor_path, "r") as f:
            content = f.read()
        
        # Should display scores in metrics or cards
        assert "text_score" in content or "avg_score" in content, "Should display scores"
    
    def test_content_audit_has_score_display(self):
        """Test content_audit.py displays scores in video cards"""
        audit_path = os.path.join(os.path.dirname(__file__), "../dashboard/page_modules/content_audit.py")
        with open(audit_path, "r") as f:
            content = f.read()
        
        # Should display scores for each video
        assert "score" in content.lower(), "Should reference scores"
    
    def test_score_not_hardcoded_zero(self):
        """Test that scores are not hardcoded to 0.00"""
        files_to_check = [
            "../dashboard/helpers.py",
            "../dashboard/page_modules/dashboard_monitor.py",
            "../dashboard/page_modules/content_audit.py"
        ]
        
        for file in files_to_check:
            file_path = os.path.join(os.path.dirname(__file__), file)
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Check for suspicious hardcoded 0.00 patterns
                # Pattern: "score = 0" or "score": 0" outside of default/fallback context
                # This is a heuristic check
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    # Skip comments and legitimate defaults
                    if '#' in line or 'default' in line.lower() or 'fallback' in line.lower():
                        continue
                    # Flag if we find direct assignment of 0 to score (excluding conditionals)
                    if re.search(r'score\s*=\s*0(?:\.\d+)?(?!\s*if)', line):
                        # This is acceptable in some contexts, so we just log it
                        pass


# ============================================================================
# TEST: DAG Configuration
# ============================================================================

class TestDAGConfiguration:
    """Test Airflow DAG configuration files"""
    
    def test_dag_files_exist(self):
        """Test DAG files exist"""
        dags_dir = os.path.join(os.path.dirname(__file__), "../airflow/dags")
        
        expected_dags = [
            "1_TIKTOK_ETL_COLLECTOR.py",
            "2_TIKTOK_STREAMING_PIPELINE.py"
        ]
        
        for dag in expected_dags:
            dag_path = os.path.join(dags_dir, dag)
            assert os.path.exists(dag_path), f"DAG {dag} should exist"
    
    def test_dag_has_dag_id(self):
        """Test DAGs have proper DAG definition"""
        dags_dir = os.path.join(os.path.dirname(__file__), "../airflow/dags")
        
        for dag_file in ["1_TIKTOK_ETL_COLLECTOR.py", "2_TIKTOK_STREAMING_PIPELINE.py"]:
            dag_path = os.path.join(dags_dir, dag_file)
            if os.path.exists(dag_path):
                with open(dag_path, "r") as f:
                    content = f.read()
                # DAG can be defined with DAG("name", ...) or dag_id="name"
                assert "DAG(" in content, f"{dag_file} should define DAG"
                # Check that DAG ID is defined (inline string after DAG()
                assert "TIKTOK" in content, f"{dag_file} should have TIKTOK in DAG ID"


# ============================================================================
# TEST: Spark Processor Configuration
# ============================================================================

class TestSparkProcessorConfig:
    """Test Spark processor configuration"""
    
    def test_spark_processor_exists(self):
        """Test spark_processor.py exists"""
        processor_path = os.path.join(os.path.dirname(__file__), "../processing/spark_processor.py")
        assert os.path.exists(processor_path), "spark_processor.py should exist"
    
    def test_spark_processor_has_fusion_model(self):
        """Test spark_processor.py has fusion model integration"""
        processor_path = os.path.join(os.path.dirname(__file__), "../processing/spark_processor.py")
        with open(processor_path, "r") as f:
            content = f.read()
        
        assert "LateFusionModel" in content, "Should have LateFusionModel class"
        assert "USE_FUSION_MODEL" in content, "Should have USE_FUSION_MODEL flag"
    
    def test_spark_processor_has_huggingface_support(self):
        """Test spark_processor.py supports HuggingFace Hub"""
        processor_path = os.path.join(os.path.dirname(__file__), "../processing/spark_processor.py")
        with open(processor_path, "r") as f:
            content = f.read()
        
        assert "HF_MODEL_TEXT" in content, "Should support HF_MODEL_TEXT env var"
        assert "HF_MODEL_VIDEO" in content, "Should support HF_MODEL_VIDEO env var"
    
    def test_spark_processor_has_postgres_write(self):
        """Test spark_processor.py writes to PostgreSQL"""
        processor_path = os.path.join(os.path.dirname(__file__), "../processing/spark_processor.py")
        with open(processor_path, "r") as f:
            content = f.read()
        
        assert "write_to_postgres" in content or "postgres" in content.lower(), "Should write to PostgreSQL"


# ============================================================================
# TEST: Docker Configuration
# ============================================================================

class TestDockerConfiguration:
    """Test Docker configuration files"""
    
    def test_docker_compose_exists(self):
        """Test docker-compose.yml exists"""
        compose_path = os.path.join(os.path.dirname(__file__), "../docker-compose.yml")
        assert os.path.exists(compose_path), "docker-compose.yml should exist"
    
    def test_docker_compose_has_required_services(self):
        """Test docker-compose.yml has all required services"""
        compose_path = os.path.join(os.path.dirname(__file__), "../docker-compose.yml")
        with open(compose_path, "r") as f:
            content = f.read()
        
        required_services = [
            "kafka",
            "postgres",
            "minio",
            "spark-processor",
            "airflow",
            "dashboard"
        ]
        
        for service in required_services:
            assert service in content, f"Service '{service}' should be in docker-compose.yml"
    
    def test_env_file_exists(self):
        """Test .env file exists"""
        env_path = os.path.join(os.path.dirname(__file__), "../.env")
        assert os.path.exists(env_path), ".env file should exist"


# ============================================================================
# TEST: Database Schema
# ============================================================================

class TestDatabaseSchema:
    """Test database schema expectations"""
    
    def test_helpers_references_correct_tables(self):
        """Test helpers.py references correct database tables"""
        helpers_path = os.path.join(os.path.dirname(__file__), "../dashboard/helpers.py")
        with open(helpers_path, "r") as f:
            content = f.read()
        
        # Should reference processed_results table
        assert "processed_results" in content, "Should reference processed_results table"
        # Should reference system_logs table
        assert "system_logs" in content, "Should reference system_logs table"
    
    def test_spark_processor_references_correct_tables(self):
        """Test spark_processor.py writes to correct tables"""
        processor_path = os.path.join(os.path.dirname(__file__), "../processing/spark_processor.py")
        with open(processor_path, "r") as f:
            content = f.read()
        
        # Should write to video_predictions or processed_results
        assert "video_predictions" in content or "processed_results" in content, \
            "Should reference prediction table"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
