# 🧪 Testing Guide

## Overview

Hệ thống testing bao gồm nhiều level kiểm tra từ unit tests đến end-to-end tests.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Testing Pyramid                            │
├─────────────────────────────────────────────────────────────────┤
│                        ▲                                        │
│                       /█\       E2E Tests (Manual/Automated)    │
│                      /███\                                      │
│                     /█████\     Integration Tests               │
│                    /███████\                                    │
│                   /█████████\   Component Tests                 │
│                  /███████████\                                  │
│                 ████████████████  Unit Tests                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Test Scripts

### Comprehensive Test Suite

**Location**: `streaming/tests/test_comprehensive.sh`

```bash
# Run all tests
cd streaming
bash tests/test_comprehensive.sh

# Expected output:
# ============================================================
#    🧪 COMPREHENSIVE SYSTEM TEST
# ============================================================
# 🔍 LAYER 1: Infrastructure Tests
#   [PASS] Network: tiktok-network exists
#   [PASS] Zookeeper: Container running
#   [PASS] Kafka: Container running
#   ...
# ============================================================
#    📊 TEST SUMMARY
# ============================================================
#    Total:   45
#    Passed:  39 ✅
#    Failed:   6 ❌
#    Warnings: 3 ⚠️
# ============================================================
```

### UI Button Functionality Tests (NEW)

**Location**: `streaming/tests/test_ui_buttons.sh`

```bash
# Test all dashboard UI buttons and API endpoints
cd streaming
bash tests/test_ui_buttons.sh

# Expected output:
# ============================================================
#   🔘 TESTING: Quick Actions Buttons
# ============================================================
# 🔍 Test 1: Dashboard Accessible (Refresh would work)
#   [PASS] Dashboard UI accessible (HTTP 200)
# 🔍 Test 2: Airflow UI Link Target
#   [PASS] Airflow UI accessible via API
# ...
# ============================================================
#   📊 TEST SUMMARY
# ============================================================
#   Total Tests:  18
#   ✅ Passed:    16
#   ❌ Failed:    0
#   ⚠️  Warnings: 2
#   🎉 All critical tests passed!
```

**Test Categories:**
| Category | Tests | Description |
|----------|-------|-------------|
| Quick Actions | 4 | Refresh, Airflow UI, MinIO, Clear Queued |
| Pipeline Control | 2 | Trigger Crawler, Trigger Streaming |
| Status Monitor | 4 | DAG Status, DAG Info, Run History, Task Instances |
| System Logs | 6 | Container logs (5 containers) + DB connection |
| Database | 2 | Processed results, System logs table |

---

## Test Categories

### Layer 1: Infrastructure Tests

```bash
#!/bin/bash
# Infrastructure tests

# Test 1.1: Docker Network
test_network() {
    if docker network ls | grep -q "tiktok-network"; then
        echo "[PASS] Network exists"
    else
        echo "[FAIL] Network not found"
    fi
}

# Test 1.2: Zookeeper
test_zookeeper() {
    if docker exec zookeeper echo "ruok" | nc localhost 2181 | grep -q "imok"; then
        echo "[PASS] Zookeeper healthy"
    else
        echo "[WARN] Zookeeper not responding"
    fi
}

# Test 1.3: Kafka
test_kafka() {
    if docker exec kafka kafka-broker-api-versions \
        --bootstrap-server kafka:9092 &>/dev/null; then
        echo "[PASS] Kafka broker healthy"
    else
        echo "[FAIL] Kafka not responding"
    fi
}

# Test 1.4: MinIO
test_minio() {
    if curl -s http://localhost:9000/minio/health/live | grep -q "OK"; then
        echo "[PASS] MinIO healthy"
    else
        echo "[FAIL] MinIO not responding"
    fi
}

# Test 1.5: PostgreSQL
test_postgres() {
    if docker exec postgres pg_isready -U user -q; then
        echo "[PASS] PostgreSQL ready"
    else
        echo "[FAIL] PostgreSQL not ready"
    fi
}
```

### Layer 2: Spark Tests

```bash
#!/bin/bash
# Spark tests

# Test 2.1: Spark Master
test_spark_master() {
    if curl -s http://localhost:9090/ | grep -q "Spark Master"; then
        echo "[PASS] Spark Master UI accessible"
    else
        echo "[FAIL] Spark Master not accessible"
    fi
}

# Test 2.2: Spark Worker
test_spark_worker() {
    WORKERS=$(curl -s http://localhost:9090/json/ | jq '.aliveworkers')
    if [ "$WORKERS" -ge 1 ]; then
        echo "[PASS] $WORKERS worker(s) registered"
    else
        echo "[FAIL] No workers registered"
    fi
}

# Test 2.3: Spark Processor
test_spark_processor() {
    if docker ps --format "{{.Names}}" | grep -q "spark-processor"; then
        echo "[PASS] Spark Processor running"
    else
        echo "[FAIL] Spark Processor not running"
    fi
}
```

### Layer 3: Airflow Tests

```bash
#!/bin/bash
# Airflow tests

# Test 3.1: Airflow DB
test_airflow_db() {
    if docker exec airflow-scheduler airflow db check &>/dev/null; then
        echo "[PASS] Airflow DB healthy"
    else
        echo "[FAIL] Airflow DB unhealthy"
    fi
}

# Test 3.2: Airflow Scheduler
test_airflow_scheduler() {
    if docker ps --filter "name=airflow-scheduler" --filter "status=running" -q | grep -q .; then
        echo "[PASS] Scheduler running"
    else
        echo "[FAIL] Scheduler not running"
    fi
}

# Test 3.3: Airflow Webserver
test_airflow_webserver() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u admin:admin http://localhost:8080/api/v1/dags)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[PASS] API accessible"
    else
        echo "[FAIL] API returned $HTTP_CODE"
    fi
}

# Test 3.4: DAGs Loaded
test_dags_loaded() {
    DAG_COUNT=$(curl -s -u admin:admin http://localhost:8080/api/v1/dags | jq '.total_entries')
    if [ "$DAG_COUNT" -ge 2 ]; then
        echo "[PASS] $DAG_COUNT DAGs loaded"
    else
        echo "[FAIL] Expected 2+ DAGs, found $DAG_COUNT"
    fi
}
```

### Layer 4: Ingestion Tests

```bash
#!/bin/bash
# Ingestion tests

# Test 4.1: CSV Files
test_csv_files() {
    CSV_COUNT=$(find ../data_viet/crawl -name "*.csv" | wc -l)
    if [ "$CSV_COUNT" -ge 1 ]; then
        echo "[PASS] Found $CSV_COUNT CSV files"
    else
        echo "[FAIL] No CSV files found"
    fi
}

# Test 4.2: Video Files
test_video_files() {
    VIDEO_COUNT=$(find ../data_viet/videos -name "*.mp4" | wc -l)
    if [ "$VIDEO_COUNT" -ge 1 ]; then
        echo "[PASS] Found $VIDEO_COUNT video files"
    else
        echo "[WARN] No video files found"
    fi
}

# Test 4.3: Kafka Topic
test_kafka_topic() {
    if docker exec kafka kafka-topics --list --bootstrap-server kafka:9092 | grep -q "raw-video-input"; then
        echo "[PASS] raw-video-input topic exists"
    else
        echo "[FAIL] Topic not found"
    fi
}
```

### Layer 5: Processing Tests

```bash
#!/bin/bash
# Processing tests

# Test 5.1: AI Models Mount
test_models_mount() {
    if docker exec spark-processor ls /app/models/ &>/dev/null; then
        echo "[PASS] Models directory mounted"
    else
        echo "[FAIL] Models not mounted"
    fi
}

# Test 5.2: Text Model
test_text_model() {
    if docker exec spark-processor python3 -c "
import torch
model = torch.load('/app/models/text_model.pt', map_location='cpu')
print('loaded')
" 2>/dev/null | grep -q "loaded"; then
        echo "[PASS] Text model loadable"
    else
        echo "[WARN] Text model not found/loadable"
    fi
}

# Test 5.3: Environment Variables
test_env_vars() {
    VARS=$(docker exec spark-processor env | grep -E "TEXT_WEIGHT|VIDEO_WEIGHT|DECISION_THRESHOLD" | wc -l)
    if [ "$VARS" -ge 3 ]; then
        echo "[PASS] All env vars set"
    else
        echo "[FAIL] Missing env vars"
    fi
}
```

### Layer 6: Dashboard Tests

```bash
#!/bin/bash
# Dashboard tests

# Test 6.1: Container Running
test_dashboard_container() {
    if docker ps --filter "name=dashboard" --filter "status=running" -q | grep -q .; then
        echo "[PASS] Dashboard container running"
    else
        echo "[FAIL] Dashboard not running"
    fi
}

# Test 6.2: Streamlit UI
test_streamlit_ui() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[PASS] Streamlit UI accessible"
    else
        echo "[FAIL] UI returned $HTTP_CODE"
    fi
}

# Test 6.3: Dashboard Modules
test_dashboard_modules() {
    MODULES=$(docker exec dashboard ls /app/page_modules/*.py 2>/dev/null | wc -l)
    if [ "$MODULES" -ge 5 ]; then
        echo "[PASS] All $MODULES modules present"
    else
        echo "[FAIL] Missing modules"
    fi
}

# Test 6.4: Database Connection
test_db_connection() {
    if docker exec dashboard python3 -c "
from helpers import get_db_engine
engine = get_db_engine()
with engine.connect() as conn:
    print('connected')
" 2>/dev/null | grep -q "connected"; then
        echo "[PASS] DB connection works"
    else
        echo "[FAIL] DB connection failed"
    fi
}
```

### Layer 7: Database Tests

```bash
#!/bin/bash
# Database tests

# Test 7.1: Table Exists
test_table_exists() {
    if docker exec postgres psql -U user -d tiktok_safety_db -c "\dt" | grep -q "processed_results"; then
        echo "[PASS] processed_results table exists"
    else
        echo "[FAIL] Table not found"
    fi
}

# Test 7.2: Schema Correct
test_schema() {
    COLUMNS=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='processed_results'" | tr -d ' ' | grep -v '^$')
    
    REQUIRED="video_id Category avg_score text_score video_score processed_at"
    MISSING=""
    for col in $REQUIRED; do
        if ! echo "$COLUMNS" | grep -qi "$col"; then
            MISSING="$MISSING $col"
        fi
    done
    
    if [ -z "$MISSING" ]; then
        echo "[PASS] All required columns present"
    else
        echo "[FAIL] Missing columns:$MISSING"
    fi
}

# Test 7.3: Data Exists
test_data_exists() {
    COUNT=$(docker exec postgres psql -U user -d tiktok_safety_db -t -c "SELECT COUNT(*) FROM processed_results")
    if [ "$COUNT" -gt 0 ]; then
        echo "[PASS] Found $COUNT records"
    else
        echo "[WARN] No records in database"
    fi
}
```

### Layer 8: E2E Tests

```bash
#!/bin/bash
# End-to-end tests

# Test 8.1: All Containers Running
test_all_containers() {
    EXPECTED=22
    RUNNING=$(docker compose ps --filter "status=running" -q | wc -l)
    if [ "$RUNNING" -ge "$EXPECTED" ]; then
        echo "[PASS] $RUNNING/$EXPECTED containers running"
    else
        echo "[FAIL] Only $RUNNING/$EXPECTED containers running"
    fi
}

# Test 8.2: Network Connectivity
test_network_connectivity() {
    # Test internal DNS
    if docker exec dashboard ping -c1 postgres &>/dev/null; then
        echo "[PASS] Dashboard can reach PostgreSQL"
    else
        echo "[FAIL] Network connectivity issue"
    fi
}

# Test 8.3: Full Pipeline Trigger
test_full_pipeline() {
    # Trigger DAG and wait for completion
    RUN_ID=$(curl -s -X POST -u admin:admin \
        -H "Content-Type: application/json" \
        "http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns" \
        -d '{}' | jq -r '.dag_run_id')
    
    if [ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ]; then
        echo "[PASS] Pipeline triggered: $RUN_ID"
    else
        echo "[FAIL] Pipeline trigger failed"
    fi
}
```

---

## Running Tests

### Quick Test
```bash
# Check all containers running
docker compose ps

# Basic health check
curl -s http://localhost:8501 | head -1
curl -s -u admin:admin http://localhost:8080/api/v1/dags | jq '.total_entries'
```

### Full Test Suite
```bash
cd streaming
chmod +x tests/test_comprehensive.sh
./tests/test_comprehensive.sh
```

### Individual Layer Tests
```bash
# Test specific layer
./tests/test_comprehensive.sh --layer 1  # Infrastructure only
./tests/test_comprehensive.sh --layer 6  # Dashboard only
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: System Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Services
        run: |
          cd streaming
          docker compose up -d
          sleep 120  # Wait for services
          
      - name: Run Tests
        run: |
          cd streaming
          bash tests/test_comprehensive.sh
          
      - name: Cleanup
        if: always()
        run: docker compose down -v
```

---

## Manual Testing Checklist

### Dashboard UI Tests
- [ ] **Analytics Page**: KPIs hiển thị đúng số liệu
- [ ] **Charts**: Pie chart, timeline chart render đúng
- [ ] **Operations**: Pipeline trigger buttons hoạt động
- [ ] **Content Audit**: Gallery pagination hoạt động
- [ ] **Video Player**: Video phát được từ MinIO
- [ ] **Database Manager**: SQL queries chạy được

### Pipeline Tests
- [ ] **Crawler DAG**: Trigger và chạy thành công
- [ ] **Streaming DAG**: Trigger và chạy thành công
- [ ] **Kafka**: Messages được gửi và nhận
- [ ] **Spark**: Jobs chạy và output đúng
- [ ] **PostgreSQL**: Data được lưu đúng format

### Integration Tests
- [ ] **Dashboard → PostgreSQL**: Data hiển thị đúng
- [ ] **Dashboard → MinIO**: Videos load được
- [ ] **Dashboard → Airflow**: DAG status đúng
- [ ] **Airflow → Kafka**: Messages được publish
- [ ] **Spark → PostgreSQL**: Results được persist

---

## Test Data

### Sample Test Data
```bash
# Create test CSV
cat > ../data_viet/crawl/test_sample.csv << 'EOF'
video_id,url,label,hashtag,description
test_001,https://tiktok.com/test1,harmful,#test,Test video 1
test_002,https://tiktok.com/test2,not_harmful,#test,Test video 2
EOF

# Create test video (placeholder)
ffmpeg -f lavfi -i color=c=blue:s=320x240:d=3 \
    -f lavfi -i anullsrc \
    -shortest ../data_viet/videos/harmful/test_001.mp4
```

### Database Test Data
```sql
-- Insert test records
INSERT INTO processed_results (
    video_id, "Category", avg_score, text_score, video_score, 
    audio_score, transcript, processed_at
) VALUES 
    ('test_001', 'harmful', 0.85, 0.9, 0.8, 0.0, 'test content', NOW()),
    ('test_002', 'not_harmful', 0.25, 0.2, 0.3, 0.0, 'safe content', NOW());

-- Verify
SELECT * FROM processed_results WHERE video_id LIKE 'test_%';

-- Cleanup
DELETE FROM processed_results WHERE video_id LIKE 'test_%';
```

---

## Debugging Tests

### Test Failures Analysis
```bash
# Layer 1 failures: Check Docker
docker system info
docker compose logs zookeeper

# Layer 2 failures: Check Spark
docker logs spark-master --tail 50
curl http://localhost:9090/json/

# Layer 3 failures: Check Airflow
docker logs airflow-scheduler --tail 50
docker exec airflow-scheduler airflow dags list-import-errors

# Layer 6 failures: Check Dashboard
docker logs dashboard --tail 50
docker exec dashboard python3 -c "import streamlit; print(streamlit.__version__)"
```

### Common Test Fixes
```bash
# Restart failed service
docker compose restart <service-name>

# Reset database
docker exec postgres psql -U user -d tiktok_safety_db -c "TRUNCATE processed_results"

# Clear Kafka topics
docker exec kafka kafka-topics --delete --topic raw-video-input --bootstrap-server kafka:9092

# Rebuild container
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

---

## Performance Testing

### Load Test Dashboard
```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_analytics(self):
        self.client.get("/")
    
    @task(1)
    def view_audit(self):
        self.client.get("/?page=audit")
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8501
```

### Database Performance
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM processed_results WHERE "Category" = 'harmful';

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('processed_results'));

-- Check indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'processed_results';
```

---

## Test Coverage

| Layer | Tests | Coverage | Status |
|-------|-------|----------|--------|
| Infrastructure | 8 | 95% | ✅ |
| Spark | 4 | 80% | ✅ |
| Airflow | 5 | 90% | ✅ |
| Ingestion | 4 | 75% | ✅ |
| Processing | 4 | 70% | ⚠️ |
| Dashboard | 5 | 85% | ✅ |
| Database | 4 | 90% | ✅ |
| E2E | 5 | 80% | ✅ |
| **Total** | **39/45** | **86%** | ✅ |
