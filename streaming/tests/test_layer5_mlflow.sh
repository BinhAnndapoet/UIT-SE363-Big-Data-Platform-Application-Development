#!/bin/bash

# =============================================================================
# TEST LAYER 5: MLflow Model Registry & Experiment Tracking
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RUNNING: Layer 5 - MLflow Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Setup colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Check MLflow Service Health
echo "▶ MLFLOW SERVICE HEALTH"
if curl -s http://localhost:5000/health > /dev/null; then
    echo -e "${GREEN}✅ PASS: MLflow service reachable at http://localhost:5000${NC}"
else
    # Fallback check for root endpoint
    if curl -s http://localhost:5000 > /dev/null; then
        echo -e "${GREEN}✅ PASS: MLflow service reachable at http://localhost:5000${NC}"
    else
        echo -e "${RED}❌ FAIL: MLflow service NOT reachable${NC}"
        echo "   (Make sure 'mlflow' container is running and port 5000 is mapped)"
        exit 1
    fi
fi

# 2. Run Python Unit Tests (Mocks)
echo ""
echo "▶ UNIT TESTS (Mocked)"
cd "$(dirname "$0")/.." || exit
export PYTHONPATH=$PYTHONPATH:$(pwd)

if pytest tests/test_mlflow.py -v; then
    echo -e "${GREEN}✅ PASS: Python Mock Tests passed${NC}"
else
    echo -e "${RED}❌ FAIL: Python Mock Tests failed${NC}"
    exit 1
fi

# 3. Functional Test: Log Dummy Experiment
echo ""
echo "▶ FUNCTIONAL TEST (Real Logging)"
# Create a temporary python script to test logging
cat <<EOF > tests/temp_mlflow_check.py
import mlflow
import os
import sys

# Connect to MLflow (Container uses http://mlflow:5000 not localhost)
MLFLOW_TRACKING_URI = "http://mlflow:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print(f"Connecting to {MLFLOW_TRACKING_URI}...")

try:
    # 1. Test Connection
    experiments = mlflow.search_experiments()
    print(f"Connection OK. Found {len(experiments)} experiments.")
    
    # 2. Test Logging
    import time
    timestamp = int(time.time())
    experiment_name = f"test_layer5_validation_{timestamp}"
    try:
        exp_id = mlflow.create_experiment(experiment_name)
    except:
        exp_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
    
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name="validation_run"):
        mlflow.log_param("test_param", "layer5_check")
        mlflow.log_metric("test_metric", 1.0)
        print("Logged param and metric successfully.")
        
    print("SUCCESS")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
EOF

# Run the python script INSIDE spark-processor container (which has mlflow installed)
# Copy script to container
docker cp tests/temp_mlflow_check.py spark-processor:/tmp/temp_mlflow_check.py

# Execute in container
if docker exec spark-processor python3 /tmp/temp_mlflow_check.py; then
    echo -e "${GREEN}✅ PASS: Functional Logging Test passed${NC}"
else
    echo -e "${RED}❌ FAIL: Functional Logging Test failed${NC}"
    rm tests/temp_mlflow_check.py
    exit 1
fi

# Cleanup
rm tests/temp_mlflow_check.py

echo ""
echo -e "${GREEN}🎉 LAYER 5 TESTS PASSED!${NC}"
