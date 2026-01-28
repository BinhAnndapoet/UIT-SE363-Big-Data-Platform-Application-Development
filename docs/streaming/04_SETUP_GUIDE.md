# 🛠️ Setup & Installation Guide

## Prerequisites

### Hardware Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB SSD | 100+ GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software Requirements
| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Container orchestration |
| Git | 2.40+ | Version control |
| Python | 3.9+ | Scripting (optional) |

### Network Requirements
- Port 8501 (Dashboard)
- Port 8080 (Airflow)
- Port 9000, 9001 (MinIO)
- Port 9090 (Spark Master)
- Port 5432 (PostgreSQL)
- Port 9092 (Kafka)
- Port 2181 (Zookeeper)

---

## Quick Start

### Step 1: Clone Repository
```bash
cd ~/Projects/SE363
git clone https://github.com/<your-repo>/UIT-SE363-Big-Data-Platform-Application-Development.git
cd UIT-SE363-Big-Data-Platform-Application-Development/streaming
```

### Step 2: Configure Environment
```bash
# Tạo file .env (optional - có defaults)
cat > .env << 'EOF'
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=tiktok_safety_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_VIDEOS=tiktok-raw-videos

# Kafka
KAFKA_BROKER=kafka:9092

# AI Models
TEXT_WEIGHT=0.6
VIDEO_WEIGHT=0.4
DECISION_THRESHOLD=0.5
EOF
```

### Step 3: Start All Services
```bash
# Grant execute permission
chmod +x start_all.sh

# Start all 22 containers
./start_all.sh
```

### Step 4: Verify Services
```bash
# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Wait for all services to be healthy (2-3 minutes)
docker compose ps
```

### Step 5: Access Dashboard
Open browser and navigate to:
- **Dashboard**: http://localhost:8501
- **Airflow**: http://localhost:8080 (admin/admin)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin123)
- **Spark**: http://localhost:9090

---

## Detailed Installation

### Docker Installation (Ubuntu)
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker compose version
```

### Project Structure Setup
```bash
# Navigate to project
cd streaming

# Verify folder structure
tree -L 1
# Expected:
# .
# ├── docker-compose.yml
# ├── start_all.sh
# ├── link_host.sh
# ├── airflow/
# ├── dashboard/
# ├── tiktok-pipeline/
# └── zookeeper/

# Make scripts executable
chmod +x start_all.sh link_host.sh

# Create data directories
mkdir -p data_viet/videos/{harmful,not_harmful}
mkdir -p data_viet/audios
mkdir -p data_viet/crawl
```

---

## Configuration Files

### docker-compose.yml Overview
```yaml
services:
  # Infrastructure
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    
  minio:
    image: minio/minio:latest
    
  postgres:
    image: postgres:15
    
  # Processing
  spark-master:
    image: bitnami/spark:3.4
    
  spark-worker:
    image: bitnami/spark:3.4
    
  spark-processor:
    build: ./tiktok-pipeline/processor
    
  # Orchestration
  airflow-webserver:
    build: ./airflow
    
  airflow-scheduler:
    build: ./airflow
    
  # Application
  dashboard:
    build: ./dashboard
```

### Airflow DAGs Configuration
```python
# airflow/dags/tiktok_etl_dag.py
DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Scheduling
schedule_interval = '@hourly'  # or '@daily', None for manual
```

### Dashboard Configuration
```python
# dashboard/config.py
# Configure based on deployment environment

# Development (localhost)
MINIO_PUBLIC_ENDPOINT = "http://localhost:9000"

# Production (Tailscale)
MINIO_PUBLIC_ENDPOINT = "http://100.69.255.87:9000"
```

---

## Service Details

### PostgreSQL Database
```bash
# Connect to database
docker exec -it postgres psql -U user -d tiktok_safety_db

# List tables
\dt

# View schema
\d processed_results

# Exit
\q
```

### MinIO Storage
```bash
# Access MinIO CLI
docker exec -it minio mc alias set local http://localhost:9000 minioadmin minioadmin123

# List buckets
docker exec -it minio mc ls local/

# View bucket contents
docker exec -it minio mc ls local/tiktok-raw-videos/
```

### Kafka Topics
```bash
# List topics
docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092

# Describe topic
docker exec -it kafka kafka-topics --describe \
    --topic raw-video-input \
    --bootstrap-server kafka:9092

# View messages
docker exec -it kafka kafka-console-consumer \
    --topic raw-video-input \
    --from-beginning \
    --max-messages 5 \
    --bootstrap-server kafka:9092
```

### Airflow
```bash
# Check DAG status
curl -u admin:admin http://localhost:8080/api/v1/dags | jq '.dags[].dag_id'

# Trigger DAG manually
curl -X POST -u admin:admin \
    -H "Content-Type: application/json" \
    "http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns" \
    -d '{}'

# Unpause DAG
curl -X PATCH -u admin:admin \
    -H "Content-Type: application/json" \
    "http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR" \
    -d '{"is_paused": false}'
```

---

## Tailscale Remote Access

### Setup Tailscale
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
# Example: 100.69.255.87
```

### Update Configuration for Remote Access
```bash
# Update link_host.sh with Tailscale IP
./link_host.sh

# Or manually update config.py
# MINIO_PUBLIC_ENDPOINT = "http://100.69.255.87:9000"
```

### Firewall Rules (if needed)
```bash
# Allow Tailscale traffic
sudo ufw allow in on tailscale0
sudo ufw allow 8501/tcp  # Dashboard
sudo ufw allow 8080/tcp  # Airflow
sudo ufw allow 9001/tcp  # MinIO Console
```

---

## Troubleshooting

### Common Issues

#### 1. Containers not starting
```bash
# Check logs
docker compose logs -f

# Check specific service
docker logs airflow-webserver --tail 100

# Restart specific service
docker compose restart dashboard
```

#### 2. Database connection errors
```bash
# Check PostgreSQL is running
docker exec postgres pg_isready -U user

# Check connection from dashboard
docker exec dashboard python -c "
from helpers import get_db_engine
engine = get_db_engine()
print(engine.connect())
"
```

#### 3. MinIO access denied
```bash
# Check bucket policy
docker exec minio mc anonymous get local/tiktok-raw-videos

# Set public read policy
docker exec minio mc anonymous set download local/tiktok-raw-videos
```

#### 4. Airflow DAGs not showing
```bash
# Check DAGs folder
docker exec airflow-scheduler ls -la /opt/airflow/dags/

# Trigger DAG parsing
docker exec airflow-scheduler airflow dags list

# Check DAG errors
docker exec airflow-scheduler airflow dags list-import-errors
```

#### 5. Dashboard can't play videos
```bash
# Check MinIO public endpoint
curl -I http://localhost:9000/tiktok-raw-videos/

# Check video exists
docker exec minio mc ls local/tiktok-raw-videos/ | head -5

# Verify URL generation
docker exec dashboard python -c "
from helpers import get_video_url
print(get_video_url('test_vid', 'harmful'))
"
```

### Health Check Commands
```bash
# All services health
./start_all.sh status  # Custom command

# Or use docker directly
docker compose ps

# Check network
docker network inspect tiktok-network

# Check volumes
docker volume ls | grep tiktok
```

---

## Upgrade & Maintenance

### Update Containers
```bash
# Pull latest images
docker compose pull

# Rebuild custom images
docker compose build --no-cache

# Restart with new images
docker compose up -d
```

### Backup Database
```bash
# Create backup
docker exec postgres pg_dump -U user tiktok_safety_db > backup.sql

# Restore backup
cat backup.sql | docker exec -i postgres psql -U user -d tiktok_safety_db
```

### Clean Up
```bash
# Stop all containers
docker compose down

# Remove all data (CAREFUL!)
docker compose down -v

# Clean unused resources
docker system prune -a
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | Database hostname |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `tiktok_safety_db` | Database name |
| `POSTGRES_USER` | `user` | Database user |
| `POSTGRES_PASSWORD` | `password` | Database password |
| `MINIO_ENDPOINT` | `minio:9000` | MinIO internal endpoint |
| `MINIO_PUBLIC_ENDPOINT` | `http://localhost:9000` | MinIO public URL |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin123` | MinIO secret key |
| `MINIO_BUCKET_VIDEOS` | `tiktok-raw-videos` | Video bucket name |
| `KAFKA_BROKER` | `kafka:9092` | Kafka broker address |
| `TEXT_WEIGHT` | `0.6` | Text model weight |
| `VIDEO_WEIGHT` | `0.4` | Video model weight |
| `DECISION_THRESHOLD` | `0.5` | Classification threshold |
