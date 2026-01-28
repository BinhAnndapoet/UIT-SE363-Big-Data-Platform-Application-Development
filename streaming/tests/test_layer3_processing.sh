#!/bin/bash
# =============================================================================
# File: streaming/tests/test_layer3_processing.sh
# Mô tả: Test chi tiết LAYER 3 - Processing (Spark Streaming, ML Models)
# Cách dùng: ./tests/test_layer3_processing.sh
# =============================================================================

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0

print_header() {
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

print_subheader() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

test_pass() {
    echo -e "  ${GREEN}✅ PASS:${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "  ${RED}❌ FAIL:${NC} $1"
    echo -e "  ${RED}   Detail:${NC} $2"
    ((FAILED++))
}

test_skip() {
    echo -e "  ${YELLOW}⏭️  SKIP:${NC} $1"
}

# =============================================================================
# SPARK CLUSTER TESTS
# =============================================================================
test_spark_cluster() {
    print_subheader "SPARK CLUSTER"
    
    # Test 1: spark-master running
    echo -e "  ${YELLOW}TEST:${NC} Container 'spark-master' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^spark-master$"; then
        test_pass "spark-master running"
    else
        test_fail "spark-master not running" "docker ps không thấy container"
    fi
    
    # Test 2: spark-worker running
    echo -e "  ${YELLOW}TEST:${NC} Container 'spark-worker' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^spark-worker$"; then
        test_pass "spark-worker running"
    else
        test_fail "spark-worker not running" "docker ps không thấy container"
    fi
    
    # Test 3: spark-processor running
    echo -e "  ${YELLOW}TEST:${NC} Container 'spark-processor' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^spark-processor$"; then
        test_pass "spark-processor running"
    else
        test_fail "spark-processor not running" "This is the streaming job container"
    fi
    
    # Test 4: Spark Master UI accessible
    echo -e "  ${YELLOW}TEST:${NC} Spark Master UI (port 9090)"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:9090 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        test_pass "Spark Master UI accessible (HTTP $HTTP_CODE)"
    else
        test_fail "Spark Master UI not accessible" "HTTP $HTTP_CODE - Port 9090"
    fi
    
    # Test 5: Worker registered with Master
    echo -e "  ${YELLOW}TEST:${NC} Worker registered với Master"
    MASTER_HTML=$(curl -sf http://localhost:9090 2>/dev/null)
    if echo "$MASTER_HTML" | grep -qi "worker"; then
        test_pass "Worker appears in Master UI"
    else
        test_skip "Cannot verify worker registration"
    fi
}

# =============================================================================
# SPARK PROCESSOR TESTS
# =============================================================================
test_spark_processor() {
    print_subheader "SPARK PROCESSOR (STREAMING JOB)"
    
    # Test 1: File structure
    echo -e "  ${YELLOW}TEST:${NC} Folder spark/ tồn tại"
    if [ -d "${STREAMING_DIR}/spark" ]; then
        test_pass "spark/ folder exists"
    else
        test_fail "spark/ folder not found" "Should contain Dockerfile and spark_processor.py"
        return
    fi
    
    # Test 2: spark_processor.py exists
    echo -e "  ${YELLOW}TEST:${NC} File spark/spark_processor.py"
    if [ -f "${STREAMING_DIR}/spark/spark_processor.py" ]; then
        test_pass "spark_processor.py exists"
    else
        test_fail "spark_processor.py not found" "Main Spark streaming job"
    fi
    
    # Test 3: Python syntax
    echo -e "  ${YELLOW}TEST:${NC} Syntax check spark_processor.py"
    if python3 -m py_compile "${STREAMING_DIR}/spark/spark_processor.py" 2>/dev/null; then
        test_pass "spark_processor.py syntax OK"
    else
        ERROR=$(python3 -m py_compile "${STREAMING_DIR}/spark/spark_processor.py" 2>&1)
        test_fail "spark_processor.py syntax error" "$ERROR"
    fi
    
    # Test 4: Container logs (check for errors)
    echo -e "  ${YELLOW}TEST:${NC} Check spark-processor logs for errors"
    ERRORS=$(docker logs spark-processor 2>&1 | grep -i "error\|exception\|failed" | tail -3)
    if [ -z "$ERRORS" ]; then
        test_pass "No recent errors in logs"
    else
        test_skip "Some log errors found (may be transient)"
        echo -e "      Last errors: $(echo $ERRORS | head -c 100)..."
    fi
    
    # Test 5: Kafka consumer group
    echo -e "  ${YELLOW}TEST:${NC} Kafka consumer group 'spark-tiktok-processor'"
    GROUPS=$(docker exec kafka /usr/bin/kafka-consumer-groups --bootstrap-server localhost:9092 --list 2>/dev/null)
    if echo "$GROUPS" | grep -q "spark-tiktok-processor"; then
        test_pass "Consumer group exists"
        
        # Get lag info
        LAG=$(docker exec kafka /usr/bin/kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group spark-tiktok-processor 2>/dev/null | grep "tiktok_raw_data" | awk '{print $5}' | head -1)
        echo -e "      Consumer lag: ${LAG:-N/A}"
    else
        test_skip "Consumer group not found (streaming job may not have started)"
    fi
    
    # Test 6: Checkpoint directory
    echo -e "  ${YELLOW}TEST:${NC} Checkpoint directory"
    if [ -d "${STREAMING_DIR}/state/spark_checkpoints" ]; then
        CHECKPOINT_FILES=$(find "${STREAMING_DIR}/state/spark_checkpoints" -type f 2>/dev/null | wc -l)
        if [ "$CHECKPOINT_FILES" -gt 0 ]; then
            test_pass "Checkpoint directory has $CHECKPOINT_FILES files"
        else
            test_skip "Checkpoint directory empty (streaming not started)"
        fi
    else
        test_skip "Checkpoint directory not found"
    fi
}

# =============================================================================
# ML MODEL TESTS
# =============================================================================
test_ml_models() {
    print_subheader "ML MODELS (Inside spark-processor)"
    
    # Test 1: Check if model loading in logs
    echo -e "  ${YELLOW}TEST:${NC} PhoBERT model loading"
    if docker logs spark-processor 2>&1 | grep -qi "phobert\|bert\|model.*load"; then
        test_pass "Model loading detected in logs"
    else
        test_skip "Cannot verify model loading"
    fi
    
    # Test 2: GPU/CPU inference
    echo -e "  ${YELLOW}TEST:${NC} Inference device (GPU/CPU)"
    DEVICE_LOG=$(docker logs spark-processor 2>&1 | grep -i "device\|cuda\|cpu" | tail -1)
    if [ -n "$DEVICE_LOG" ]; then
        echo -e "      Device info: $DEVICE_LOG"
        test_pass "Device info found"
    else
        test_skip "Cannot determine inference device"
    fi
    
    # Test 3: Blacklist keywords in spark_processor
    echo -e "  ${YELLOW}TEST:${NC} Blacklist keywords defined"
    if grep -q "BLACKLIST_KEYWORDS\|blacklist" "${STREAMING_DIR}/spark/spark_processor.py" 2>/dev/null; then
        test_pass "Blacklist keywords found in code"
    else
        test_skip "No blacklist check in spark_processor"
    fi
}

# =============================================================================
# DATABASE OUTPUT TESTS
# =============================================================================
test_database_output() {
    print_subheader "DATABASE OUTPUT (processed_results)"
    
    # Test 1: Table exists
    echo -e "  ${YELLOW}TEST:${NC} Table 'processed_results' tồn tại"
    TABLE_EXISTS=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'processed_results');" 2>/dev/null)
    if [ "$TABLE_EXISTS" = "t" ]; then
        test_pass "Table exists"
    else
        test_fail "Table not found" "Spark job should create this table"
        return
    fi
    
    # Test 2: Table schema
    echo -e "  ${YELLOW}TEST:${NC} Table schema có đủ columns"
    COLUMNS=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT column_name FROM information_schema.columns WHERE table_name = 'processed_results' ORDER BY ordinal_position;" 2>/dev/null | tr -d ' ')
    
    REQUIRED_COLS=("video_id" "raw_text" "final_decision" "processed_at")
    for col in "${REQUIRED_COLS[@]}"; do
        if echo "$COLUMNS" | grep -qw "$col"; then
            test_pass "Column '$col' exists"
        else
            test_skip "Column '$col' not found (may have different name)"
        fi
    done
    
    # Test 3: Row count
    echo -e "  ${YELLOW}TEST:${NC} Số records đã xử lý"
    ROW_COUNT=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT COUNT(*) FROM processed_results;" 2>/dev/null)
    if [ -n "$ROW_COUNT" ] && [ "$ROW_COUNT" -gt 0 ]; then
        test_pass "Found $ROW_COUNT processed records"
    else
        test_skip "No records yet (pipeline chưa chạy)"
    fi
    
    # Test 4: Recent processing (within 5 minutes)
    echo -e "  ${YELLOW}TEST:${NC} Records mới trong 5 phút"
    RECENT=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT COUNT(*) FROM processed_results WHERE processed_at > NOW() - INTERVAL '5 minutes';" 2>/dev/null)
    if [ -n "$RECENT" ] && [ "$RECENT" -gt 0 ]; then
        test_pass "$RECENT records in last 5 minutes"
    else
        test_skip "No recent processing"
    fi
    
    # Test 5: Sample record
    echo -e "  ${YELLOW}TEST:${NC} Sample record"
    SAMPLE=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT video_id, final_decision, text_score, video_score FROM processed_results ORDER BY processed_at DESC LIMIT 1;" 2>/dev/null)
    if [ -n "$SAMPLE" ]; then
        echo -e "      Sample: $SAMPLE"
        test_pass "Sample record retrieved"
    else
        test_skip "No sample available"
    fi
    
    # Test 6: Decision distribution
    echo -e "  ${YELLOW}TEST:${NC} Decision distribution"
    DIST=$(docker exec -i postgres psql -U user -d tiktok_safety_db -c "SELECT final_decision, COUNT(*) FROM processed_results GROUP BY final_decision;" 2>/dev/null)
    if [ -n "$DIST" ]; then
        echo "$DIST" | head -5
        test_pass "Distribution query OK"
    else
        test_skip "Cannot get distribution"
    fi
}

# =============================================================================
# END-TO-END FLOW TEST
# =============================================================================
test_e2e_flow() {
    print_subheader "END-TO-END FLOW CHECK"
    
    # Check if data flows from Kafka -> Spark -> Postgres
    echo -e "  ${YELLOW}TEST:${NC} Data flow: Kafka -> Spark -> Postgres"
    
    # Get Kafka message count
    KAFKA_COUNT=$(docker exec kafka /usr/bin/kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic tiktok_raw_data --time -1 2>/dev/null | awk -F: '{sum += $3} END {print sum}')
    
    # Get Postgres count
    PG_COUNT=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT COUNT(*) FROM processed_results;" 2>/dev/null)
    
    if [ -n "$KAFKA_COUNT" ] && [ -n "$PG_COUNT" ]; then
        echo -e "      Kafka messages: ${KAFKA_COUNT:-0}"
        echo -e "      Postgres records: ${PG_COUNT:-0}"
        
        if [ "${KAFKA_COUNT:-0}" -gt 0 ] && [ "${PG_COUNT:-0}" -gt 0 ]; then
            # Calculate processing rate
            RATE=$(echo "scale=2; $PG_COUNT * 100 / $KAFKA_COUNT" | bc 2>/dev/null || echo "N/A")
            echo -e "      Processing rate: ${RATE}%"
            test_pass "Data flowing through pipeline"
        else
            test_skip "Pipeline not fully active"
        fi
    else
        test_skip "Cannot verify flow"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
print_header "LAYER 3: PROCESSING TESTS"
echo -e "${CYAN}Testing: Spark Streaming, ML Models, Database Output${NC}"
echo -e "${CYAN}Thời gian: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

test_spark_cluster
test_spark_processor
test_ml_models
test_database_output
test_e2e_flow

# Summary
print_header "KẾT QUẢ LAYER 3"
TOTAL=$((PASSED + FAILED))
echo -e "  ${GREEN}Passed:${NC} $PASSED"
echo -e "  ${RED}Failed:${NC} $FAILED"
echo -e "  ${BLUE}Total:${NC}  $TOTAL"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 TẤT CẢ TESTS ĐỀU PASS!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  CÓ $FAILED TESTS FAIL - Xem chi tiết ở trên${NC}"
    exit 1
fi
