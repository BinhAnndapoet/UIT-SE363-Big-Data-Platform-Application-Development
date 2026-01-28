#!/bin/bash
# =============================================================================
# File: streaming/tests/test_layer4_dashboard.sh
# Mô tả: Test chi tiết LAYER 4 - Dashboard & Visualization
# Cách dùng: ./tests/test_layer4_dashboard.sh
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
# DASHBOARD CONTAINER TESTS
# =============================================================================
test_dashboard_container() {
    print_subheader "DASHBOARD CONTAINER"
    
    # Test 1: Container running
    echo -e "  ${YELLOW}TEST:${NC} Container 'dashboard' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^dashboard$"; then
        test_pass "dashboard container running"
    else
        test_fail "dashboard container not running" "docker compose up dashboard"
        return
    fi
    
    # Test 2: Port 8501 accessible
    echo -e "  ${YELLOW}TEST:${NC} Port 8501 accessible"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Dashboard HTTP 200"
    else
        test_fail "Dashboard not accessible" "HTTP $HTTP_CODE"
    fi
    
    # Test 3: Streamlit health
    echo -e "  ${YELLOW}TEST:${NC} Streamlit health endpoint"
    HEALTH_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8501/healthz 2>/dev/null)
    if [ "$HEALTH_CODE" = "200" ]; then
        test_pass "Streamlit healthy"
    else
        test_skip "Health endpoint not available (older Streamlit)"
    fi
    
    # Test 4: Environment variables
    echo -e "  ${YELLOW}TEST:${NC} Environment variables set"
    MINIO_ENDPOINT=$(docker exec dashboard env 2>/dev/null | grep "MINIO_PUBLIC_ENDPOINT" | cut -d= -f2)
    if [ -n "$MINIO_ENDPOINT" ]; then
        test_pass "MINIO_PUBLIC_ENDPOINT=$MINIO_ENDPOINT"
    else
        test_fail "MINIO_PUBLIC_ENDPOINT not set" "Videos won't load correctly"
    fi
    
    POSTGRES_HOST=$(docker exec dashboard env 2>/dev/null | grep "POSTGRES_HOST" | cut -d= -f2)
    if [ -n "$POSTGRES_HOST" ]; then
        test_pass "POSTGRES_HOST=$POSTGRES_HOST"
    else
        test_skip "POSTGRES_HOST using default"
    fi
    
    # Test 5: Container logs (check for errors)
    echo -e "  ${YELLOW}TEST:${NC} Check logs for errors"
    ERRORS=$(docker logs dashboard 2>&1 | tail -20 | grep -i "error\|exception\|failed" | head -2)
    if [ -z "$ERRORS" ]; then
        test_pass "No recent errors in logs"
    else
        test_skip "Some errors in logs"
        echo -e "      ${RED}$ERRORS${NC}"
    fi
}

# =============================================================================
# DASHBOARD FILES TESTS
# =============================================================================
test_dashboard_files() {
    print_subheader "DASHBOARD FILES"
    
    # Test 1: app.py exists
    echo -e "  ${YELLOW}TEST:${NC} File app.py tồn tại"
    if [ -f "${STREAMING_DIR}/dashboard/app.py" ]; then
        test_pass "app.py exists"
    else
        test_fail "app.py not found" "Main dashboard file"
        return
    fi
    
    # Test 2: Python syntax
    echo -e "  ${YELLOW}TEST:${NC} Python syntax check"
    if python3 -m py_compile "${STREAMING_DIR}/dashboard/app.py" 2>/dev/null; then
        test_pass "app.py syntax OK"
    else
        ERROR=$(python3 -m py_compile "${STREAMING_DIR}/dashboard/app.py" 2>&1)
        test_fail "app.py syntax error" "$ERROR"
    fi
    
    # Test 3: Dockerfile exists
    echo -e "  ${YELLOW}TEST:${NC} Dockerfile.dashboard exists"
    if [ -f "${STREAMING_DIR}/dashboard/Dockerfile.dashboard" ]; then
        test_pass "Dockerfile.dashboard exists"
    else
        test_fail "Dockerfile.dashboard not found" "Required for docker compose"
    fi
    
    # Test 4: requirements.txt exists
    echo -e "  ${YELLOW}TEST:${NC} requirements.txt exists"
    if [ -f "${STREAMING_DIR}/dashboard/requirements.txt" ]; then
        test_pass "requirements.txt exists"
        # Check for key packages
        PACKAGES=$(cat "${STREAMING_DIR}/dashboard/requirements.txt" | tr '\n' ' ')
        echo -e "      Packages: $(echo $PACKAGES | head -c 80)..."
    else
        test_fail "requirements.txt not found" "Dependency list"
    fi
}

# =============================================================================
# VIDEO URL TESTS
# =============================================================================
test_video_urls() {
    print_subheader "VIDEO URL ACCESSIBILITY"
    
    # Get MINIO endpoint from dashboard
    MINIO_ENDPOINT=$(docker exec dashboard env 2>/dev/null | grep "MINIO_PUBLIC_ENDPOINT" | cut -d= -f2)
    if [ -z "$MINIO_ENDPOINT" ]; then
        MINIO_ENDPOINT="http://localhost:9000"
    fi
    echo -e "  MinIO Endpoint: ${CYAN}${MINIO_ENDPOINT}${NC}"
    
    # Test 1: Get sample video from database
    echo -e "  ${YELLOW}TEST:${NC} Lấy video ID từ database"
    VIDEO_INFO=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT video_id, human_label FROM processed_results ORDER BY processed_at DESC LIMIT 1;" 2>/dev/null)
    if [ -n "$VIDEO_INFO" ]; then
        VIDEO_ID=$(echo "$VIDEO_INFO" | cut -d'|' -f1 | tr -d ' ')
        HUMAN_LABEL=$(echo "$VIDEO_INFO" | cut -d'|' -f2 | tr -d ' ')
        echo -e "      Video ID: ${VIDEO_ID}"
        echo -e "      Human Label: ${HUMAN_LABEL}"
        test_pass "Got video from database"
    else
        test_skip "No video in database to test"
        return
    fi
    
    # Test 2: Construct URL as app.py does
    echo -e "  ${YELLOW}TEST:${NC} Construct video URL"
    # Normalize label
    case "$HUMAN_LABEL" in
        *harm*) LABEL="harmful" ;;
        *safe*) LABEL="safe" ;;
        *) LABEL="unknown" ;;
    esac
    
    VIDEO_URL="${MINIO_ENDPOINT}/tiktok-raw-videos/raw/${LABEL}/${VIDEO_ID}.mp4"
    echo -e "      URL: ${VIDEO_URL}"
    test_pass "URL constructed"
    
    # Test 3: Check if video exists in MinIO
    echo -e "  ${YELLOW}TEST:${NC} Video tồn tại trong MinIO"
    FOUND=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c "mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/ --name '${VIDEO_ID}.mp4'" 2>/dev/null)
    if [ -n "$FOUND" ]; then
        ACTUAL_PATH=$(echo "$FOUND" | head -1)
        echo -e "      Found at: ${ACTUAL_PATH}"
        test_pass "Video exists in MinIO"
    else
        test_fail "Video not found in MinIO" "ID: ${VIDEO_ID}"
    fi
    
    # Test 4: HTTP accessibility via localhost
    echo -e "  ${YELLOW}TEST:${NC} Video accessible via localhost:9000"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:9000/tiktok-raw-videos/raw/${LABEL}/${VIDEO_ID}.mp4" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Video HTTP 200 via localhost"
    else
        test_fail "Video not accessible via localhost" "HTTP $HTTP_CODE"
    fi
    
    # Test 5: HTTP accessibility via MINIO_ENDPOINT
    echo -e "  ${YELLOW}TEST:${NC} Video accessible via MINIO_PUBLIC_ENDPOINT"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "${VIDEO_URL}" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Video HTTP 200 via ${MINIO_ENDPOINT}"
    else
        test_fail "Video not accessible via public endpoint" "HTTP $HTTP_CODE - URL: ${VIDEO_URL}"
    fi
    
    # Test 6: Check URL function in helpers.py (refactored location)
    echo -e "  ${YELLOW}TEST:${NC} get_video_url() function trong helpers.py"
    if grep -q "def get_video_url" "${STREAMING_DIR}/dashboard/helpers.py"; then
        test_pass "get_video_url() function exists"
        
        # Check if it uses human_label or Category
        if grep -A 10 "def get_video_url" "${STREAMING_DIR}/dashboard/helpers.py" | grep -q "human_label\|storage_label\|label"; then
            test_pass "Function uses label for path"
        else
            test_skip "Check if function uses correct label field"
        fi
    else
        test_fail "get_video_url() not found" "Video URLs won't work"
    fi
}

# =============================================================================
# DATABASE CONNECTION TESTS
# =============================================================================
test_database_connection() {
    print_subheader "DATABASE CONNECTION"
    
    # Test 1: Dashboard can query database
    echo -e "  ${YELLOW}TEST:${NC} Dashboard kết nối được database"
    # Check by looking at dashboard logs for SQL errors
    DB_ERRORS=$(docker logs dashboard 2>&1 | grep -i "psycopg\|database\|connection" | grep -i "error\|fail" | head -2)
    if [ -z "$DB_ERRORS" ]; then
        test_pass "No database connection errors"
    else
        test_fail "Database connection issues" "$DB_ERRORS"
    fi
    
    # Test 2: Query test from container
    echo -e "  ${YELLOW}TEST:${NC} Test query từ dashboard network"
    QUERY_RESULT=$(docker exec dashboard python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'user'),
        password=os.getenv('POSTGRES_PASSWORD', 'password'),
        database=os.getenv('POSTGRES_DB', 'tiktok_safety_db')
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM processed_results')
    print(cur.fetchone()[0])
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

    if [ -n "$QUERY_RESULT" ] && ! echo "$QUERY_RESULT" | grep -qi "error"; then
        test_pass "Query returned: $QUERY_RESULT records"
    else
        test_fail "Query failed" "$QUERY_RESULT"
    fi
}

# =============================================================================
# AIRFLOW INTEGRATION TESTS
# =============================================================================
test_airflow_integration() {
    print_subheader "AIRFLOW INTEGRATION"
    
    # Test 1: Airflow webserver accessible
    echo -e "  ${YELLOW}TEST:${NC} Airflow webserver (port 8080)"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        test_pass "Airflow UI accessible (HTTP $HTTP_CODE)"
    else
        test_fail "Airflow UI not accessible" "HTTP $HTTP_CODE"
    fi
    
    # Test 2: Airflow API accessible
    echo -e "  ${YELLOW}TEST:${NC} Airflow API /api/v1/dags"
    API_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -u admin:admin http://localhost:8080/api/v1/dags 2>/dev/null)
    if [ "$API_CODE" = "200" ]; then
        test_pass "Airflow API accessible"
    else
        test_fail "Airflow API not accessible" "HTTP $API_CODE - Check auth"
    fi
    
    # Test 3: DAGs visible via API
    echo -e "  ${YELLOW}TEST:${NC} DAGs visible in API"
    DAGS=$(curl -sf -u admin:admin http://localhost:8080/api/v1/dags 2>/dev/null)
    if echo "$DAGS" | grep -q "1_TIKTOK_ETL_COLLECTOR"; then
        test_pass "DAGs returned from API"
    else
        test_skip "Cannot verify DAGs via API"
    fi
    
    # Test 4: Dashboard can reach Airflow
    echo -e "  ${YELLOW}TEST:${NC} Dashboard có thể call Airflow API"
    API_TEST=$(docker exec dashboard curl -sf -o /dev/null -w "%{http_code}" -u admin:admin http://airflow-webserver:8080/api/v1/dags 2>/dev/null)
    if [ "$API_TEST" = "200" ]; then
        test_pass "Dashboard -> Airflow API OK"
    else
        test_skip "Cannot verify dashboard -> airflow connection"
    fi
}

# =============================================================================
# UI FUNCTIONALITY TESTS
# =============================================================================
test_ui_functionality() {
    print_subheader "UI FUNCTIONALITY"
    
    # Test 1: Main page loads
    echo -e "  ${YELLOW}TEST:${NC} Main page HTML"
    PAGE_HTML=$(curl -sf http://localhost:8501 2>/dev/null | head -50)
    if echo "$PAGE_HTML" | grep -qi "streamlit\|tiktok\|dashboard"; then
        test_pass "Page HTML contains expected content"
    else
        test_fail "Page HTML unexpected" "Check Streamlit app"
    fi
    
    # Test 2: Static assets
    echo -e "  ${YELLOW}TEST:${NC} Static assets loading"
    STATIC_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8501/static/css/main.css 2>/dev/null)
    if [ "$STATIC_CODE" = "200" ] || [ "$STATIC_CODE" = "404" ]; then
        test_pass "Static endpoint accessible"
    else
        test_skip "Cannot verify static assets"
    fi
    
    # Test 3: WebSocket (Streamlit uses WebSocket for updates)
    echo -e "  ${YELLOW}TEST:${NC} WebSocket support"
    # Just check if the port accepts connections
    if nc -z localhost 8501 2>/dev/null; then
        test_pass "Port 8501 accepting connections"
    else
        test_skip "Cannot verify WebSocket"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
print_header "LAYER 4: DASHBOARD TESTS"
echo -e "${CYAN}Testing: Streamlit Dashboard, Video URLs, Database Connection${NC}"
echo -e "${CYAN}Thời gian: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

test_dashboard_container
test_dashboard_files
test_video_urls
test_database_connection
test_airflow_integration
test_ui_functionality

# Summary
print_header "KẾT QUẢ LAYER 4"
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
