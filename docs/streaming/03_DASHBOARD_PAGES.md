# 📊 Dashboard Pages Documentation

## Overview

Streamlit Dashboard bao gồm **5 pages** chính, được tổ chức theo sidebar navigation.

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ TikTok Safety Dashboard                                     │
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                               │
│  📊 Analytics   │   [Current Page Content]                      │
│  ⚙️ Operations  │                                               │
│  🔍 Audit       │                                               │
│  📚 Info        │                                               │
│  🗄️ Database    │                                               │
│                 │                                               │
├─────────────────┴───────────────────────────────────────────────┤
│  © 2024 TikTok Safety | Powered by Streamlit                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Page 1: 📊 Analytics Dashboard

**File**: `page_modules/dashboard_monitor.py`

### Purpose
Hiển thị thống kê real-time và KPIs về các video đã được phân tích.

### Components

#### 1. KPI Metrics Row
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 📹 Total     │ ⚠️ Harmful   │ ✅ Safe      │ 🎯 Risk      │
│ Processed    │ Detected     │ Content      │ Score        │
│    413       │    191       │    222       │   4.6/10     │
│  +50 (1h)    │   46.2%      │   53.8%      │  Medium      │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

#### 2. Charts Row
| Chart | Type | Description |
|-------|------|-------------|
| Category Distribution | Donut Pie | Tỷ lệ Harmful vs Safe |
| Timeline | Area Chart | Video xử lý theo thời gian |

#### 3. Score Distribution Row
| Chart | Type | Description |
|-------|------|-------------|
| Score Histogram | Histogram | Phân bố avg_score |
| Score Scatter | Scatter Plot | Text vs Video score correlation |

### Functions
```python
def render_dashboard_monitor(df):
    """Main render function"""
    
def render_kpi_metrics(df):
    """Display KPI cards"""
    
def render_charts(df):
    """Render Plotly charts"""
```

### Data Requirements
- `processed_results` table with columns:
  - `video_id`, `Category`, `avg_score`, `text_score`, `video_score`, `processed_at`

---

## Page 2: ⚙️ System Operations

**File**: `page_modules/system_operations.py`

### Purpose
Điều khiển Pipeline, xem trạng thái hệ thống và logs.

### Tabs

#### Tab 1: 🔧 Pipeline Control
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ Quick Actions (ĐÃ ĐƯA LÊN TRÊN)                              │
│  ┌────────────┬────────────┬────────────┬────────────┐          │
│  │ 🔄 Refresh │ 🌐 Airflow │ 📦 MinIO   │ 🗑️ Clear   │          │
│  │   Page     │    UI      │  Console   │  Queued    │          │
│  └────────────┴────────────┴────────────┴────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│  📊 Pipeline Status Summary                                      │
│  ┌──────────────────────────┬──────────────────────────┐        │
│  │  Crawler Pipeline        │  Streaming Pipeline      │        │
│  │  🟢 RUNNING [ACTIVE]     │  🟢 RUNNING [ACTIVE]     │        │
│  └──────────────────────────┴──────────────────────────┘        │
├─────────────────────────────────────────────────────────────────┤
│  🚀 Điều khiển Pipeline (ĐÃ ĐƯA XUỐNG DƯỚI)                     │
│  ┌──────────────────────────┬──────────────────────────────────┐│
│  │  Crawler Pipeline        │  Streaming Pipeline               ││
│  │  • Crawl từ hashtag      │  • Kafka consumer nhận events     ││
│  │  • Download video        │  • Spark streaming xử lý          ││
│  │  • Extract metadata      │  • AI Models phân loại            ││
│  │  [🚀 KÍCH HOẠT CRAWLER]  │  [⚡ KÍCH HOẠT STREAMING]         ││
│  └──────────────────────────┴──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 2: 📊 Status Monitor (MỚI - CHI TIẾT TASK LOGS)
- Streaming Engine State (Idle/Consuming/Processing/Done/Error)
- **DAG Run History với Task Logs chi tiết**
  - Chọn DAG từ dropdown
  - Xem lịch sử 5 runs gần nhất
  - Expandable sections cho mỗi run
  - Danh sách tasks với status (✅ success, 🔄 running, ❌ failed)
  - **Button "📜 Xem Logs"** để xem chi tiết logs của từng task

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 DAG Run History & Task Logs                                  │
│  ────────────────────────────────────────────────────────────── │
│  Chọn DAG: [🕷️ Crawler Pipeline ▼]                               │
│  ────────────────────────────────────────────────────────────── │
│  ▼ 🔴 manual__2025-01-01T10:30:00 - FAILED                      │
│    │  Start: 2025-01-01 10:30:00                                │
│    │  End: 2025-01-01 10:35:00                                  │
│    │  Tasks:                                                    │
│    │    ✅ monitor_db_health    success   2.1s                  │
│    │    ❌ crawl_tiktok_links   failed    180.5s                │
│    │    [📜 Xem Logs: crawl_tiktok_links]                       │
│    └────────────────────────────────────────────────────────── │
│  ► 🟢 manual__2025-01-01T09:00:00 - SUCCESS                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Tab 3: 📋 System Logs
- Log source selector (PostgreSQL, MinIO, Airflow, Kafka, Spark)
- Log viewer with filtering
- Application logs from database

### Functions
```python
def render_system_operations():
    """Main render function"""

def _render_pipeline_control():
    """Render pipeline trigger buttons"""

def _render_status_monitor():
    """Render status cards"""

def _render_system_logs():
    """Render log viewer"""

def _render_pipeline_status_card(name, status, info):
    """Render colored status card"""

def _render_dag_status_badge(status):
    """Render DAG status badge"""
```

### Key Features
- **Auto-unpause DAGs**: `trigger_dag()` tự động unpause trước khi trigger
- **Clear Queued**: Xóa các DAG runs đang queued
- **Inline Status**: Hiển thị status ngay sau khi trigger

---

## Page 3: 🔍 Content Audit

**File**: `page_modules/content_audit.py`

### Purpose
Kiểm duyệt nội dung video chi tiết với nhiều chế độ xem.

### View Modes

#### 🖼️ Gallery Mode
```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Bộ lọc                                                       │
│  Category: [All ▼]  Score: [0.0 ──●── 1.0]  🔎 Search: [___]    │
├─────────────────────────────────────────────────────────────────┤
│  📊 Hiển thị 413 / 413 videos                                    │
├─────────────────────────────────────────────────────────────────┤
│  🖼️ Video Gallery                                                │
│  Videos per page: [──●── 12]                                     │
│  ────────────────────────────────────────────────────────────── │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ ⚠️Harmful │  │ ✅ Safe  │  │ ⚠️Harmful │                       │
│  │ Score:   │  │ Score:   │  │ Score:   │                       │
│  │ 0.856    │  │ 0.234    │  │ 0.712    │                       │
│  │ [▶ Play] │  │ [▶ Play] │  │ [▶ Play] │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
│  ────────────────────────────────────────────────────────────── │
│  [◀️ Previous]    Page 1 / 35 (413 videos)    [Next Page ▶️]     │
└─────────────────────────────────────────────────────────────────┘
```

#### 📋 Detail View
- Video player embedded
- AI scores breakdown (Text, Video, Audio, Average)
- Transcript với blacklist keyword highlighting
- Metadata display

#### 📊 Table View
- Selectable columns
- Sortable data
- CSV download

### Functions
```python
def render_content_audit(df):
    """Main render function"""

def _render_gallery_mode(df):
    """Render video grid with pagination"""

def _render_video_card(item):
    """Render single video card"""

def _render_detail_view(df):
    """Render detailed single video view"""

def _render_table_view(df):
    """Render table with all data"""
```

### Pagination System
```python
# Session state management
if "gallery_page" not in st.session_state:
    st.session_state.gallery_page = 1
if "items_per_page" not in st.session_state:
    st.session_state.items_per_page = 12

# Navigation buttons
if st.button("Next Page ▶️"):
    st.session_state.gallery_page += 1
    st.rerun()
```

---

## Page 4: 📚 Project Info

**File**: `page_modules/project_info.py`

### Purpose
Tài liệu kiến trúc hệ thống và hướng dẫn sử dụng.

### Tabs

#### Tab 1: 🏗️ Architecture
- Mermaid diagram của system architecture
- Component details tables

#### Tab 2: 📊 Data Pipeline
- 5-stage pipeline documentation
- Code blocks showing data flow

#### Tab 3: 🤖 AI Models
```
┌─────────────────────────────────────────────────────────────────┐
│  AI Model Cards                                                  │
├──────────────────┬──────────────────┬────────────────────────────┤
│  📝 Text Model   │  🎬 Video Model  │  🔊 Audio Model            │
│  ────────────────│  ────────────────│  ────────────────────────  │
│  PhoBERT-base    │  TimeSformer     │  Wav2Vec2                  │
│  Input: Text     │  Input: Frames   │  Input: Waveform           │
│  Weight: 40%     │  Weight: 40%     │  Weight: 20%               │
│                  │                  │  (placeholder)              │
└──────────────────┴──────────────────┴────────────────────────────┘
```

#### Tab 4: 📖 Documentation
- Project structure tree
- Quick start guide
- Useful links (with EXTERNAL_URLS)
- Team information

### Functions
```python
def render_project_info():
    """Main render function"""

def _render_architecture():
    """Render system architecture"""

def _render_data_pipeline():
    """Render pipeline documentation"""

def _render_ai_models():
    """Render AI model cards"""

def _render_documentation():
    """Render project docs"""
```

---

## Page 5: 🗄️ Database Manager

**File**: `page_modules/database_manager.py`

### Purpose
Quản lý và truy vấn database trực tiếp.

### Features

#### SQL Query Editor
- Custom SQL query execution
- Results display in dataframe
- Query history

#### Quick Actions
- View recent records
- Count by category
- Export to CSV

#### Database Stats
- Table sizes
- Index information
- Connection status

### Functions
```python
def render_database_manager():
    """Main render function"""

def execute_query(query):
    """Execute SQL and return results"""

def get_table_stats():
    """Get database statistics"""
```

---

## Helper Functions

**File**: `helpers.py`

### Database Functions
```python
def get_db_engine():
    """Create SQLAlchemy engine"""

def get_data():
    """Get all processed results"""

def get_all_data_paginated(page, per_page, category_filter):
    """Get paginated data with filters"""

def get_recent_logs(limit):
    """Get recent logs from system_logs table"""
```

### Airflow Functions
```python
def get_dag_status(dag_id):
    """Get DAG run status from Airflow API"""

def trigger_dag(dag_id):
    """Trigger DAG (with auto-unpause)"""

def clear_queued_dag_runs(dag_id):
    """Clear all queued DAG runs"""

def get_dag_info(dag_id):
    """Get DAG info including paused status"""
```

### Utility Functions
```python
def get_video_url(vid_id, label):
    """Generate video URL from MinIO"""

def find_blacklist_hits(text):
    """Find blacklist keyword matches"""

def highlight_keywords(text, keywords):
    """Highlight keywords with HTML"""

def infer_streaming_engine_state(df):
    """Infer AI engine state from recent data"""

def render_header(title, subtitle, icon):
    """Render page header"""

def get_container_logs(container_name, num_lines):
    """Get Docker container logs"""

def get_system_stats():
    """Get system resource stats"""
```

---

## Configuration

**File**: `config.py`

```python
# Database Config
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "tiktok_safety_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

# MinIO Config
MINIO_CONF = {
    "public_endpoint": os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000"),
    "bucket": os.getenv("MINIO_BUCKET_VIDEOS", "tiktok-raw-videos"),
}

# External URLs (Tailscale)
PUBLIC_HOST = extract_host_from_minio_endpoint()  # 100.69.255.87
EXTERNAL_URLS = {
    "airflow": f"http://{PUBLIC_HOST}:8080",
    "minio_console": f"http://{PUBLIC_HOST}:9001",
    "spark_ui": f"http://{PUBLIC_HOST}:9090",
    "dashboard": f"http://{PUBLIC_HOST}:8501",
}

# Airflow API
AIRFLOW_API_URL = "http://airflow-webserver:8080/api/v1/dags"
AIRFLOW_AUTH = ("admin", "admin")

# Blacklist Keywords
BLACKLIST_KEYWORDS = [
    "bạo lực", "giết", "đánh", "máu", "chết",
    "sex", "khỏa thân", "gợi cảm", "bikini",
    # ... more keywords
]
```

---

## Styles

**File**: `styles.py`

```css
/* Custom CSS for dashboard */
.video-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
}

.badge-harm {
    background: #FE2C55;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
}

.badge-safe {
    background: #25F4EE;
    color: black;
    padding: 4px 8px;
    border-radius: 4px;
}

/* TikTok-inspired color scheme */
--tiktok-pink: #FE2C55;
--tiktok-cyan: #25F4EE;
--tiktok-dark: #121212;
```
