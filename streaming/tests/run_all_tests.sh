#!/bin/bash
# =============================================================================
# File: streaming/tests/run_all_tests.sh
# Mô tả: Chạy tất cả tests cho pipeline TikTok Safety
# Cách dùng: ./tests/run_all_tests.sh [layer_number]
#   - Không tham số: chạy tất cả layers
#   - Có tham số (1-4): chạy test layer cụ thể
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Counters
TOTAL_PASSED=0
TOTAL_FAILED=0

print_banner() {
    echo ""
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                                                                  ║${NC}"
    echo -e "${MAGENTA}║   🛡️  TIKTOK SAFETY PIPELINE - COMPREHENSIVE TEST SUITE          ║${NC}"
    echo -e "${MAGENTA}║                                                                  ║${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Thời gian: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}Workspace: ${SCRIPT_DIR}/..${NC}"
    echo ""
}

run_layer_test() {
    LAYER=$1
    TEST_FILE=$2
    DESCRIPTION=$3
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}RUNNING: Layer $LAYER - $DESCRIPTION${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -f "${SCRIPT_DIR}/${TEST_FILE}" ]; then
        chmod +x "${SCRIPT_DIR}/${TEST_FILE}"
        bash "${SCRIPT_DIR}/${TEST_FILE}"
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "\n${GREEN}✅ Layer $LAYER PASSED${NC}"
            ((TOTAL_PASSED++))
        else
            echo -e "\n${RED}❌ Layer $LAYER HAS FAILURES${NC}"
            ((TOTAL_FAILED++))
        fi
    else
        echo -e "${RED}❌ Test file not found: ${TEST_FILE}${NC}"
        ((TOTAL_FAILED++))
    fi
}

# Parse arguments
LAYER_ARG=$1

print_banner

# Define test layers
declare -A LAYERS
LAYERS[1]="test_layer1_infrastructure.sh:Infrastructure (Zookeeper, Kafka, MinIO, Postgres)"
LAYERS[2]="test_layer2_ingestion.sh:Ingestion (Crawler, Downloader, Kafka Producer)"
LAYERS[3]="test_layer3_processing.sh:Processing (Spark Streaming, ML Models)"
LAYERS[4]="test_layer4_dashboard.sh:Dashboard & Visualization"

if [ -n "$LAYER_ARG" ]; then
    # Run specific layer
    if [ -n "${LAYERS[$LAYER_ARG]}" ]; then
        IFS=':' read -r TEST_FILE DESCRIPTION <<< "${LAYERS[$LAYER_ARG]}"
        run_layer_test "$LAYER_ARG" "$TEST_FILE" "$DESCRIPTION"
    else
        echo -e "${RED}Invalid layer number: $LAYER_ARG${NC}"
        echo "Available layers: 1, 2, 3, 4"
        exit 1
    fi
else
    # Run all layers
    echo -e "${CYAN}Chạy tất cả 4 layers...${NC}"
    
    for i in 1 2 3 4; do
        IFS=':' read -r TEST_FILE DESCRIPTION <<< "${LAYERS[$i]}"
        run_layer_test "$i" "$TEST_FILE" "$DESCRIPTION"
    done
fi

# Final Summary
echo ""
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║                      FINAL SUMMARY                               ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Layers Passed:${NC} $TOTAL_PASSED"
echo -e "  ${RED}Layers Failed:${NC} $TOTAL_FAILED"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 ALL TESTS PASSED! Pipeline is healthy!                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ⚠️  SOME TESTS FAILED - Check output above for details          ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
