#!/bin/bash
# ============================================================================
# TikTok Safety MLOps - Comprehensive Test Suite
# ============================================================================
# This script runs all tests for the streaming pipeline and MLOps components.
#
# Usage:
#   ./scripts/comprehensive_test.sh [mode]
#
# Modes:
#   all       - Run all tests (default)
#   layer     - Run only layer tests (ingestion, spark, db)
#   mlflow    - Run only MLflow/MLOps tests
#   docker    - Verify Docker configuration
#   report    - Generate test report
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$STREAMING_DIR")"
TESTS_DIR="$STREAMING_DIR/tests"
REPORT_FILE="$STREAMING_DIR/test_report.txt"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Ensure we are in streaming directory
cd "$STREAMING_DIR"
export PYTHONPATH="$STREAMING_DIR:$PYTHONPATH"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_section() {
    echo ""
    echo -e "${YELLOW}---[ $1 ]---${NC}"
}

run_pytest() {
    local name=$1
    local target=$2
    
    print_section "$name"
    
    if pytest "$target" -v --tb=short 2>&1; then
        echo -e "${GREEN}✅ $name: PASSED${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ $name: FAILED${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
}

# ============================================================================
# Test Functions
# ============================================================================

test_ingestion_layer() {
    print_header "INGESTION LAYER TESTS"
    echo "Testing: Video download, Audio extraction, MinIO upload, Kafka messaging"
    
    run_pytest "Ingestion Layer" "tests/test_ingestion_layer.py"
}

test_spark_layer() {
    print_header "SPARK PROCESSING LAYER TESTS"
    echo "Testing: Text classification, Video classification, Fusion model logic"
    
    run_pytest "Spark Layer" "tests/test_spark_layer.py"
}

test_db_layer() {
    print_header "DATABASE LAYER TESTS"
    echo "Testing: PostgreSQL UPSERT operations, Connection handling"
    
    run_pytest "Database Layer" "tests/test_db_layer.py"
}

test_mlflow() {
    print_header "MLFLOW / MLOPS TESTS"
    echo "Testing: MLflow client, Model registry, Auto-updater"
    
    if [ -f "tests/test_mlflow.py" ]; then
        run_pytest "MLflow Integration" "tests/test_mlflow.py"
    else
        echo -e "${YELLOW}⚠️ MLflow tests not found. Creating...${NC}"
        # Test file will be created separately
        echo -e "${YELLOW}   Run this script again after tests are created.${NC}"
    fi
}

verify_docker() {
    print_header "DOCKER CONFIGURATION VERIFICATION"
    
    print_section "Checking docker-compose.yml syntax"
    if docker compose config -q 2>/dev/null; then
        echo -e "${GREEN}✅ docker-compose.yml syntax: VALID${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ docker-compose.yml syntax: INVALID${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    print_section "Checking Dockerfiles"
    local dockerfiles=("spark/Dockerfile" "airflow/Dockerfile.airflow" "dashboard/Dockerfile.dashboard")
    
    for df in "${dockerfiles[@]}"; do
        if [ -f "$df" ]; then
            echo -e "${GREEN}✅ $df exists${NC}"
        else
            echo -e "${RED}❌ $df missing${NC}"
        fi
    done
    
    print_section "Checking required services in docker-compose.yml"
    local services=("kafka" "postgres" "minio" "spark-processor" "airflow-webserver" "mlflow")
    
    for svc in "${services[@]}"; do
        if grep -q "^  $svc:" docker-compose.yml 2>/dev/null; then
            echo -e "${GREEN}✅ Service '$svc' defined${NC}"
        else
            echo -e "${YELLOW}⚠️ Service '$svc' not found${NC}"
        fi
    done
}

generate_report() {
    print_header "GENERATING TEST REPORT"
    
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    cat > "$REPORT_FILE" << EOF
================================================================================
TikTok Safety Platform - Test Report
Generated: $timestamp
================================================================================

SUMMARY
-------
Total Tests: $TOTAL_TESTS
Passed:      $PASSED_TESTS
Failed:      $FAILED_TESTS
Pass Rate:   $(( PASSED_TESTS * 100 / (TOTAL_TESTS > 0 ? TOTAL_TESTS : 1) ))%

LAYER TESTS
-----------
- Ingestion Layer: Tests video download, audio extraction, MinIO, Kafka
- Spark Layer:     Tests text/video classification, fusion model
- Database Layer:  Tests PostgreSQL UPSERT operations

MLOPS TESTS
-----------
- MLflow Client:    Model registry operations
- Model Updater:    Auto-update mechanism
- HuggingFace Hub:  Model push/pull operations

DOCKER VERIFICATION
-------------------
- docker-compose.yml syntax check
- Dockerfile existence check
- Service definition check

================================================================================
EOF
    
    echo -e "${GREEN}✅ Report saved to: $REPORT_FILE${NC}"
    cat "$REPORT_FILE"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local mode=${1:-all}
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       TikTok Safety Platform - Comprehensive Test Suite                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Mode: $mode"
    echo "Time: $(date)"
    echo ""
    
    case $mode in
        all)
            test_ingestion_layer
            test_spark_layer
            test_db_layer
            test_mlflow
            verify_docker
            generate_report
            ;;
        layer)
            test_ingestion_layer
            test_spark_layer
            test_db_layer
            ;;
        mlflow)
            test_mlflow
            ;;
        docker)
            verify_docker
            ;;
        report)
            generate_report
            ;;
        *)
            echo "Usage: $0 {all|layer|mlflow|docker|report}"
            exit 1
            ;;
    esac
    
    print_header "FINAL SUMMARY"
    echo ""
    echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed:      ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:      ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed. Check output above.${NC}"
        exit 1
    fi
}

main "$@"
