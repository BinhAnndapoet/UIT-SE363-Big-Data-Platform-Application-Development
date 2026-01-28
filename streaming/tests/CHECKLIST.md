# ✅ TikTok Pipeline Testing Checklist

## 🚀 Quick Test (Chạy ngay)

```bash
cd /home/guest/Projects/SE363/UIT-SE363-Big-Data-Platform-Application-Development/streaming
./tests/test_all_layers.sh
```

**Expected Result:** `✅ ALL TESTS PASSED! (37/37)`

---

## 📋 Layer-by-Layer Manual Checklist

### Layer 1: Infrastructure ✅
- [ ] Zookeeper responds to srvr
- [ ] Kafka container running
- [ ] Kafka topic `tiktok_raw_data` exists
- [ ] MinIO health endpoint OK
- [ ] MinIO bucket `tiktok-raw-videos` exists
- [ ] Postgres is ready
- [ ] Table `processed_results` exists

**Manual verify:**
```bash
# Kafka topics
docker exec kafka /usr/bin/kafka-topics --list --bootstrap-server localhost:9092

# MinIO buckets
docker exec minio mc alias set local http://localhost:9000 admin password123
docker exec minio mc ls local/

# Postgres tables
docker exec postgres psql -U user -d tiktok_safety_db -c "\dt"
```

### Layer 2: Spark Cluster ✅
- [ ] Spark Master UI on http://localhost:9090
- [ ] spark-worker container running
- [ ] spark-processor container running
- [ ] Text model (CafeBERT) mounted at `/models/text/output/uitnlp_CafeBERT/`
- [ ] Video model mounted at `/models/video/`

**Manual verify:**
```bash
# Spark containers
docker ps | grep spark

# Model check
docker exec spark-processor ls /models/text/output/uitnlp_CafeBERT/train/best_checkpoint_FocalLoss/
```

### Layer 3: Airflow Orchestration ✅
- [ ] Airflow UI on http://localhost:8080 (admin/admin)
- [ ] airflow-scheduler container running
- [ ] DAG `1_TIKTOK_ETL_COLLECTOR` exists
- [ ] DAG `2_TIKTOK_STREAMING_PIPELINE` exists

**Manual verify:**
```bash
# List DAGs
docker exec airflow-scheduler airflow dags list

# Trigger DAG manually
docker exec airflow-scheduler airflow dags trigger 2_TIKTOK_STREAMING_PIPELINE
```

### Layer 4: Ingestion Module ✅
- [ ] `config.py` exists
- [ ] `ingestion_main_worker.py` exists
- [ ] CSV data source `tiktok_links_viet.csv` exists (3612+ lines)
- [ ] Can connect to MinIO from Airflow
- [ ] Can connect to Kafka from Airflow

**Manual verify:**
```bash
# CSV count
wc -l streaming/tiktok-pipeline/data_viet/crawl/tiktok_links_viet.csv

# Test connections
docker exec airflow-scheduler python3 -c "
from minio import Minio
client = Minio('minio:9000', access_key='admin', secret_key='password123', secure=False)
print('MinIO OK:', client.bucket_exists('tiktok-raw-videos'))
"
```

### Layer 5: Spark Processor (AI) ✅
- [ ] `spark_processor.py` exists
- [ ] PyTorch available (2.1.2+cpu)
- [ ] Transformers available (4.30.2)
- [ ] CafeBERT model loads successfully
- [ ] TEXT_WEIGHT=0.6 environment variable set

**Manual verify:**
```bash
# Check env vars
docker exec spark-processor sh -c 'echo TEXT_WEIGHT=$TEXT_WEIGHT'

# Test model loading
docker exec spark-processor python3 -c "
from transformers import AutoModelForSequenceClassification, AutoTokenizer
model_path = '/models/text/output/uitnlp_CafeBERT/train/best_checkpoint_FocalLoss'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
print('Model loaded successfully!')
"
```

### Layer 6: Database Results ✅
- [ ] Table has records (200+)
- [ ] Schema has 6+ required columns
- [ ] Recent data exists (last 24h)
- [ ] Accuracy metrics calculable

**Manual verify:**
```bash
# Record count
docker exec postgres psql -U user -d tiktok_safety_db -c "SELECT COUNT(*) FROM processed_results"

# Latest records
docker exec postgres psql -U user -d tiktok_safety_db -c "
SELECT video_id, final_decision, human_label, processed_at 
FROM processed_results 
ORDER BY processed_at DESC 
LIMIT 5
"

# Accuracy metrics
docker exec postgres psql -U user -d tiktok_safety_db -c "
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN final_decision = 'harmful' AND human_label = 'harmful' THEN 1 ELSE 0 END) as TP,
    SUM(CASE WHEN final_decision = 'not_harmful' AND human_label = 'not_harmful' THEN 1 ELSE 0 END) as TN,
    SUM(CASE WHEN final_decision = 'harmful' AND human_label = 'not_harmful' THEN 1 ELSE 0 END) as FP,
    SUM(CASE WHEN final_decision = 'not_harmful' AND human_label = 'harmful' THEN 1 ELSE 0 END) as FN
FROM processed_results
"
```

### Layer 7: Dashboard ✅
- [ ] dashboard container running
- [ ] Dashboard UI on http://localhost:8501
- [ ] Can connect to Postgres

**Manual verify:**
```bash
# Open browser
echo "Open: http://localhost:8501"

# Or with Tailscale:
echo "Open: http://100.69.255.87:8501"
```

### Layer 8: End-to-End ✅
- [ ] All 10 required containers running
- [ ] Network DNS resolution OK
- [ ] Spark processing active (check logs)
- [ ] state/ folder has data (16GB+)

**Manual verify:**
```bash
# All containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# State folder
du -sh streaming/state/

# Spark logs
docker logs spark-processor 2>&1 | tail -20
```

---

## 🔗 Service URLs

| Service | Internal | External (Tailscale) |
|---------|----------|---------------------|
| Airflow UI | http://localhost:8080 | http://100.69.255.87:8080 |
| Spark Master | http://localhost:9090 | http://100.69.255.87:9090 |
| MinIO Console | http://localhost:9001 | http://100.69.255.87:9001 |
| Dashboard | http://localhost:8501 | http://100.69.255.87:8501 |

**Credentials:**
- Airflow: `admin` / `admin`
- MinIO: `admin` / `password123`
- Postgres: `user` / `password` / `tiktok_safety_db`

---

## 🛠️ Troubleshooting

### Tests fail?
```bash
# Restart all services
cd streaming
docker-compose down
./start_all.sh

# Wait 2-3 minutes then test again
./tests/test_all_layers.sh
```

### Specific layer failing?
```bash
# Test only that layer
./tests/test_all_layers.sh 1  # Layer 1 only
./tests/test_all_layers.sh 3  # Layer 3 only
```

### Check container logs
```bash
docker logs <container_name> 2>&1 | tail -50
# Examples:
docker logs spark-processor 2>&1 | tail -50
docker logs airflow-scheduler 2>&1 | tail -50
```
