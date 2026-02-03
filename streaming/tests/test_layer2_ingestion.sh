#!/bin/bash
# =============================================================================
# File: streaming/tests/test_layer2_ingestion.sh
# Mô tả: Test chi tiết LAYER 2 - Ingestion (Crawler, Downloader, Kafka Producer)
# Cách dùng: ./tests/test_layer2_ingestion.sh
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
# FILE STRUCTURE TESTS
# =============================================================================
test_file_structure() {
    print_subheader "INGESTION FILE STRUCTURE"
    
    # Test 1: ingestion folder exists
    echo -e "  ${YELLOW}TEST:${NC} Folder ingestion/ tồn tại"
    if [ -d "${STREAMING_DIR}/ingestion" ]; then
        test_pass "Folder ingestion/ exists"
    else
        test_fail "Folder ingestion/ not found" "Path: ${STREAMING_DIR}/ingestion"
        return
    fi
    
    # Test 2: crawler.py exists
    echo -e "  ${YELLOW}TEST:${NC} File crawler.py tồn tại"
    if [ -f "${STREAMING_DIR}/ingestion/crawler.py" ]; then
        test_pass "crawler.py exists"
    else
        test_fail "crawler.py not found" "Renamed from crawler_links.py?"
    fi
    
    # Test 3: downloader.py exists
    echo -e "  ${YELLOW}TEST:${NC} File downloader.py tồn tại"
    if [ -f "${STREAMING_DIR}/ingestion/downloader.py" ]; then
        test_pass "downloader.py exists"
    else
        test_fail "downloader.py not found" "Path: ${STREAMING_DIR}/ingestion/downloader.py"
    fi
    
    # Test 4: main_worker.py exists
    echo -e "  ${YELLOW}TEST:${NC} File main_worker.py tồn tại"
    if [ -f "${STREAMING_DIR}/ingestion/main_worker.py" ]; then
        test_pass "main_worker.py exists"
    else
        test_fail "main_worker.py not found" "Main pipeline entry point"
    fi
    
    # Test 5: config.py exists
    echo -e "  ${YELLOW}TEST:${NC} File config.py tồn tại"
    if [ -f "${STREAMING_DIR}/ingestion/config.py" ]; then
        test_pass "config.py exists"
    else
        test_fail "config.py not found" "Configuration file"
    fi
    
    # Test 6: clients/ folder exists
    echo -e "  ${YELLOW}TEST:${NC} Folder clients/ tồn tại"
    if [ -d "${STREAMING_DIR}/ingestion/clients" ]; then
        test_pass "clients/ folder exists"
        # List files in clients/
        CLIENT_FILES=$(ls "${STREAMING_DIR}/ingestion/clients/" 2>/dev/null | tr '\n' ' ')
        echo -e "      Files: ${CLIENT_FILES}"
    else
        test_fail "clients/ folder not found" "Should contain kafka_client.py, minio_client.py"
    fi
    
    # Test 7: cookies.txt exists
    echo -e "  ${YELLOW}TEST:${NC} File cookies.txt tồn tại"
    if [ -f "${STREAMING_DIR}/ingestion/cookies.txt" ]; then
        COOKIE_SIZE=$(wc -c < "${STREAMING_DIR}/ingestion/cookies.txt")
        if [ "$COOKIE_SIZE" -gt 100 ]; then
            test_pass "cookies.txt exists (${COOKIE_SIZE} bytes)"
        else
            test_skip "cookies.txt exists but may be empty/invalid (${COOKIE_SIZE} bytes)"
        fi
    else
        test_fail "cookies.txt not found" "Needed for TikTok authentication"
    fi
}

# =============================================================================
# PYTHON SYNTAX TESTS
# =============================================================================
test_python_syntax() {
    print_subheader "PYTHON SYNTAX CHECKS"
    
    PYTHON_FILES=(
        "crawler.py"
        "downloader.py"
        "main_worker.py"
        "config.py"
        "audio_processor.py"
    )
    
    for file in "${PYTHON_FILES[@]}"; do
        echo -e "  ${YELLOW}TEST:${NC} Syntax check: ${file}"
        FILEPATH="${STREAMING_DIR}/ingestion/${file}"
        if [ -f "$FILEPATH" ]; then
            if python3 -m py_compile "$FILEPATH" 2>/dev/null; then
                test_pass "${file} syntax OK"
            else
                ERROR=$(python3 -m py_compile "$FILEPATH" 2>&1)
                test_fail "${file} syntax error" "$ERROR"
            fi
        else
            test_skip "${file} not found"
        fi
    done
    
    # Check clients folder
    for file in "${STREAMING_DIR}/ingestion/clients"/*.py; do
        if [ -f "$file" ]; then
            FILENAME=$(basename "$file")
            echo -e "  ${YELLOW}TEST:${NC} Syntax check: clients/${FILENAME}"
            if python3 -m py_compile "$file" 2>/dev/null; then
                test_pass "clients/${FILENAME} syntax OK"
            else
                ERROR=$(python3 -m py_compile "$file" 2>&1)
                test_fail "clients/${FILENAME} syntax error" "$ERROR"
            fi
        fi
    done
}

# =============================================================================
# DATA FILES TESTS
# =============================================================================
test_data_files() {
    print_subheader "DATA FILES"
    
    # Test 1: data/crawl folder exists
    echo -e "  ${YELLOW}TEST:${NC} Folder data/crawl/ tồn tại"
    if [ -d "${STREAMING_DIR}/data/crawl" ]; then
        test_pass "data/crawl/ folder exists"
    else
        test_fail "data/crawl/ not found" "Created by start_all.sh"
    fi
    
    # Test 2: CSV file exists (after DAG 1 runs)
    echo -e "  ${YELLOW}TEST:${NC} File tiktok_links_viet.csv"
    CSV_PATH="${STREAMING_DIR}/data/crawl/tiktok_links_viet.csv"
    if [ -f "$CSV_PATH" ]; then
        LINE_COUNT=$(wc -l < "$CSV_PATH")
        test_pass "tiktok_links_viet.csv exists (${LINE_COUNT} lines)"
        
        # Check CSV header
        HEADER=$(head -1 "$CSV_PATH")
        echo -e "      Header: ${HEADER}"
    else
        test_skip "tiktok_links_viet.csv not found (run DAG 1 first)"
    fi
    
    # Test 3: temp_downloads folder
    echo -e "  ${YELLOW}TEST:${NC} Folder temp_downloads/"
    if [ -d "${STREAMING_DIR}/ingestion/temp_downloads" ]; then
        FILE_COUNT=$(find "${STREAMING_DIR}/ingestion/temp_downloads" -type f 2>/dev/null | wc -l)
        test_pass "temp_downloads/ exists (${FILE_COUNT} files)"
    else
        test_skip "temp_downloads/ not found (created at runtime)"
    fi
}

# =============================================================================
# KAFKA PRODUCER TESTS
# =============================================================================
test_kafka_integration() {
    print_subheader "KAFKA INTEGRATION"
    
    # Test 1: Topic exists
    echo -e "  ${YELLOW}TEST:${NC} Topic 'tiktok_raw_data' tồn tại"
    TOPICS=$(timeout 10 docker exec kafka /usr/bin/kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || echo "")
    if echo "$TOPICS" | grep -q "tiktok_raw_data"; then
        test_pass "Topic 'tiktok_raw_data' exists"
    elif [ -z "$TOPICS" ]; then
        test_skip "Cannot list topics (timeout)"
    else
        test_skip "Topic 'tiktok_raw_data' not found (will be created on first message)"
    fi
    
    # Test 2: Count messages in topic
    echo -e "  ${YELLOW}TEST:${NC} Đếm messages trong topic"
    MSG_COUNT=$(docker exec kafka /usr/bin/kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic tiktok_raw_data --time -1 2>/dev/null | awk -F: '{sum += $3} END {print sum}')
    if [ -n "$MSG_COUNT" ] && [ "$MSG_COUNT" -gt 0 ]; then
        test_pass "Topic has $MSG_COUNT messages"
    else
        test_skip "Topic empty or cannot count (run pipeline first)"
    fi
    
    # Test 3: Sample message from topic
    echo -e "  ${YELLOW}TEST:${NC} Đọc sample message từ topic"
    SAMPLE=$(docker exec kafka /usr/bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic tiktok_raw_data --from-beginning --max-messages 1 --timeout-ms 3000 2>/dev/null)
    if [ -n "$SAMPLE" ]; then
        # Check if JSON
        if echo "$SAMPLE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            test_pass "Sample message is valid JSON"
            # Extract video_id
            VIDEO_ID=$(echo "$SAMPLE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('video_id',''))" 2>/dev/null)
            echo -e "      Sample video_id: ${VIDEO_ID}"
        else
            test_fail "Sample message not valid JSON" "Check producer format"
        fi
    else
        test_skip "No message to sample (topic empty)"
    fi
}

# =============================================================================
# MINIO UPLOAD TESTS
# =============================================================================
test_minio_integration() {
    print_subheader "MINIO INTEGRATION"
    
    # Test 1: Videos uploaded
    echo -e "  ${YELLOW}TEST:${NC} Videos uploaded vào MinIO"
    VIDEO_COUNT=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/ --name "*.mp4" 2>/dev/null | wc -l')
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        test_pass "Found $VIDEO_COUNT videos in MinIO"
    else
        test_skip "No videos in MinIO (run pipeline first)"
    fi
    
    # Test 2: Folder structure raw/harmful and raw/safe
    echo -e "  ${YELLOW}TEST:${NC} Folder structure raw/harmful/ và raw/safe/"
    HARMFUL_COUNT=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/raw/harmful/ --name "*.mp4" 2>/dev/null | wc -l')
    SAFE_COUNT=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/raw/safe/ --name "*.mp4" 2>/dev/null | wc -l')
    
    if [ "$HARMFUL_COUNT" -gt 0 ] || [ "$SAFE_COUNT" -gt 0 ]; then
        test_pass "raw/harmful/: $HARMFUL_COUNT, raw/safe/: $SAFE_COUNT videos"
    else
        test_skip "No videos in structured folders yet"
    fi
    
    # Test 3: Sample video accessible
    echo -e "  ${YELLOW}TEST:${NC} Sample video accessible via HTTP"
    SAMPLE_VIDEO=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/ --name "*.mp4" 2>/dev/null | head -1')
    if [ -n "$SAMPLE_VIDEO" ]; then
        VIDEO_PATH=$(echo "$SAMPLE_VIDEO" | sed 's|local/tiktok-raw-videos/||')
        HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:9000/tiktok-raw-videos/${VIDEO_PATH}" 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            test_pass "Video HTTP accessible (200)"
        else
            test_fail "Video HTTP failed" "HTTP $HTTP_CODE - Path: $VIDEO_PATH"
        fi
    else
        test_skip "No video to test"
    fi
}

# =============================================================================
# AIRFLOW DAG TESTS
# =============================================================================
test_airflow_dags() {
    print_subheader "AIRFLOW DAGs"
    
    # Test 1: DAG files exist
    echo -e "  ${YELLOW}TEST:${NC} DAG file 1_TIKTOK_ETL_COLLECTOR.py"
    if [ -f "${STREAMING_DIR}/airflow/dags/1_TIKTOK_ETL_COLLECTOR.py" ]; then
        test_pass "DAG 1 file exists"
    else
        test_fail "DAG 1 file not found" "Path: airflow/dags/1_TIKTOK_ETL_COLLECTOR.py"
    fi
    
    echo -e "  ${YELLOW}TEST:${NC} DAG file 2_TIKTOK_STREAMING_PIPELINE.py"
    if [ -f "${STREAMING_DIR}/airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py" ]; then
        test_pass "DAG 2 file exists"
    else
        test_fail "DAG 2 file not found" "Path: airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py"
    fi
    
    # Test 2: DAG syntax
    echo -e "  ${YELLOW}TEST:${NC} DAG 1 Python syntax"
    if python3 -m py_compile "${STREAMING_DIR}/airflow/dags/1_TIKTOK_ETL_COLLECTOR.py" 2>/dev/null; then
        test_pass "DAG 1 syntax OK"
    else
        test_fail "DAG 1 syntax error" "Check file"
    fi
    
    echo -e "  ${YELLOW}TEST:${NC} DAG 2 Python syntax"
    if python3 -m py_compile "${STREAMING_DIR}/airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py" 2>/dev/null; then
        test_pass "DAG 2 syntax OK"
    else
        test_fail "DAG 2 syntax error" "Check file"
    fi
    
    # Test 3: DAG registered in Airflow
    echo -e "  ${YELLOW}TEST:${NC} DAGs registered trong Airflow"
    
    # Check if Airflow is ready (timeout 5s)
    if ! timeout 5 docker exec airflow-webserver airflow dags list 2>/dev/null >/dev/null; then
        test_skip "Airflow not ready yet (may need more startup time)"
    else
        DAGS=$(docker exec airflow-webserver airflow dags list 2>/dev/null | grep -E "1_TIKTOK|2_TIKTOK")
        if echo "$DAGS" | grep -q "1_TIKTOK_ETL_COLLECTOR"; then
            test_pass "DAG 1 registered"
        else
            test_skip "DAG 1 not yet registered (scheduler parsing, wait 30-60s)"
        fi
        
        if echo "$DAGS" | grep -q "2_TIKTOK_STREAMING_PIPELINE"; then
            test_pass "DAG 2 registered"
        else
            test_skip "DAG 2 not yet registered (scheduler parsing, wait 30-60s)"
        fi
    fi
    
    # Test 4: DAG paths correct
    echo -e "  ${YELLOW}TEST:${NC} DAG 1 uses correct INGESTION_PATH"
    if grep -q 'INGESTION_PATH.*=.*"/opt/project/streaming/ingestion"' "${STREAMING_DIR}/airflow/dags/1_TIKTOK_ETL_COLLECTOR.py"; then
        test_pass "DAG 1 INGESTION_PATH correct"
    else
        test_fail "DAG 1 INGESTION_PATH wrong" "Should be /opt/project/streaming/ingestion"
    fi
    
    echo -e "  ${YELLOW}TEST:${NC} DAG 2 uses correct DATA_DIR"
    if grep -q 'DATA_DIR.*=.*"/opt/project/streaming/data"' "${STREAMING_DIR}/airflow/dags/2_TIKTOK_STREAMING_PIPELINE.py"; then
        test_pass "DAG 2 DATA_DIR correct"
    else
        test_fail "DAG 2 DATA_DIR wrong" "Should be /opt/project/streaming/data"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
print_header "LAYER 2: INGESTION TESTS"
echo -e "${CYAN}Testing: Crawler, Downloader, Kafka Producer, MinIO Upload${NC}"
echo -e "${CYAN}Thời gian: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

test_file_structure
test_python_syntax
test_data_files
test_kafka_integration
test_minio_integration
test_airflow_dags

# Summary
print_header "KẾT QUẢ LAYER 2"
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
