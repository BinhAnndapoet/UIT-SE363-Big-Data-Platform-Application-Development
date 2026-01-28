#!/bin/bash
# ==============================================================================
# Dashboard Bug Fix Verification Tests
# Tests all the specific bugs that were fixed:
# 1. TypeError: unhashable dict in system_operations.py
# 2. localhost links → Tailscale IP (100.69.255.87)
# 3. Video path using MINIO_PUBLIC_ENDPOINT
# 4. Gallery pagination session state
# 5. AI Model cards overflow
# ==============================================================================

# Don't exit on error - we want to run all tests
# set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

print_header() {
    echo ""
    echo -e "${CYAN}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═════════════════════════════════════════════════════════════${NC}"
}

test_pass() {
    echo -e "  ${GREEN}✅ PASS:${NC} $1"
    ((PASS_COUNT++))
}

test_fail() {
    echo -e "  ${RED}❌ FAIL:${NC} $1"
    ((FAIL_COUNT++))
}

test_warn() {
    echo -e "  ${YELLOW}⚠️ WARN:${NC} $1"
    ((WARN_COUNT++))
}

# ==============================================================================
# BUG FIX 1: TypeError unhashable dict
# ==============================================================================
print_header "BUG FIX 1: TypeError unhashable dict"

echo "  TEST: system_operations.py uses engine_state.get('state')"
if grep -q 'engine_state.get("state"' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py 2>/dev/null; then
    test_pass "Fix applied - uses engine_state.get('state')"
else
    test_fail "Fix NOT applied - still using engine_state directly"
fi

echo "  TEST: state_info dict has 'waiting' and 'active' keys"
if grep -q '"waiting":' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py && \
   grep -q '"active":' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py; then
    test_pass "state_info has 'waiting' and 'active' keys"
else
    test_fail "state_info missing new state keys"
fi

# ==============================================================================
# BUG FIX 2: EXTERNAL_URLS configuration
# ==============================================================================
print_header "BUG FIX 2: EXTERNAL_URLS Configuration"

echo "  TEST: config.py has EXTERNAL_URLS dict"
if grep -q "EXTERNAL_URLS" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/config.py 2>/dev/null; then
    test_pass "EXTERNAL_URLS defined in config.py"
else
    test_fail "EXTERNAL_URLS missing from config.py"
fi

echo "  TEST: config.py extracts PUBLIC_HOST from MINIO_PUBLIC_ENDPOINT"
if grep -q "PUBLIC_HOST" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/config.py; then
    test_pass "PUBLIC_HOST extraction configured"
else
    test_fail "PUBLIC_HOST not configured"
fi

echo "  TEST: system_operations.py imports EXTERNAL_URLS"
if grep -q "from config import.*EXTERNAL_URLS" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py; then
    test_pass "system_operations.py imports EXTERNAL_URLS"
else
    test_fail "system_operations.py missing EXTERNAL_URLS import"
fi

echo "  TEST: project_info.py imports EXTERNAL_URLS"
if grep -q "from config import EXTERNAL_URLS" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "project_info.py imports EXTERNAL_URLS"
else
    test_fail "project_info.py missing EXTERNAL_URLS import"
fi

echo "  TEST: No hardcoded localhost:8080 in system_operations.py"
if grep -q "localhost:8080" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py; then
    test_fail "Still has hardcoded localhost:8080"
else
    test_pass "No hardcoded localhost:8080"
fi

echo "  TEST: No hardcoded localhost:9001 in system_operations.py"
if grep -q "localhost:9001" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/system_operations.py; then
    test_fail "Still has hardcoded localhost:9001"
else
    test_pass "No hardcoded localhost:9001"
fi

# ==============================================================================
# BUG FIX 3: Video URL uses MINIO_PUBLIC_ENDPOINT
# ==============================================================================
print_header "BUG FIX 3: Video URL Configuration"

echo "  TEST: get_video_url uses MINIO_CONF['public_endpoint']"
if grep -q "MINIO_CONF\['public_endpoint'\]" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/helpers.py; then
    test_pass "get_video_url uses MINIO_CONF['public_endpoint']"
else
    test_fail "get_video_url not using MINIO_CONF['public_endpoint']"
fi

echo "  TEST: MINIO_PUBLIC_ENDPOINT env var is set"
MINIO_EP=$(docker exec dashboard printenv MINIO_PUBLIC_ENDPOINT 2>/dev/null || echo "NOT_SET")
if [[ "$MINIO_EP" != "NOT_SET" && "$MINIO_EP" != "" ]]; then
    test_pass "MINIO_PUBLIC_ENDPOINT = $MINIO_EP"
else
    test_warn "MINIO_PUBLIC_ENDPOINT not set in container"
fi

# ==============================================================================
# BUG FIX 4: Gallery Pagination Session State
# ==============================================================================
print_header "BUG FIX 4: Gallery Pagination"

echo "  TEST: content_audit.py initializes session_state for pagination"
if grep -q '"gallery_page" not in st.session_state' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/content_audit.py; then
    test_pass "Session state initialization exists"
else
    test_fail "Missing session state initialization"
fi

echo "  TEST: content_audit.py initializes items_per_page in session_state"
if grep -q '"items_per_page" not in st.session_state' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/content_audit.py; then
    test_pass "items_per_page session state initialized"
else
    test_fail "Missing items_per_page session state"
fi

echo "  TEST: Next/Previous buttons call st.rerun()"
if grep -q "st.rerun()" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/content_audit.py; then
    test_pass "st.rerun() called for pagination"
else
    test_fail "Missing st.rerun() for pagination"
fi

# ==============================================================================
# BUG FIX 5: AI Model Cards Overflow
# ==============================================================================
print_header "BUG FIX 5: AI Model Cards CSS"

echo "  TEST: project_info.py uses min-height instead of height"
if grep -q "min-height: 280px" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "Uses min-height: 280px"
else
    test_fail "Still using fixed height"
fi

echo "  TEST: project_info.py has overflow: visible"
if grep -q "overflow: visible" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "Has overflow: visible"
else
    test_fail "Missing overflow: visible"
fi

echo "  TEST: No fixed height: 300px in AI model cards"
# Check specifically in AI model card section
if grep -A5 "Text Model\|Video Model\|Audio Model" /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py | grep -q "height: 300px"; then
    test_fail "Still has fixed height: 300px"
else
    test_pass "No fixed height: 300px in AI cards"
fi

# ==============================================================================
# BUG FIX 6: Useful Links in Project Info
# ==============================================================================
print_header "BUG FIX 6: Useful Links URLs"

echo "  TEST: project_info.py uses EXTERNAL_URLS for dashboard link"
if grep -q 'EXTERNAL_URLS\["dashboard"\]' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "Dashboard link uses EXTERNAL_URLS"
else
    test_fail "Dashboard link not using EXTERNAL_URLS"
fi

echo "  TEST: project_info.py uses EXTERNAL_URLS for airflow link"
if grep -q 'EXTERNAL_URLS\["airflow"\]' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "Airflow link uses EXTERNAL_URLS"
else
    test_fail "Airflow link not using EXTERNAL_URLS"
fi

echo "  TEST: project_info.py uses EXTERNAL_URLS for minio link"
if grep -q 'EXTERNAL_URLS\["minio_console"\]' /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming/dashboard/page_modules/project_info.py; then
    test_pass "MinIO link uses EXTERNAL_URLS"
else
    test_fail "MinIO link not using EXTERNAL_URLS"
fi

# ==============================================================================
# INTEGRATION: Dashboard Runtime Tests
# ==============================================================================
print_header "INTEGRATION: Dashboard Runtime"

echo "  TEST: Dashboard container is running"
if docker ps --format '{{.Names}}' | grep -q "dashboard"; then
    test_pass "Dashboard container running"
else
    test_fail "Dashboard container not running"
fi

echo "  TEST: Dashboard UI responds on port 8501"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 | grep -q "200"; then
    test_pass "Dashboard responds HTTP 200"
else
    test_warn "Dashboard not responding (may need network check)"
fi

echo "  TEST: No import errors in dashboard logs (last 50 lines)"
if docker logs dashboard --tail 50 2>&1 | grep -qi "ImportError\|ModuleNotFoundError\|AttributeError"; then
    test_fail "Import errors found in dashboard logs"
else
    test_pass "No import errors in recent logs"
fi

echo "  TEST: No TypeError in dashboard logs (recent)"
if docker logs dashboard --since 60s 2>&1 | grep -qi "TypeError"; then
    test_fail "TypeError found in dashboard logs (recent)"
else
    test_pass "No TypeError in recent logs"
fi

# ==============================================================================
# SUMMARY
# ==============================================================================
print_header "TEST SUMMARY"

echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASS_COUNT"
echo -e "  ${RED}Failed:${NC}  $FAIL_COUNT"
echo -e "  ${YELLOW}Warnings:${NC} $WARN_COUNT"
echo ""

TOTAL=$((PASS_COUNT + FAIL_COUNT))
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ ALL BUG FIXES VERIFIED! ($PASS_COUNT/$TOTAL tests passed)${NC}"
    echo -e "${GREEN}═════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ SOME FIXES INCOMPLETE! ($PASS_COUNT/$TOTAL tests passed)${NC}"
    echo -e "${RED}═════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
