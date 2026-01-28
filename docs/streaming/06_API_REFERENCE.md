# 📖 API Reference

## Overview

Tài liệu này mô tả các internal APIs, endpoints, và helper functions trong hệ thống.

---

## 1. Dashboard Internal APIs

### 1.1 helpers.py Functions

#### Database Functions

```python
def get_db_engine():
    """
    Create SQLAlchemy engine for PostgreSQL connection.
    
    Returns:
        Engine: SQLAlchemy engine instance
        
    Environment Variables:
        - POSTGRES_HOST: Database host (default: postgres)
        - POSTGRES_PORT: Database port (default: 5432)
        - POSTGRES_DB: Database name (default: tiktok_safety_db)
        - POSTGRES_USER: Database user (default: user)
        - POSTGRES_PASSWORD: Database password (default: password)
        
    Example:
        >>> engine = get_db_engine()
        >>> with engine.connect() as conn:
        ...     result = conn.execute("SELECT 1")
    """
```

```python
def get_data():
    """
    Get all processed results from database.
    
    Returns:
        DataFrame: Pandas DataFrame with all records from processed_results table
        
    Columns:
        - video_id (str): Unique video identifier
        - Category (str): 'harmful' or 'not_harmful'
        - avg_score (float): Average of all model scores
        - text_score (float): Text model prediction score
        - video_score (float): Video model prediction score
        - audio_score (float): Audio model prediction score
        - transcript (str): Video transcript/captions
        - processed_at (datetime): Processing timestamp
        
    Example:
        >>> df = get_data()
        >>> print(f"Total records: {len(df)}")
    """
```

```python
def get_all_data_paginated(page=1, per_page=50, category_filter=None, search_query=None):
    """
    Get paginated data with optional filters.
    
    Args:
        page (int): Page number (1-indexed)
        per_page (int): Records per page
        category_filter (str): Filter by 'harmful', 'not_harmful', or None for all
        search_query (str): Search in video_id or transcript
        
    Returns:
        tuple: (DataFrame, total_count, total_pages)
        
    Example:
        >>> df, total, pages = get_all_data_paginated(page=1, per_page=20, category_filter='harmful')
    """
```

```python
def get_recent_logs(limit=100):
    """
    Get recent system logs from database.
    
    Args:
        limit (int): Maximum number of logs to retrieve
        
    Returns:
        list[dict]: List of log entries with keys: timestamp, level, source, message
        
    Example:
        >>> logs = get_recent_logs(50)
        >>> for log in logs:
        ...     print(f"[{log['level']}] {log['message']}")
    """
```

#### Airflow API Functions

```python
def get_dag_status(dag_id):
    """
    Get latest DAG run status from Airflow API.
    
    Args:
        dag_id (str): DAG identifier (e.g., '1_TIKTOK_ETL_COLLECTOR')
        
    Returns:
        str: Status string ('success', 'running', 'failed', 'queued', 'unknown')
        
    API Endpoint:
        GET /api/v1/dags/{dag_id}/dagRuns?limit=1&order_by=-execution_date
        
    Example:
        >>> status = get_dag_status('1_TIKTOK_ETL_COLLECTOR')
        >>> print(f"DAG status: {status}")
    """
```

```python
def trigger_dag(dag_id):
    """
    Trigger a DAG run via Airflow API.
    Auto-unpauses DAG if it's paused before triggering.
    
    Args:
        dag_id (str): DAG identifier
        
    Returns:
        tuple: (success: bool, message: str)
        
    API Endpoints:
        - PATCH /api/v1/dags/{dag_id} (unpause)
        - POST /api/v1/dags/{dag_id}/dagRuns (trigger)
        
    Example:
        >>> success, msg = trigger_dag('1_TIKTOK_ETL_COLLECTOR')
        >>> if success:
        ...     print(f"Triggered: {msg}")
    """
```

```python
def clear_queued_dag_runs(dag_id):
    """
    Clear all queued DAG runs for a specific DAG.
    
    Args:
        dag_id (str): DAG identifier
        
    Returns:
        tuple: (success: bool, message: str, cleared_count: int)
        
    API Endpoints:
        - GET /api/v1/dags/{dag_id}/dagRuns?state=queued
        - DELETE /api/v1/dags/{dag_id}/dagRuns/{run_id}
        
    Example:
        >>> success, msg, count = clear_queued_dag_runs('1_TIKTOK_ETL_COLLECTOR')
        >>> print(f"Cleared {count} queued runs")
    """
```

```python
def get_dag_info(dag_id):
    """
    Get DAG information including paused status.
    
    Args:
        dag_id (str): DAG identifier
        
    Returns:
        dict: DAG info with keys: dag_id, is_paused, description, schedule_interval
        
    API Endpoint:
        GET /api/v1/dags/{dag_id}
        
    Example:
        >>> info = get_dag_info('1_TIKTOK_ETL_COLLECTOR')
        >>> print(f"Paused: {info['is_paused']}")
    """
```

```python
def get_dag_run_history(dag_id, limit=10):
    """
    Get DAG run history with details.
    
    Args:
        dag_id (str): DAG identifier
        limit (int): Maximum number of runs to retrieve
        
    Returns:
        list[dict]: List of DAG runs with keys:
            dag_run_id, state, execution_date, start_date, end_date
            
    API Endpoint:
        GET /api/v1/dags/{dag_id}/dagRuns?limit={limit}&order_by=-execution_date
        
    Example:
        >>> history = get_dag_run_history('1_TIKTOK_ETL_COLLECTOR', 5)
        >>> for run in history:
        ...     print(f"{run['dag_run_id']}: {run['state']}")
    """
```

```python
def get_task_instances(dag_id, dag_run_id):
    """
    Get task instances for a specific DAG run.
    
    Args:
        dag_id (str): DAG identifier
        dag_run_id (str): Specific DAG run ID
        
    Returns:
        list[dict]: List of tasks with keys:
            task_id, state, start_date, end_date, duration, try_number
            
    API Endpoint:
        GET /api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances
        
    Example:
        >>> tasks = get_task_instances('1_TIKTOK_ETL_COLLECTOR', 'manual__2025-01-01')
        >>> for task in tasks:
        ...     print(f"{task['task_id']}: {task['state']}")
    """
```

```python
def get_task_logs(dag_id, dag_run_id, task_id, try_number=1):
    """
    Get logs for a specific task instance.
    
    Args:
        dag_id (str): DAG identifier
        dag_run_id (str): DAG run ID
        task_id (str): Task identifier
        try_number (int): Attempt number (default 1)
        
    Returns:
        str: Task log content
        
    API Endpoint:
        GET /api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}
        
    Example:
        >>> logs = get_task_logs('1_TIKTOK_ETL_COLLECTOR', 'manual__2025-01-01', 'crawl_task', 1)
        >>> print(logs[-1000:])  # Last 1000 chars
    """
```

```python
def get_dag_run_history(dag_id, limit=10):
    """
    Get DAG run history.
    
    Args:
        dag_id (str): DAG identifier
        limit (int): Maximum number of runs to retrieve
        
    Returns:
        list[dict]: List of DAG runs with keys: 
            dag_run_id, state, start_date, end_date, execution_date
            
    API Endpoint:
        GET /api/v1/dags/{dag_id}/dagRuns?limit={limit}&order_by=-execution_date
        
    Example:
        >>> history = get_dag_run_history('1_TIKTOK_ETL_COLLECTOR', 5)
        >>> for run in history:
        ...     print(f"{run['dag_run_id']}: {run['state']}")
    """
```

#### Utility Functions

```python
def get_video_url(video_id, label):
    """
    Generate MinIO URL for a video file.
    
    Args:
        video_id (str): Video identifier (without .mp4 extension)
        label (str): 'harmful' or 'not_harmful' (folder name)
        
    Returns:
        str: Full MinIO URL for the video
        
    URL Format:
        {MINIO_PUBLIC_ENDPOINT}/{BUCKET}/{label}/{video_id}.mp4
        
    Example:
        >>> url = get_video_url('abc123', 'harmful')
        >>> # Returns: http://100.69.255.87:9000/tiktok-raw-videos/harmful/abc123.mp4
    """
```

```python
def find_blacklist_hits(text):
    """
    Find blacklist keyword matches in text.
    
    Args:
        text (str): Text to search for blacklist keywords
        
    Returns:
        list[str]: List of matched keywords
        
    Blacklist Categories:
        - Violence: bạo lực, giết, đánh, máu, chết
        - Adult: sex, khỏa thân, gợi cảm
        - Drugs: ma túy, thuốc lắc, cần sa
        - Hate: kỳ thị, phân biệt
        
    Example:
        >>> hits = find_blacklist_hits("nội dung bạo lực quá mức")
        >>> print(hits)  # ['bạo lực']
    """
```

```python
def highlight_keywords(text, keywords):
    """
    Highlight keywords in text with HTML styling.
    
    Args:
        text (str): Original text
        keywords (list[str]): Keywords to highlight
        
    Returns:
        str: HTML string with highlighted keywords
        
    Example:
        >>> html = highlight_keywords("test content", ["test"])
        >>> # Returns: '<span style="background: #ff0">test</span> content'
    """
```

```python
def infer_streaming_engine_state(df):
    """
    Infer AI engine state from recent data patterns.
    
    Args:
        df (DataFrame): Recent processed results
        
    Returns:
        str: State ('Idle', 'Consuming', 'Processing', 'Done', 'Error')
        
    Logic:
        - No recent data (>10min) → 'Idle'
        - New data in last 1min → 'Processing'
        - Data in last 5min → 'Consuming'
        - Otherwise → 'Done'
        
    Example:
        >>> state = infer_streaming_engine_state(df)
        >>> print(f"Engine state: {state}")
    """
```

```python
def render_header(title, subtitle, icon="🎯"):
    """
    Render standardized page header.
    
    Args:
        title (str): Main title text
        subtitle (str): Subtitle/description
        icon (str): Emoji icon (default: 🎯)
        
    Returns:
        None (renders directly to Streamlit)
        
    Example:
        >>> render_header("Analytics", "Real-time metrics", "📊")
    """
```

```python
def get_container_logs(container_name, num_lines=50):
    """
    Get Docker container logs.
    
    Args:
        container_name (str): Docker container name
        num_lines (int): Number of log lines to retrieve
        
    Returns:
        str: Container log output
        
    Example:
        >>> logs = get_container_logs('dashboard', 100)
    """
```

```python
def get_system_stats():
    """
    Get system resource statistics.
    
    Returns:
        dict: System stats with keys:
            - cpu_percent (float): CPU usage percentage
            - memory_percent (float): Memory usage percentage
            - disk_percent (float): Disk usage percentage
            
    Example:
        >>> stats = get_system_stats()
        >>> print(f"CPU: {stats['cpu_percent']}%")
    """
```

---

## 2. External APIs Used

### 2.1 Airflow REST API

**Base URL**: `http://airflow-webserver:8080/api/v1`

**Authentication**: Basic Auth (`admin:admin`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dags` | GET | List all DAGs |
| `/dags/{dag_id}` | GET | Get DAG details |
| `/dags/{dag_id}` | PATCH | Update DAG (pause/unpause) |
| `/dags/{dag_id}/dagRuns` | GET | List DAG runs |
| `/dags/{dag_id}/dagRuns` | POST | Trigger new DAG run |
| `/dags/{dag_id}/dagRuns/{run_id}` | DELETE | Delete DAG run |

**Example Requests**:
```bash
# List DAGs
curl -u admin:admin http://localhost:8080/api/v1/dags | jq '.dags[].dag_id'

# Trigger DAG
curl -X POST -u admin:admin \
    -H "Content-Type: application/json" \
    http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns \
    -d '{}'

# Unpause DAG
curl -X PATCH -u admin:admin \
    -H "Content-Type: application/json" \
    http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR \
    -d '{"is_paused": false}'
```

### 2.2 MinIO S3 API

**Endpoint**: `http://minio:9000` (internal) / `http://100.69.255.87:9000` (external)

**Authentication**: Access Key / Secret Key

| Operation | Method | Path |
|-----------|--------|------|
| List buckets | GET | `/` |
| List objects | GET | `/{bucket}` |
| Get object | GET | `/{bucket}/{key}` |
| Put object | PUT | `/{bucket}/{key}` |

**Public URLs**:
```
http://100.69.255.87:9000/tiktok-raw-videos/harmful/{video_id}.mp4
http://100.69.255.87:9000/tiktok-raw-videos/not_harmful/{video_id}.mp4
```

### 2.3 Kafka

**Broker**: `kafka:9092`

**Topics**:
| Topic | Purpose | Partitions |
|-------|---------|------------|
| `raw-video-input` | Video metadata events | 3 |
| `processing-results` | AI processing results | 3 |

**Message Format (raw-video-input)**:
```json
{
    "video_id": "abc123",
    "url": "https://tiktok.com/...",
    "label": "harmful",
    "hashtag": "#example",
    "description": "Video description",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 3. Database Schema

### 3.1 processed_results Table

```sql
CREATE TABLE processed_results (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) UNIQUE NOT NULL,
    "Category" VARCHAR(50) NOT NULL,  -- 'harmful' or 'not_harmful'
    avg_score FLOAT,
    text_score FLOAT,
    video_score FLOAT,
    audio_score FLOAT DEFAULT 0.0,
    transcript TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_category ("Category"),
    INDEX idx_processed_at (processed_at),
    INDEX idx_avg_score (avg_score)
);
```

### 3.2 system_logs Table

```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,  -- 'INFO', 'WARNING', 'ERROR'
    source VARCHAR(100),
    message TEXT,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level)
);
```

### 3.3 Sample Queries

```sql
-- Get harmful content statistics
SELECT 
    "Category",
    COUNT(*) as count,
    AVG(avg_score) as avg_risk_score
FROM processed_results
GROUP BY "Category";

-- Get recent processing activity
SELECT 
    DATE_TRUNC('hour', processed_at) as hour,
    COUNT(*) as videos_processed
FROM processed_results
WHERE processed_at > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;

-- Find high-risk content
SELECT video_id, avg_score, text_score, video_score
FROM processed_results
WHERE "Category" = 'harmful'
AND avg_score > 0.8
ORDER BY avg_score DESC
LIMIT 20;

-- Search transcripts
SELECT video_id, transcript, avg_score
FROM processed_results
WHERE transcript ILIKE '%keyword%';
```

---

## 4. Configuration Reference

### 4.1 config.py

```python
# Database Configuration
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "tiktok_safety_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

# MinIO Configuration
MINIO_CONF = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "public_endpoint": os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    "bucket": os.getenv("MINIO_BUCKET_VIDEOS", "tiktok-raw-videos"),
}

# Airflow Configuration
AIRFLOW_CONFIG = {
    "api_url": os.getenv("AIRFLOW_API_URL", "http://airflow-webserver:8080/api/v1"),
    "username": os.getenv("AIRFLOW_USERNAME", "admin"),
    "password": os.getenv("AIRFLOW_PASSWORD", "admin"),
}

# AI Model Weights
AI_CONFIG = {
    "text_weight": float(os.getenv("TEXT_WEIGHT", "0.6")),
    "video_weight": float(os.getenv("VIDEO_WEIGHT", "0.4")),
    "audio_weight": float(os.getenv("AUDIO_WEIGHT", "0.0")),
    "decision_threshold": float(os.getenv("DECISION_THRESHOLD", "0.5")),
}

# External URLs (Tailscale)
def extract_host_from_minio_endpoint():
    """Extract host from MINIO_PUBLIC_ENDPOINT."""
    endpoint = MINIO_CONF["public_endpoint"]
    from urllib.parse import urlparse
    return urlparse(endpoint).hostname or "localhost"

PUBLIC_HOST = extract_host_from_minio_endpoint()

EXTERNAL_URLS = {
    "airflow": f"http://{PUBLIC_HOST}:8080",
    "minio_console": f"http://{PUBLIC_HOST}:9001",
    "spark_ui": f"http://{PUBLIC_HOST}:9090",
    "dashboard": f"http://{PUBLIC_HOST}:8501",
}

# DAG IDs
DAG_IDS = {
    "crawler": "1_TIKTOK_ETL_COLLECTOR",
    "streaming": "2_TIKTOK_STREAMING_PIPELINE",
}
```

---

## 5. Error Codes

### Dashboard Errors

| Code | Message | Cause | Solution |
|------|---------|-------|----------|
| `DB_001` | Database connection failed | PostgreSQL not running | Check `docker ps` for postgres |
| `DB_002` | Query execution failed | Invalid SQL | Check SQL syntax |
| `API_001` | Airflow API unreachable | Webserver down | Restart airflow-webserver |
| `API_002` | DAG trigger failed | DAG not found | Check DAG exists in Airflow |
| `MINIO_001` | Video not found | Invalid path | Check video_id and label |
| `MINIO_002` | Access denied | Wrong credentials | Check MINIO_ACCESS_KEY |

### HTTP Status Codes

| Code | Meaning | Dashboard Context |
|------|---------|-------------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Wrong Airflow credentials |
| 404 | Not Found | DAG/video not found |
| 500 | Server Error | Internal service error |
| 503 | Unavailable | Service not running |

---

## 6. Rate Limits & Performance

### Airflow API
- **Rate Limit**: 100 requests/minute
- **Timeout**: 30 seconds
- **Retry**: 3 attempts with exponential backoff

### MinIO
- **Max Connections**: 100 concurrent
- **Download Speed**: Limited by network
- **File Size Limit**: 5GB per object

### PostgreSQL
- **Max Connections**: 100
- **Query Timeout**: 60 seconds
- **Connection Pool**: 10 connections

### Dashboard
- **Refresh Rate**: 5 seconds (auto-refresh disabled by default)
- **Page Size**: 12-50 items per page
- **Cache TTL**: 60 seconds for data queries

---

## 7. SDK Examples

### Python Client
```python
import requests
from config import AIRFLOW_CONFIG, DB_CONFIG
from sqlalchemy import create_engine

class TikTokSafetyClient:
    def __init__(self):
        self.airflow_url = AIRFLOW_CONFIG["api_url"]
        self.auth = (AIRFLOW_CONFIG["username"], AIRFLOW_CONFIG["password"])
        self.engine = create_engine(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        )
    
    def trigger_pipeline(self, dag_id):
        """Trigger a pipeline DAG."""
        resp = requests.post(
            f"{self.airflow_url}/dags/{dag_id}/dagRuns",
            auth=self.auth,
            json={}
        )
        return resp.json()
    
    def get_results(self, limit=100):
        """Get processed results."""
        import pandas as pd
        return pd.read_sql(
            f"SELECT * FROM processed_results ORDER BY processed_at DESC LIMIT {limit}",
            self.engine
        )
    
    def get_statistics(self):
        """Get content statistics."""
        import pandas as pd
        return pd.read_sql("""
            SELECT 
                "Category",
                COUNT(*) as count,
                AVG(avg_score) as avg_score
            FROM processed_results
            GROUP BY "Category"
        """, self.engine)

# Usage
client = TikTokSafetyClient()
client.trigger_pipeline('1_TIKTOK_ETL_COLLECTOR')
df = client.get_results(50)
stats = client.get_statistics()
```

### cURL Examples
```bash
# Get all DAGs
curl -s -u admin:admin http://localhost:8080/api/v1/dags | jq

# Trigger crawler
curl -X POST -u admin:admin \
    -H "Content-Type: application/json" \
    http://localhost:8080/api/v1/dags/1_TIKTOK_ETL_COLLECTOR/dagRuns \
    -d '{}'

# Get video URL
VIDEO_ID="abc123"
LABEL="harmful"
echo "http://100.69.255.87:9000/tiktok-raw-videos/${LABEL}/${VIDEO_ID}.mp4"

# Query database
docker exec postgres psql -U user -d tiktok_safety_db -c "SELECT COUNT(*) FROM processed_results"
```
