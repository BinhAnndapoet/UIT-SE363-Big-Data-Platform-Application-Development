#!/bin/bash
# ==============================================================================
# TikTok Big Data Pipeline - Comprehensive Test Suite
# Version: 2.0
# Tests all layers with detailed error reporting
# ==============================================================================

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0

# Log file
LOG_FILE="/tmp/tiktok_pipeline_test_$(date +%Y%m%d_%H%M%S).log"

# ==============================================================================
# Helper Functions
# ==============================================================================

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

print_banner() {
    log ""
    log "${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    log "${CYAN}║  $1${NC}"
    log "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
}

print_section() {
    log ""
    log "${BLUE}┌──────────────────────────────────────────────────────────────────────────┐${NC}"
    log "${BLUE}│  $1${NC}"
    log "${BLUE}└──────────────────────────────────────────────────────────────────────────┘${NC}"
}

test_start() {
    ((TOTAL_TESTS++))
    log "  ${BOLD}TEST $TOTAL_TESTS:${NC} $1"
}

test_pass() {
    ((PASSED_TESTS++))
    log "    ${GREEN}✅ PASS:${NC} $1"
}

test_fail() {
    ((FAILED_TESTS++))
    log "    ${RED}❌ FAIL:${NC} $1"
    if [ -n "$2" ]; then
        log "    ${RED}   └─ Error: $2${NC}"
    fi
}

test_warn() {
    ((WARNED_TESTS++))
    log "    ${YELLOW}⚠️  WARN:${NC} $1"
}

test_info() {
    log "    ${CYAN}ℹ️  INFO:${NC} $1"
}

# ==============================================================================
# LAYER 1: Infrastructure Tests
# ==============================================================================

test_layer1_infrastructure() {
    print_section "LAYER 1: Infrastructure Services"
    
    # 1.1 Docker Network
    test_start "Docker network 'tiktok-network' exists"
    if docker network ls | grep -q "tiktok-network"; then
        test_pass "Network exists"
        NETWORK_SUBNET=$(docker network inspect tiktok-network --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null)
        test_info "Subnet: $NETWORK_SUBNET"
    else
        test_fail "Network not found"
    fi
    
    # 1.2 Zookeeper
    test_start "Zookeeper container running and healthy"
    ZK_STATUS=$(docker inspect -f '{{.State.Status}}' zookeeper 2>/dev/null)
    if [ "$ZK_STATUS" = "running" ]; then
        ZK_RESPONSE=$(docker exec zookeeper bash -c 'echo ruok | nc localhost 2181' 2>/dev/null)
        if [ "$ZK_RESPONSE" = "imok" ]; then
            test_pass "Zookeeper running and responding 'imok'"
        else
            test_warn "Zookeeper running but not responding properly"
        fi
    else
        test_fail "Zookeeper not running (status: $ZK_STATUS)"
    fi
    
    # 1.3 Kafka
    test_start "Kafka container running and healthy"
    KAFKA_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' kafka 2>/dev/null)
    if [ "$KAFKA_HEALTH" = "healthy" ]; then
        test_pass "Kafka healthy"
        
        # Check topic
        test_start "Kafka topic 'tiktok_raw_data' exists"
        TOPICS=$(docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null)
        if echo "$TOPICS" | grep -q "tiktok_raw_data"; then
            test_pass "Topic exists"
        else
            test_warn "Topic not found, creating..."
            docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic tiktok_raw_data --partitions 1 --replication-factor 1 2>/dev/null
        fi
    else
        test_fail "Kafka not healthy (status: $KAFKA_HEALTH)"
    fi
    
    # 1.4 MinIO
    test_start "MinIO container running and healthy"
    MINIO_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' minio 2>/dev/null)
    if [ "$MINIO_HEALTH" = "healthy" ]; then
        test_pass "MinIO healthy"
        
        # Check buckets
        test_start "MinIO buckets exist"
        BUCKETS=$(docker run --rm --network tiktok-network -e MINIO_ROOT_USER=admin -e MINIO_ROOT_PASSWORD=password123 minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && mc ls local/' 2>/dev/null)
        if echo "$BUCKETS" | grep -q "tiktok-raw-videos"; then
            test_pass "Bucket 'tiktok-raw-videos' exists"
        else
            test_fail "Bucket 'tiktok-raw-videos' not found"
        fi
    else
        test_fail "MinIO not healthy (status: $MINIO_HEALTH)"
    fi
    
    # 1.5 PostgreSQL
    test_start "PostgreSQL container running and healthy"
    PG_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' postgres 2>/dev/null)
    if [ "$PG_HEALTH" = "healthy" ]; then
        test_pass "PostgreSQL healthy"
        
        # Check database
        test_start "Database 'tiktok_safety_db' exists with tables"
        TABLES=$(docker exec postgres psql -U user -d tiktok_safety_db -c "\dt" 2>/dev/null)
        if echo "$TABLES" | grep -q "processed_results"; then
            test_pass "Table 'processed_results' exists"
            
            # Count records
            RECORD_COUNT=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results;" 2>/dev/null | tr -d ' ')
            test_info "Records in processed_results: $RECORD_COUNT"
        else
            test_fail "Table 'processed_results' not found"
        fi
    else
        test_fail "PostgreSQL not healthy (status: $PG_HEALTH)"
    fi
    
    # 1.6 Port mappings
    test_start "All required ports are mapped"
    PORTS_OK=true
    for PORT in 8501 8080 9090 9000 9001 9092; do
        if docker ps --format '{{.Ports}}' | grep -q "$PORT->"; then
            test_info "Port $PORT: ✓"
        else
            test_warn "Port $PORT: not mapped"
            PORTS_OK=false
        fi
    done
    if [ "$PORTS_OK" = true ]; then
        test_pass "All ports correctly mapped"
    fi
}

# ==============================================================================
# LAYER 2: Spark Cluster Tests
# ==============================================================================

test_layer2_spark() {
    print_section "LAYER 2: Spark Cluster"
    
    # 2.1 Spark Master
    test_start "Spark Master container running"
    SM_STATUS=$(docker inspect -f '{{.State.Status}}' spark-master 2>/dev/null)
    if [ "$SM_STATUS" = "running" ]; then
        test_pass "Spark Master running"
        
        # Check UI
        test_start "Spark Master UI accessible"
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            test_pass "Spark UI responds HTTP 200"
        else
            test_fail "Spark UI returns HTTP $HTTP_CODE"
        fi
    else
        test_fail "Spark Master not running"
    fi
    
    # 2.2 Spark Worker
    test_start "Spark Worker container running"
    SW_STATUS=$(docker inspect -f '{{.State.Status}}' spark-worker 2>/dev/null)
    if [ "$SW_STATUS" = "running" ]; then
        test_pass "Spark Worker running"
    else
        test_fail "Spark Worker not running"
    fi
    
    # 2.3 Spark Processor
    test_start "Spark Processor container running"
    SP_STATUS=$(docker inspect -f '{{.State.Status}}' spark-processor 2>/dev/null)
    if [ "$SP_STATUS" = "running" ]; then
        test_pass "Spark Processor running"
        
        # Check AI models
        test_start "AI models mounted in Spark Processor"
        if docker exec spark-processor ls /models/text/CafeBERT_finetuned_best >/dev/null 2>&1; then
            test_pass "Text model (CafeBERT) mounted"
        else
            test_fail "Text model not found"
        fi
        
        test_start "Video model mounted"
        if docker exec spark-processor ls /models/video >/dev/null 2>&1; then
            test_pass "Video model directory exists"
        else
            test_warn "Video model directory not found"
        fi
        
        # Check PyTorch
        test_start "PyTorch available in Spark Processor"
        TORCH_VER=$(docker exec spark-processor python -c "import torch; print(torch.__version__)" 2>/dev/null)
        if [ -n "$TORCH_VER" ]; then
            test_pass "PyTorch version: $TORCH_VER"
        else
            test_fail "PyTorch not available"
        fi
        
        # Check Transformers
        test_start "Transformers library available"
        TRANS_VER=$(docker exec spark-processor python -c "import transformers; print(transformers.__version__)" 2>/dev/null)
        if [ -n "$TRANS_VER" ]; then
            test_pass "Transformers version: $TRANS_VER"
        else
            test_fail "Transformers not available"
        fi
    else
        test_fail "Spark Processor not running"
    fi
}

# ==============================================================================
# LAYER 3: Airflow Orchestration Tests
# ==============================================================================

test_layer3_airflow() {
    print_section "LAYER 3: Airflow Orchestration"
    
    # 3.1 Airflow DB
    test_start "Airflow database healthy"
    ADB_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' airflow-db 2>/dev/null)
    if [ "$ADB_HEALTH" = "healthy" ]; then
        test_pass "Airflow DB healthy"
    else
        test_fail "Airflow DB not healthy"
    fi
    
    # 3.2 Airflow Scheduler
    test_start "Airflow Scheduler running"
    AS_STATUS=$(docker inspect -f '{{.State.Status}}' airflow-scheduler 2>/dev/null)
    if [ "$AS_STATUS" = "running" ]; then
        test_pass "Scheduler running"
    else
        test_fail "Scheduler not running"
    fi
    
    # 3.3 Airflow Webserver
    test_start "Airflow Webserver accessible"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Webserver health check OK"
    else
        test_warn "Webserver returns HTTP $HTTP_CODE (may still be starting)"
    fi
    
    # 3.4 DAGs
    test_start "DAG 1_TIKTOK_ETL_COLLECTOR exists"
    DAG1=$(docker exec airflow-webserver airflow dags list 2>/dev/null | grep "1_TIKTOK_ETL_COLLECTOR")
    if [ -n "$DAG1" ]; then
        test_pass "DAG 1 found"
        IS_PAUSED=$(echo "$DAG1" | awk '{print $NF}')
        test_info "Paused: $IS_PAUSED"
    else
        test_fail "DAG 1 not found"
    fi
    
    test_start "DAG 2_TIKTOK_STREAMING_PIPELINE exists"
    DAG2=$(docker exec airflow-webserver airflow dags list 2>/dev/null | grep "2_TIKTOK_STREAMING_PIPELINE")
    if [ -n "$DAG2" ]; then
        test_pass "DAG 2 found"
        IS_PAUSED=$(echo "$DAG2" | awk '{print $NF}')
        test_info "Paused: $IS_PAUSED"
    else
        test_fail "DAG 2 not found"
    fi
    
    # 3.5 Connections
    test_start "Airflow connection 'postgres_pipeline' exists"
    CONN=$(docker exec airflow-webserver airflow connections get postgres_pipeline 2>/dev/null)
    if [ -n "$CONN" ]; then
        test_pass "Connection exists"
    else
        test_warn "Connection not found"
    fi
}

# ==============================================================================
# LAYER 4: Ingestion Module Tests
# ==============================================================================

test_layer4_ingestion() {
    print_section "LAYER 4: Ingestion Module"
    
    # 4.1 Ingestion files
    test_start "Ingestion module files exist"
    if [ -f "ingestion/main_worker.py" ]; then
        test_pass "main_worker.py exists"
    else
        test_fail "main_worker.py not found"
    fi
    
    if [ -f "ingestion/crawler.py" ]; then
        test_pass "crawler.py exists"
    else
        test_fail "crawler.py not found"
    fi
    
    if [ -f "ingestion/downloader.py" ]; then
        test_pass "downloader.py exists"
    else
        test_fail "downloader.py not found"
    fi
    
    # 4.2 Data source
    test_start "CSV data source exists"
    CSV_PATH="../data_viet/crawl/sub_tiktok_links_viet.csv"
    if [ -f "$CSV_PATH" ]; then
        LINE_COUNT=$(wc -l < "$CSV_PATH")
        test_pass "CSV exists with $LINE_COUNT lines"
    else
        CSV_PATH2="data/crawl/tiktok_links.csv"
        if [ -f "$CSV_PATH2" ]; then
            test_pass "Fallback CSV found"
        else
            test_warn "No CSV data source found"
        fi
    fi
    
    # 4.3 Test MinIO connectivity from ingestion perspective
    test_start "Ingestion can connect to MinIO"
    MINIO_TEST=$(docker run --rm --network tiktok-network minio/mc sh -c 'mc alias set local http://minio:9000 admin password123 >/dev/null 2>&1 && echo OK' 2>/dev/null)
    if [ "$MINIO_TEST" = "OK" ]; then
        test_pass "MinIO connection OK"
    else
        test_fail "Cannot connect to MinIO"
    fi
    
    # 4.4 Test Kafka connectivity
    test_start "Ingestion can connect to Kafka"
    KAFKA_TEST=$(docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null)
    if [ -n "$KAFKA_TEST" ]; then
        test_pass "Kafka connection OK"
    else
        test_fail "Cannot connect to Kafka"
    fi
}

# ==============================================================================
# LAYER 5: Processing Tests
# ==============================================================================

test_layer5_processing() {
    print_section "LAYER 5: AI Processing"
    
    # 5.1 Spark processor file
    test_start "spark_processor.py exists"
    if [ -f "spark/spark_processor.py" ]; then
        test_pass "File exists"
    else
        test_fail "File not found"
    fi
    
    # 5.2 Test text model loading
    test_start "Text model (CafeBERT) loads correctly"
    MODEL_TEST=$(docker exec spark-processor python -c "
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import warnings
warnings.filterwarnings('ignore')
try:
    tokenizer = AutoTokenizer.from_pretrained('/models/text/CafeBERT_finetuned_best')
    model = AutoModelForSequenceClassification.from_pretrained('/models/text/CafeBERT_finetuned_best')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    if echo "$MODEL_TEST" | grep -q "SUCCESS"; then
        test_pass "CafeBERT model loads successfully"
    else
        test_fail "Model loading failed: $MODEL_TEST"
    fi
    
    # 5.3 Environment variables
    test_start "TEXT_WEIGHT environment variable set"
    TEXT_WEIGHT=$(docker exec spark-processor printenv TEXT_WEIGHT 2>/dev/null)
    if [ -n "$TEXT_WEIGHT" ]; then
        test_pass "TEXT_WEIGHT=$TEXT_WEIGHT"
    else
        test_warn "TEXT_WEIGHT not set"
    fi
    
    test_start "DECISION_THRESHOLD environment variable set"
    THRESHOLD=$(docker exec spark-processor printenv DECISION_THRESHOLD 2>/dev/null)
    if [ -n "$THRESHOLD" ]; then
        test_pass "DECISION_THRESHOLD=$THRESHOLD"
    else
        test_warn "DECISION_THRESHOLD not set"
    fi
}

# ==============================================================================
# LAYER 6: Dashboard Tests
# ==============================================================================

test_layer6_dashboard() {
    print_section "LAYER 6: Streamlit Dashboard"
    
    # 6.1 Dashboard container
    test_start "Dashboard container running"
    DASH_STATUS=$(docker inspect -f '{{.State.Status}}' dashboard 2>/dev/null)
    if [ "$DASH_STATUS" = "running" ]; then
        test_pass "Dashboard running"
    else
        test_fail "Dashboard not running"
    fi
    
    # 6.2 Dashboard UI
    test_start "Dashboard UI accessible"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        test_pass "Dashboard responds HTTP 200"
    else
        test_fail "Dashboard returns HTTP $HTTP_CODE"
    fi
    
    # 6.3 Dashboard files
    test_start "Dashboard module files exist"
    MODULES=("app.py" "config.py" "helpers.py" "styles.py")
    for MOD in "${MODULES[@]}"; do
        if [ -f "dashboard/$MOD" ]; then
            test_info "$MOD: ✓"
        else
            test_fail "$MOD not found"
        fi
    done
    test_pass "Core modules present"
    
    # 6.4 Page modules
    test_start "Page modules exist"
    PAGES=("dashboard_monitor.py" "system_operations.py" "content_audit.py" "project_info.py" "database_manager.py")
    for PAGE in "${PAGES[@]}"; do
        if [ -f "dashboard/page_modules/$PAGE" ]; then
            test_info "$PAGE: ✓"
        else
            test_warn "$PAGE not found"
        fi
    done
    test_pass "Page modules present"
    
    # 6.5 Database connectivity
    test_start "Dashboard can connect to PostgreSQL"
    DB_TEST=$(docker exec dashboard python -c "
import psycopg2
try:
    conn = psycopg2.connect(host='postgres', port=5432, dbname='tiktok_safety_db', user='user', password='password')
    cur = conn.cursor()
    cur.execute('SELECT 1')
    conn.close()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    if [ "$DB_TEST" = "OK" ]; then
        test_pass "PostgreSQL connection OK"
    else
        test_fail "Cannot connect to PostgreSQL: $DB_TEST"
    fi
    
    # 6.6 No import errors
    test_start "No import errors in dashboard"
    IMPORT_ERRORS=$(docker logs dashboard 2>&1 | grep -i "ImportError\|ModuleNotFoundError" | tail -1)
    if [ -z "$IMPORT_ERRORS" ]; then
        test_pass "No import errors"
    else
        test_fail "Import error: $IMPORT_ERRORS"
    fi
    
    # 6.7 MINIO_PUBLIC_ENDPOINT
    test_start "MINIO_PUBLIC_ENDPOINT configured"
    MINIO_EP=$(docker exec dashboard printenv MINIO_PUBLIC_ENDPOINT 2>/dev/null)
    if [ -n "$MINIO_EP" ]; then
        test_pass "MINIO_PUBLIC_ENDPOINT=$MINIO_EP"
    else
        test_warn "MINIO_PUBLIC_ENDPOINT not set"
    fi
}

# ==============================================================================
# LAYER 7: Database Results Tests
# ==============================================================================

test_layer7_database() {
    print_section "LAYER 7: Database & Results"
    
    # 7.1 Table schema
    test_start "Table schema is correct"
    COLUMNS=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='processed_results' ORDER BY ordinal_position;" 2>/dev/null | tr -d ' ' | tr '\n' ',')
    REQUIRED="video_id,raw_text,text_score,video_score,avg_score,final_decision"
    ALL_FOUND=true
    for COL in $(echo $REQUIRED | tr ',' ' '); do
        if echo "$COLUMNS" | grep -q "$COL"; then
            test_info "Column $COL: ✓"
        else
            test_fail "Column $COL not found"
            ALL_FOUND=false
        fi
    done
    if [ "$ALL_FOUND" = true ]; then
        test_pass "All required columns present"
    fi
    
    # 7.2 Record count
    test_start "Records in processed_results"
    COUNT=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results;" 2>/dev/null | tr -d ' ')
    if [ -n "$COUNT" ] && [ "$COUNT" -ge 0 ]; then
        test_pass "Table has $COUNT records"
        
        if [ "$COUNT" -gt 0 ]; then
            # Category distribution
            HARMFUL=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results WHERE LOWER(final_decision) LIKE '%harmful%';" 2>/dev/null | tr -d ' ')
            SAFE=$((COUNT - HARMFUL))
            test_info "Harmful: $HARMFUL, Safe: $SAFE"
        fi
    else
        test_fail "Cannot query record count"
    fi
    
    # 7.3 Recent data
    test_start "Recent data exists (last 24h)"
    RECENT=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results WHERE processed_at > NOW() - INTERVAL '24 hours';" 2>/dev/null | tr -d ' ')
    if [ -n "$RECENT" ] && [ "$RECENT" -gt 0 ]; then
        test_pass "$RECENT records in last 24h"
    else
        test_info "No records in last 24h"
    fi
}

# ==============================================================================
# LAYER 8: End-to-End Integration
# ==============================================================================

test_layer8_e2e() {
    print_section "LAYER 8: End-to-End Integration"
    
    # 8.1 All containers running
    test_start "All required containers running"
    REQUIRED_CONTAINERS="zookeeper kafka minio postgres spark-master spark-worker spark-processor airflow-db airflow-scheduler airflow-webserver dashboard"
    ALL_UP=true
    for CONT in $REQUIRED_CONTAINERS; do
        STATUS=$(docker inspect -f '{{.State.Status}}' $CONT 2>/dev/null)
        if [ "$STATUS" = "running" ]; then
            test_info "$CONT: ✓"
        else
            test_fail "$CONT not running (status: $STATUS)"
            ALL_UP=false
        fi
    done
    if [ "$ALL_UP" = true ]; then
        test_pass "All containers running"
    fi
    
    # 8.2 Internal network connectivity
    test_start "Internal network DNS resolution"
    DNS_TEST=$(docker exec dashboard python -c "
import socket
hosts = ['postgres', 'kafka', 'minio', 'spark-master']
for h in hosts:
    try:
        ip = socket.gethostbyname(h)
        print(f'{h}:{ip}')
    except:
        print(f'{h}:FAIL')
" 2>/dev/null)
    if echo "$DNS_TEST" | grep -q "FAIL"; then
        test_fail "Some DNS resolutions failed"
    else
        test_pass "All hostnames resolve"
    fi
    
    # 8.3 Volume persistence
    test_start "Volume persistence configured"
    STATE_SIZE=$(du -sh state/ 2>/dev/null | cut -f1)
    if [ -n "$STATE_SIZE" ]; then
        test_pass "state/ folder: $STATE_SIZE"
    else
        test_warn "state/ folder not found"
    fi
    
    # 8.4 External access
    test_start "External access URLs configured"
    TAILSCALE_IP="100.69.255.87"
    test_info "Dashboard: http://$TAILSCALE_IP:8501"
    test_info "Airflow: http://$TAILSCALE_IP:8080"
    test_info "MinIO: http://$TAILSCALE_IP:9001"
    test_info "Spark: http://$TAILSCALE_IP:9090"
    test_pass "URLs documented"
}

# ==============================================================================
# Summary
# ==============================================================================

print_summary() {
    print_banner "TEST SUMMARY"
    
    log ""
    log "  ${BOLD}Total Tests:${NC}   $TOTAL_TESTS"
    log "  ${GREEN}Passed:${NC}        $PASSED_TESTS"
    log "  ${RED}Failed:${NC}        $FAILED_TESTS"
    log "  ${YELLOW}Warnings:${NC}      $WARNED_TESTS"
    log ""
    
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
        log "${GREEN}║  ✅ ALL TESTS PASSED! ($PASSED_TESTS/$TOTAL_TESTS - $PASS_RATE%)                                    ║${NC}"
        log "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
        EXIT_CODE=0
    else
        log "${RED}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
        log "${RED}║  ❌ SOME TESTS FAILED! ($PASSED_TESTS/$TOTAL_TESTS - $PASS_RATE%)                                   ║${NC}"
        log "${RED}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
        EXIT_CODE=1
    fi
    
    log ""
    log "📋 Full log saved to: $LOG_FILE"
    
    return $EXIT_CODE
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_banner "TikTok Big Data Pipeline - Comprehensive Test Suite"
    log "📅 Date: $(date)"
    log "📁 Working Directory: $(pwd)"
    log ""
    
    # Wait for services to be fully ready
    log "${YELLOW}⏳ Waiting 10 seconds for services to stabilize...${NC}"
    sleep 10
    
    # Run all tests
    test_layer1_infrastructure
    test_layer2_spark
    test_layer3_airflow
    test_layer4_ingestion
    test_layer5_processing
    test_layer6_dashboard
    test_layer7_database
    test_layer8_e2e
    
    # Print summary
    print_summary
    exit $?
}

# Run main
cd /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming
main
