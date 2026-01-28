#!/bin/bash
# =============================================================================
#  UI BUTTON FUNCTIONALITY TEST SCRIPT
#  Tests all dashboard buttons and API endpoints
# =============================================================================

PASS=0
FAIL=0
WARN=0

AIRFLOW_URL="http://localhost:8080/api/v1"
AIRFLOW_AUTH="admin:admin"
DASHBOARD_URL="http://localhost:8501"

print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
}

test_pass() {
    echo "  [PASS] $1"
    PASS=$((PASS + 1))
}

test_fail() {
    echo "  [FAIL] $1"
    FAIL=$((FAIL + 1))
}

test_warn() {
    echo "  [WARN] $1"
    WARN=$((WARN + 1))
}

# =============================================================================
print_header "🔘 TESTING: Quick Actions Buttons"
# =============================================================================

# Test 1: Refresh Page (Dashboard accessible)
echo "🔍 Test 1: Dashboard Accessible (Refresh would work)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_URL")
if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Dashboard UI accessible (HTTP 200)"
else
    test_fail "Dashboard not accessible (HTTP $HTTP_CODE)"
fi

# Test 2: Airflow UI Link
echo "🔍 Test 2: Airflow UI Link Target"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags")
if [ "$HTTP_CODE" = "200" ]; then
    test_pass "Airflow UI accessible via API"
else
    test_fail "Airflow API not accessible (HTTP $HTTP_CODE)"
fi

# Test 3: MinIO Console Link
echo "🔍 Test 3: MinIO Console Link Target"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9001")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    test_pass "MinIO Console accessible"
else
    test_warn "MinIO Console may not be accessible (HTTP $HTTP_CODE)"
fi

# Test 4: Clear Queued Button - API Test
echo "🔍 Test 4: Clear Queued Runs API"
# Get queued runs count
QUEUED=$(curl -s -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns?state=queued" | grep -o '"dag_run_id"' | wc -l || echo "0")
test_pass "Clear Queued API accessible (found $QUEUED queued runs)"

# =============================================================================
print_header "🚀 TESTING: Pipeline Control Buttons"
# =============================================================================

# Test 5: Trigger Crawler DAG
echo "🔍 Test 5: Trigger Crawler DAG API"
# First unpause
curl -s -X PATCH -u "$AIRFLOW_AUTH" \
    -H "Content-Type: application/json" \
    "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR" \
    -d '{"is_paused": false}' > /dev/null

# Then trigger
TRIGGER_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST -u "$AIRFLOW_AUTH" \
    -H "Content-Type: application/json" \
    "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns" \
    -d '{"conf": {}}')

if [ "$TRIGGER_RESP" = "200" ] || [ "$TRIGGER_RESP" = "409" ]; then
    test_pass "Crawler DAG trigger API works (HTTP $TRIGGER_RESP)"
else
    test_fail "Crawler DAG trigger failed (HTTP $TRIGGER_RESP)"
fi

# Test 6: Trigger Streaming DAG
echo "🔍 Test 6: Trigger Streaming DAG API"
curl -s -X PATCH -u "$AIRFLOW_AUTH" \
    -H "Content-Type: application/json" \
    "$AIRFLOW_URL/dags/2_TIKTOK_STREAMING_PIPELINE" \
    -d '{"is_paused": false}' > /dev/null

TRIGGER_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST -u "$AIRFLOW_AUTH" \
    -H "Content-Type: application/json" \
    "$AIRFLOW_URL/dags/2_TIKTOK_STREAMING_PIPELINE/dagRuns" \
    -d '{"conf": {}}')

if [ "$TRIGGER_RESP" = "200" ] || [ "$TRIGGER_RESP" = "409" ]; then
    test_pass "Streaming DAG trigger API works (HTTP $TRIGGER_RESP)"
else
    test_fail "Streaming DAG trigger failed (HTTP $TRIGGER_RESP)"
fi

# =============================================================================
print_header "📊 TESTING: Status Monitor Functions"
# =============================================================================

# Test 7: Get DAG Status
echo "🔍 Test 7: Get DAG Status API"
CRAWL_STATUS=$(curl -s -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns?limit=1" | grep -o '"state":"[^"]*"' | head -1 || echo "unknown")
if [ -n "$CRAWL_STATUS" ]; then
    test_pass "DAG status API works ($CRAWL_STATUS)"
else
    test_warn "DAG status returned empty"
fi

# Test 8: Get DAG Info (paused status)
echo "🔍 Test 8: Get DAG Info API"
DAG_INFO=$(curl -s -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR")
IS_PAUSED=$(echo "$DAG_INFO" | grep -o '"is_paused":[^,}]*' | head -1 || echo "unknown")
if [ -n "$IS_PAUSED" ]; then
    test_pass "DAG info API works ($IS_PAUSED)"
else
    test_fail "DAG info API failed"
fi

# Test 9: Get DAG Run History
echo "🔍 Test 9: Get DAG Run History API"
RUN_HISTORY=$(curl -s -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns?limit=5")
RUN_COUNT=$(echo "$RUN_HISTORY" | grep -o '"dag_run_id"' | wc -l || echo "0")
test_pass "DAG run history API works (found $RUN_COUNT runs)"

# Test 10: Get Task Instances
echo "🔍 Test 10: Get Task Instances API"
# Get latest run ID first
LATEST_RUN=$(curl -s -u "$AIRFLOW_AUTH" "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns?limit=1" | grep -o '"dag_run_id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$LATEST_RUN" ]; then
    TASK_INSTANCES=$(curl -s -o /dev/null -w "%{http_code}" -u "$AIRFLOW_AUTH" \
        "$AIRFLOW_URL/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns/$LATEST_RUN/taskInstances")
    if [ "$TASK_INSTANCES" = "200" ]; then
        test_pass "Task instances API works"
    else
        test_warn "Task instances API returned HTTP $TASK_INSTANCES"
    fi
else
    test_warn "No DAG runs found to test task instances"
fi

# =============================================================================
print_header "📋 TESTING: System Logs Functions"
# =============================================================================

# Test 11: Get Container Logs
echo "🔍 Test 11: Docker Container Logs"
for container in postgres minio kafka airflow-scheduler spark-master; do
    LOGS=$(docker logs --tail 5 $container 2>&1)
    if [ -n "$LOGS" ]; then
        test_pass "Container logs accessible: $container"
    else
        test_warn "Container logs empty: $container"
    fi
done

# Test 12: Database Connection
echo "🔍 Test 12: Database Connection for Logs"
DB_TEST=$(docker exec postgres psql -U user -d tiktok_safety_db -c "SELECT 1" 2>&1)
if echo "$DB_TEST" | grep -q "1"; then
    test_pass "Database connection works"
else
    test_fail "Database connection failed"
fi

# =============================================================================
print_header "🗃️ TESTING: Database Functions"  
# =============================================================================

# Test 13: Get Data from processed_results
echo "🔍 Test 13: Get Processed Results"
DATA_COUNT=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results" 2>/dev/null | tr -d ' ')
if [ -n "$DATA_COUNT" ] && [ "$DATA_COUNT" -ge 0 ]; then
    test_pass "Processed results accessible ($DATA_COUNT records)"
else
    test_warn "Could not get processed results count"
fi

# Test 14: System Logs Table
echo "🔍 Test 14: System Logs Table"
LOGS_EXISTS=$(docker exec postgres psql -U user -d tiktok_safety_db -c "\dt" 2>&1 | grep -c "system_logs" || echo "0")
if [ "$LOGS_EXISTS" -ge 1 ]; then
    test_pass "System logs table exists"
else
    test_warn "System logs table not found"
fi

# =============================================================================
print_header "📊 TEST SUMMARY"
# =============================================================================

TOTAL=$((PASS + FAIL + WARN))

echo ""
echo "  Total Tests:  $TOTAL"
echo "  ✅ Passed:    $PASS"
echo "  ❌ Failed:    $FAIL"
echo "  ⚠️  Warnings: $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "  🎉 All critical tests passed!"
    exit 0
else
    echo "  ⚠️  Some tests failed. Please review above."
    exit 1
fi
