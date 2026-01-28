#!/bin/bash
# ============================================================================
# Layer 1: INGESTION LAYER - Run Script
# ============================================================================
# Purpose: Test or run the ingestion layer (crawler, downloader, main_worker)
# Components: TikTok Crawler, Video Downloader, Audio Extractor, MinIO Upload
#
# Usage:
#   ./scripts/run_ingestion.sh [mode]
#
# Modes:
#   test      - Run unit tests for ingestion layer
#   worker    - Run main_worker.py directly (requires Kafka, MinIO running)
#   crawler   - Run crawler.py to collect TikTok links
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(dirname "$SCRIPT_DIR")"
INGESTION_DIR="$STREAMING_DIR/ingestion"

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
    echo -e "${GREEN}  INGESTION LAYER - $1${NC}"
    echo -e "${GREEN}============================================================================${NC}"
}

run_tests() {
    print_header "UNIT TESTS"
    cd "$STREAMING_DIR"
    
    echo "Running ingestion layer tests..."
    pytest tests/test_ingestion_layer.py -v --tb=short
    
    echo -e "${GREEN}✅ Ingestion tests completed!${NC}"
}

run_worker() {
    print_header "MAIN WORKER"
    cd "$INGESTION_DIR"
    
    echo "📁 Input CSV: $INPUT_CSV_PATH"
    echo "📡 Kafka: $KAFKA_BOOTSTRAP_SERVERS"
    echo "📦 MinIO: $MINIO_ENDPOINT"
    echo ""
    
    # Check dependencies
    if ! docker ps | grep -q kafka; then
        echo -e "${RED}❌ Kafka is not running! Start with: docker compose up kafka -d${NC}"
        exit 1
    fi
    
    if ! docker ps | grep -q minio; then
        echo -e "${RED}❌ MinIO is not running! Start with: docker compose up minio -d${NC}"
        exit 1
    fi
    
    echo "🚀 Starting main_worker.py..."
    python main_worker.py
}

run_crawler() {
    print_header "CRAWLER"
    cd "$INGESTION_DIR"
    
    echo "🔍 Running TikTok crawler..."
    echo "   Output: data/crawl/tiktok_links_viet.csv"
    
    python crawler.py
}

show_help() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  test      Run unit tests for ingestion layer"
    echo "  worker    Run main_worker.py (requires Kafka, MinIO)"
    echo "  crawler   Run crawler to collect TikTok links"
    echo ""
    echo "Environment Variables (set in .env):"
    echo "  KAFKA_BOOTSTRAP_SERVERS  Kafka broker address"
    echo "  MINIO_ENDPOINT           MinIO server URL"
    echo "  INPUT_CSV_PATH           Path to input CSV file"
}

# Main
case "${1:-test}" in
    test)
        run_tests
        ;;
    worker)
        run_worker
        ;;
    crawler)
        run_crawler
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
