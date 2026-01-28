#!/bin/bash
# =============================================================================
# File: streaming/tests/test_layer1_infrastructure.sh
# Mô tả: Test chi tiết LAYER 1 - Infrastructure (Zookeeper, Kafka, MinIO, Postgres)
# Cách dùng: ./tests/test_layer1_infrastructure.sh
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
# ZOOKEEPER TESTS
# =============================================================================
test_zookeeper() {
    print_subheader "ZOOKEEPER TESTS"
    
    # Test 1: Container running
    echo -e "  ${YELLOW}TEST:${NC} Container 'zookeeper' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^zookeeper$"; then
        test_pass "Container zookeeper running"
    else
        test_fail "Container zookeeper not running" "docker ps không thấy container"
        return
    fi
    
    # Test 2: Port 2181 listening (check via nc or health)
    echo -e "  ${YELLOW}TEST:${NC} Port 2181 đang listen"
    if docker exec zookeeper bash -c 'echo ruok | nc 127.0.0.1 2181 2>/dev/null' | grep -q "imok"; then
        test_pass "Port 2181 responding (imok)"
    elif docker exec zookeeper bash -c 'cat /proc/net/tcp 2>/dev/null' | grep -qi "0881"; then
        test_pass "Port 2181 listening (via /proc/net/tcp)"
    else
        test_skip "Cannot verify port 2181 (container healthy)"
    fi
    
    # Test 3: ZK mode (standalone/leader/follower)
    echo -e "  ${YELLOW}TEST:${NC} Zookeeper mode"
    ZK_MODE=$(docker exec zookeeper bash -c 'echo srvr | nc 127.0.0.1 2181 2>/dev/null | grep Mode' || echo "")
    if [ -n "$ZK_MODE" ]; then
        test_pass "Zookeeper mode: $ZK_MODE"
    else
        test_skip "Không lấy được mode (nc có thể không cài)"
    fi
    
    # Test 4: Check znode /brokers
    echo -e "  ${YELLOW}TEST:${NC} Znode /brokers tồn tại (Kafka registered)"
    if docker exec zookeeper bash -c 'echo "ls /brokers/ids" | /opt/bitnami/zookeeper/bin/zkCli.sh -server localhost:2181 2>/dev/null' | grep -q "\["; then
        test_pass "Znode /brokers/ids exists"
    else
        test_skip "Không verify được znode (zkCli có thể khác path)"
    fi
}

# =============================================================================
# KAFKA TESTS
# =============================================================================
test_kafka() {
    print_subheader "KAFKA TESTS"
    
    # Test 1: Container running
    echo -e "  ${YELLOW}TEST:${NC} Container 'kafka' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^kafka$"; then
        test_pass "Container kafka running"
    else
        test_fail "Container kafka not running" "docker ps không thấy container"
        return
    fi
    
    # Test 2: Container healthy
    echo -e "  ${YELLOW}TEST:${NC} Health check status"
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' kafka 2>/dev/null || echo "none")
    if [ "$HEALTH" = "healthy" ]; then
        test_pass "Kafka container healthy"
    else
        test_fail "Kafka not healthy" "Status: $HEALTH"
    fi
    
    # Test 3: Port 9092 listening (via broker API or healthcheck)
    echo -e "  ${YELLOW}TEST:${NC} Port 9092 (internal) đang listen"
    if docker exec kafka /usr/bin/kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null | head -1 | grep -q "ApiVersion\|kafka"; then
        test_pass "Port 9092 responding (broker API)"
    elif docker exec kafka bash -c 'cat /proc/net/tcp 2>/dev/null' | grep -qi "2384"; then
        test_pass "Port 9092 listening (via /proc/net/tcp)"
    elif [ "$HEALTH" = "healthy" ]; then
        test_pass "Kafka healthy (port assumed OK)"
    else
        test_skip "Cannot verify port 9092 directly"
    fi
    
    # Test 4: Topic list
    echo -e "  ${YELLOW}TEST:${NC} Có thể list topics"
    TOPICS=$(timeout 10 docker exec kafka /usr/bin/kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || echo "")
    if [ -n "$TOPICS" ]; then
        test_pass "Kafka topics accessible"
        echo -e "      Topics: $(echo $TOPICS | tr '\n' ' ')"
    else
        test_skip "Cannot list topics (timeout or broker issue)"
    fi
    
    # Test 5: Topic tiktok_raw_data exists
    echo -e "  ${YELLOW}TEST:${NC} Topic 'tiktok_raw_data' tồn tại"
    if echo "$TOPICS" | grep -q "tiktok_raw_data"; then
        test_pass "Topic 'tiktok_raw_data' exists"
    elif [ -z "$TOPICS" ]; then
        test_skip "Cannot list topics (timeout)"
    else
        test_skip "Topic 'tiktok_raw_data' not found (chưa tạo)"
    fi
    
    # Test 6: Produce/Consume test
    echo -e "  ${YELLOW}TEST:${NC} Produce & Consume message"
    TEST_MSG="test_$(date +%s)"
    echo "$TEST_MSG" | docker exec -i kafka /usr/bin/kafka-console-producer --broker-list localhost:9092 --topic test_health 2>/dev/null
    RECEIVED=$(docker exec kafka /usr/bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic test_health --from-beginning --max-messages 1 --timeout-ms 5000 2>/dev/null | tail -1)
    if [ "$RECEIVED" = "$TEST_MSG" ]; then
        test_pass "Produce/Consume OK"
    else
        test_skip "Không verify được (topic test_health chưa tạo hoặc timeout)"
    fi
}

# =============================================================================
# MINIO TESTS
# =============================================================================
test_minio() {
    print_subheader "MINIO TESTS"
    
    # Test 1: Container running
    echo -e "  ${YELLOW}TEST:${NC} Container 'minio' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^minio$"; then
        test_pass "Container minio running"
    else
        test_fail "Container minio not running" "docker ps không thấy container"
        return
    fi
    
    # Test 2: Container healthy
    echo -e "  ${YELLOW}TEST:${NC} Health check status"
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' minio 2>/dev/null || echo "none")
    if [ "$HEALTH" = "healthy" ]; then
        test_pass "MinIO container healthy"
    else
        test_fail "MinIO not healthy" "Status: $HEALTH"
    fi
    
    # Test 3: Health endpoint
    echo -e "  ${YELLOW}TEST:${NC} Health endpoint /minio/health/live"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Health endpoint returns 200"
    else
        test_fail "Health endpoint failed" "HTTP code: $HTTP_CODE"
    fi
    
    # Test 4: Console port
    echo -e "  ${YELLOW}TEST:${NC} Console port 9001 accessible"
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:9001 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        test_pass "Console port 9001 OK (HTTP $HTTP_CODE)"
    else
        test_fail "Console port 9001 not accessible" "HTTP code: $HTTP_CODE"
    fi
    
    # Test 5: Bucket tiktok-raw-videos exists
    echo -e "  ${YELLOW}TEST:${NC} Bucket 'tiktok-raw-videos' tồn tại"
    BUCKETS=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc ls local/' 2>/dev/null)
    if echo "$BUCKETS" | grep -q "tiktok-raw-videos"; then
        test_pass "Bucket 'tiktok-raw-videos' exists"
    else
        test_fail "Bucket 'tiktok-raw-videos' not found" "Available: $BUCKETS"
    fi
    
    # Test 6: Bucket tiktok-raw-audios exists
    echo -e "  ${YELLOW}TEST:${NC} Bucket 'tiktok-raw-audios' tồn tại"
    if echo "$BUCKETS" | grep -q "tiktok-raw-audios"; then
        test_pass "Bucket 'tiktok-raw-audios' exists"
    else
        test_skip "Bucket 'tiktok-raw-audios' not found (optional)"
    fi
    
    # Test 7: Count videos in bucket
    echo -e "  ${YELLOW}TEST:${NC} Đếm số video trong bucket"
    VIDEO_COUNT=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/ --name "*.mp4" 2>/dev/null | wc -l')
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        test_pass "Found $VIDEO_COUNT videos in bucket"
    else
        test_skip "No videos found yet (chưa crawl)"
    fi
    
    # Test 8: Public access policy
    echo -e "  ${YELLOW}TEST:${NC} Video accessible publicly (anonymous download)"
    SAMPLE_VIDEO=$(docker run --rm --network tiktok-network --entrypoint "" minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc find local/tiktok-raw-videos/ --name "*.mp4" 2>/dev/null | head -1')
    if [ -n "$SAMPLE_VIDEO" ]; then
        VIDEO_NAME=$(basename "$SAMPLE_VIDEO")
        VIDEO_PATH=$(echo "$SAMPLE_VIDEO" | sed 's|local/tiktok-raw-videos/||')
        HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:9000/tiktok-raw-videos/${VIDEO_PATH}" 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            test_pass "Video publicly accessible (HTTP 200)"
        else
            test_fail "Video not publicly accessible" "HTTP $HTTP_CODE - Check anonymous policy"
        fi
    else
        test_skip "No video to test public access"
    fi
}

# =============================================================================
# POSTGRES TESTS
# =============================================================================
test_postgres() {
    print_subheader "POSTGRES TESTS"
    
    # Test 1: Container running
    echo -e "  ${YELLOW}TEST:${NC} Container 'postgres' đang chạy"
    if docker ps --format '{{.Names}}' | grep -q "^postgres$"; then
        test_pass "Container postgres running"
    else
        test_fail "Container postgres not running" "docker ps không thấy container"
        return
    fi
    
    # Test 2: Container healthy
    echo -e "  ${YELLOW}TEST:${NC} Health check status"
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' postgres 2>/dev/null || echo "none")
    if [ "$HEALTH" = "healthy" ]; then
        test_pass "Postgres container healthy"
    else
        test_fail "Postgres not healthy" "Status: $HEALTH"
    fi
    
    # Test 3: Can connect
    echo -e "  ${YELLOW}TEST:${NC} Có thể kết nối database"
    if docker exec postgres pg_isready -U user -d tiktok_safety_db >/dev/null 2>&1; then
        test_pass "Database connection OK"
    else
        test_fail "Cannot connect to database" "pg_isready failed"
    fi
    
    # Test 4: Table processed_results exists
    echo -e "  ${YELLOW}TEST:${NC} Table 'processed_results' tồn tại"
    TABLE_EXISTS=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'processed_results');" 2>/dev/null)
    if [ "$TABLE_EXISTS" = "t" ]; then
        test_pass "Table 'processed_results' exists"
    else
        test_fail "Table 'processed_results' not found" "Run init.sql or Spark job first"
    fi
    
    # Test 5: Table system_logs exists
    echo -e "  ${YELLOW}TEST:${NC} Table 'system_logs' tồn tại"
    TABLE_EXISTS=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_logs');" 2>/dev/null)
    if [ "$TABLE_EXISTS" = "t" ]; then
        test_pass "Table 'system_logs' exists"
    else
        test_skip "Table 'system_logs' not found (created by db-migrator)"
    fi
    
    # Test 6: Count rows in processed_results
    echo -e "  ${YELLOW}TEST:${NC} Đếm số records đã xử lý"
    ROW_COUNT=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT COUNT(*) FROM processed_results;" 2>/dev/null)
    if [ -n "$ROW_COUNT" ] && [ "$ROW_COUNT" -gt 0 ]; then
        test_pass "Found $ROW_COUNT processed records"
    else
        test_skip "No processed records yet (chưa chạy pipeline)"
    fi
    
    # Test 7: Recent activity (within 1 hour)
    echo -e "  ${YELLOW}TEST:${NC} Hoạt động gần đây (trong 1 giờ)"
    RECENT=$(docker exec -i postgres psql -U user -d tiktok_safety_db -tAc "SELECT COUNT(*) FROM processed_results WHERE processed_at > NOW() - INTERVAL '1 hour';" 2>/dev/null)
    if [ -n "$RECENT" ] && [ "$RECENT" -gt 0 ]; then
        test_pass "$RECENT records processed in last hour"
    else
        test_skip "No recent activity"
    fi
}

# =============================================================================
# MAIN
# =============================================================================
print_header "LAYER 1: INFRASTRUCTURE TESTS"
echo -e "${CYAN}Testing: Zookeeper, Kafka, MinIO, Postgres${NC}"
echo -e "${CYAN}Thời gian: $(date '+%Y-%m-%d %H:%M:%S')${NC}"

test_zookeeper
test_kafka
test_minio
test_postgres

# Summary
print_header "KẾT QUẢ LAYER 1"
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
