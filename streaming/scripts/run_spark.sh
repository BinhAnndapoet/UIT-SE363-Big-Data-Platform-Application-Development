#!/bin/bash
# ============================================================================
# Layer 2: SPARK PROCESSING LAYER - Run Script
# ============================================================================
# Purpose: Test or run the Spark processing layer
# Components: Text Classification, Video Classification, Fusion Model, PostgreSQL
#
# Usage:
#   ./scripts/run_spark.sh [mode]
#
# Modes:
#   test      - Run unit tests for Spark layer
#   local     - Run spark_processor.py locally (for development)
#   docker    - Run via Docker Compose (production)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(dirname "$SCRIPT_DIR")"
PROCESSING_DIR="$STREAMING_DIR/processing"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment
if [ -f "$STREAMING_DIR/.env" ]; then
    set -a
    source "$STREAMING_DIR/.env"
    set +a
fi

print_header() {
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}  SPARK PROCESSING LAYER - $1${NC}"
    echo -e "${GREEN}============================================================================${NC}"
}

run_tests() {
    print_header "UNIT TESTS"
    cd "$STREAMING_DIR"
    
    echo "Running Spark layer tests..."
    pytest tests/test_spark_layer.py -v --tb=short
    
    echo -e "${GREEN}✅ Spark tests completed!${NC}"
}

run_local() {
    print_header "LOCAL DEVELOPMENT"
    
    echo -e "${YELLOW}⚠️  Running Spark locally requires:${NC}"
    echo "   - Java 8/11 installed"
    echo "   - Spark 3.5+ installed"
    echo "   - Kafka, MinIO, Postgres running"
    echo ""
    
    # Check Kafka
    if ! docker ps | grep -q kafka; then
        echo -e "${RED}❌ Kafka not running!${NC}"
        exit 1
    fi
    
    cd "$PROCESSING_DIR"
    
    echo "🚀 Starting spark_processor.py..."
    spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
        spark_processor.py
}

run_docker() {
    print_header "DOCKER MODE"
    cd "$STREAMING_DIR"
    
    echo "🐳 Starting Spark processor via Docker Compose..."
    docker compose up spark-processor -d
    
    echo ""
    echo "📋 View logs: docker logs -f spark-processor"
    echo "🛑 Stop:      docker compose stop spark-processor"
}

show_help() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  test      Run unit tests for Spark layer"
    echo "  local     Run spark_processor.py locally (requires Spark installation)"
    echo "  docker    Run via Docker Compose (recommended)"
    echo ""
    echo "Configuration (in .env):"
    echo "  USE_FUSION_MODEL        true/false - Enable fusion model"
    echo "  TEXT_WEIGHT             0.0-1.0 - Weight for text classification"
    echo "  DECISION_THRESHOLD      0.0-1.0 - Threshold for harmful decision"
    echo "  HF_MODEL_TEXT           HuggingFace model ID (optional)"
    echo "  HF_MODEL_VIDEO          HuggingFace model ID (optional)"
}

# Main
case "${1:-test}" in
    test)
        run_tests
        ;;
    local)
        run_local
        ;;
    docker)
        run_docker
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown mode: $1${NC}"
        show_help
        exit 1
        ;;
esac
