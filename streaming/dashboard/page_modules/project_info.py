"""
Project Info Page - Architecture & Pipeline Documentation
"""

import streamlit as st
from helpers import render_header
from config import EXTERNAL_URLS


def render_project_info():
    """Render the project information page"""
    render_header(
        title="Project Info",
        subtitle="Kiến trúc hệ thống và tài liệu kỹ thuật Big Data Pipeline.",
        icon="📚",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🏗️ Architecture", "📊 Data Pipeline", "🤖 AI Models", "📖 Documentation"]
    )

    with tab1:
        _render_architecture()

    with tab2:
        _render_data_pipeline()

    with tab3:
        _render_ai_models()

    with tab4:
        _render_documentation()


def _render_architecture():
    """Render system architecture diagram"""
    st.subheader("🏗️ Kiến trúc Hệ thống")

    st.markdown(
        """
    ### High-Level Architecture
    
    Hệ thống **TikTok Harmful Content Detection** được xây dựng theo kiến trúc **Lambda Architecture** 
    kết hợp **Batch Processing** và **Stream Processing**.
    """
    )

    # Architecture Diagram using Mermaid
    st.markdown(
        """
    ```mermaid
    graph TB
        subgraph "📥 Data Ingestion"
            A[TikTok API] --> B[Crawler Service]
            B --> C[MinIO Storage]
        end
        
        subgraph "📡 Message Queue"
            C --> D[Kafka Producer]
            D --> E[Kafka Broker]
        end
        
        subgraph "⚡ Stream Processing"
            E --> F[Spark Streaming]
            F --> G[AI Models]
        end
        
        subgraph "🤖 AI Pipeline"
            G --> H[Text Model]
            G --> I[Video Model]
            G --> J[Audio Model]
            H --> K[Fusion Layer]
            I --> K
            J --> K
        end
        
        subgraph "💾 Data Storage"
            K --> L[PostgreSQL]
            L --> M[Dashboard]
        end
        
        subgraph "🔧 Orchestration"
            N[Airflow] --> B
            N --> F
        end
    ```
    """
    )

    st.info("📌 Diagram trên mô tả luồng dữ liệu từ TikTok → AI Analysis → Dashboard")

    # Component Details
    st.markdown("---")
    st.markdown("### 🧩 Chi tiết các Components")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        #### 📥 Data Ingestion Layer
        | Component | Technology | Purpose |
        |-----------|------------|---------|
        | Crawler | Python + Selenium | Thu thập video TikTok |
        | Storage | MinIO (S3-compatible) | Lưu trữ video/audio |
        | Producer | kafka-python | Gửi events vào Kafka |
        
        #### 📡 Message Queue Layer
        | Component | Technology | Purpose |
        |-----------|------------|---------|
        | Broker | Apache Kafka | Message streaming |
        | Zookeeper | Apache Zookeeper | Cluster coordination |
        """
        )

    with col2:
        st.markdown(
            """
        #### ⚡ Processing Layer
        | Component | Technology | Purpose |
        |-----------|------------|---------|
        | Streaming | Apache Spark | Real-time processing |
        | Batch | Apache Spark | Large-scale processing |
        
        #### 💾 Storage Layer
        | Component | Technology | Purpose |
        |-----------|------------|---------|
        | Database | PostgreSQL | Structured data |
        | Object Store | MinIO | Unstructured data |
        | Cache | Redis (optional) | Fast access cache |
        """
        )


def _render_data_pipeline():
    """Render data pipeline documentation"""
    st.subheader("📊 Data Pipeline Flow")

    st.markdown(
        """
    ### Pipeline Stages
    
    Dữ liệu đi qua **5 giai đoạn chính** từ thu thập đến hiển thị kết quả:
    """
    )

    # Stage 1
    with st.expander("**1️⃣ Stage 1: Data Collection (Crawler)**", expanded=True):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                    CRAWLER SERVICE                          │
        ├─────────────────────────────────────────────────────────────┤
        │  Input:  Hashtag list (e.g., #harmful, #violence, #safe)   │
        │  Process: Selenium WebDriver → TikTok scraping             │
        │  Output:  MP4 videos + metadata (JSON)                      │
        │  Storage: MinIO bucket (tiktok-videos/)                     │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Files involved:**
        - `crawl_tiktok_links_update_v1.py`
        - `ScrapingVideoTiktok.py`
        
        **Output structure:**
        ```
        MinIO:tiktok-videos/
        ├── harmful/
        │   ├── video_001.mp4
        │   └── video_002.mp4
        └── not_harmful/
            ├── video_003.mp4
            └── video_004.mp4
        ```
        """
        )

    # Stage 2
    with st.expander("**2️⃣ Stage 2: Event Streaming (Kafka)**"):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                    KAFKA PIPELINE                           │
        ├─────────────────────────────────────────────────────────────┤
        │  Producer: Sends video metadata to topic                    │
        │  Topic:    tiktok-videos-topic                              │
        │  Consumer: Spark Streaming subscriber                       │
        │  Format:   JSON (video_id, path, timestamp, label)          │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Message Schema:**
        ```json
        {
            "video_id": "7123456789",
            "video_path": "s3://tiktok-videos/harmful/video_001.mp4",
            "timestamp": "2024-01-15T10:30:00Z",
            "label": "harmful",
            "metadata": {...}
        }
        ```
        """
        )

    # Stage 3
    with st.expander("**3️⃣ Stage 3: Stream Processing (Spark)**"):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                  SPARK STREAMING                            │
        ├─────────────────────────────────────────────────────────────┤
        │  Input:    Kafka topic subscription                         │
        │  Process:  Micro-batch processing (5s window)               │
        │  Transform: Download video → Extract features               │
        │  Output:   Feature vectors for AI models                    │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Processing steps:**
        1. Receive Kafka message
        2. Download video from MinIO
        3. Extract audio track (ffmpeg)
        4. Generate text transcript (Whisper)
        5. Extract video frames (OpenCV)
        6. Send to AI models
        """
        )

    # Stage 4
    with st.expander("**4️⃣ Stage 4: AI Analysis (Multi-Modal)**"):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                  AI MODEL ENSEMBLE                          │
        ├─────────────────────────────────────────────────────────────┤
        │  Text Model:   PhoBERT (Vietnamese NLP)                     │
        │  Video Model:  TimeSformer / SlowFast                       │
        │  Audio Model:  Wav2Vec2                                     │
        │  Fusion:       Late fusion (weighted average)               │
        │  Output:       Harmful probability [0-1]                    │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Decision logic:**
        ```python
        avg_score = (text_score * 0.4 + video_score * 0.4 + audio_score * 0.2)
        verdict = "Harmful" if avg_score >= 0.5 else "Safe"
        ```
        """
        )

    # Stage 5
    with st.expander("**5️⃣ Stage 5: Results Storage & Visualization**"):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                  DATA SINK                                  │
        ├─────────────────────────────────────────────────────────────┤
        │  Database:  PostgreSQL (processed_results table)            │
        │  Dashboard: Streamlit real-time visualization               │
        │  Alerts:    (Optional) Webhook notifications                │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Database schema:**
        ```sql
        CREATE TABLE processed_results (
            id SERIAL PRIMARY KEY,
            video_id VARCHAR(50),
            text_score FLOAT,
            video_score FLOAT,
            audio_score FLOAT,
            avg_score FLOAT,
            text_verdict VARCHAR(20),
            video_verdict VARCHAR(20),
            audio_verdict VARCHAR(20),
            category VARCHAR(20),
            transcript TEXT,
            processed_at TIMESTAMP
        );
        ```
        """
        )


def _render_ai_models():
    """Render AI models documentation"""
    st.subheader("🤖 AI Models Documentation")

    st.markdown(
        """
    ### Multi-Modal Harmful Content Detection
    
    Hệ thống sử dụng **3 AI models** phân tích song song và kết hợp kết quả:
    """
    )

    # Model cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            min-height: 280px;
            overflow: visible;
        ">
            <h3 style="color: white; margin: 0 0 10px 0;">📝 Text Model</h3>
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> PhoBERT-base</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> Transcript (Vietnamese)</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Harmful probability</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Weight:</b> 40%</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Phân tích ngữ nghĩa văn bản, phát hiện từ khóa độc hại, 
                hate speech, và nội dung không phù hợp.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px;
            border-radius: 12px;
            min-height: 280px;
            overflow: visible;
        ">
            <h3 style="color: white; margin: 0 0 10px 0;">🎬 Video Model</h3>
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> TimeSformer</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> Video frames (16 fps)</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Harmful probability</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Weight:</b> 40%</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Phân tích hình ảnh, phát hiện bạo lực, nội dung người lớn,
                và các hành vi nguy hiểm.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 20px;
            border-radius: 12px;
            min-height: 280px;
            overflow: visible;
        ">
            <h3 style="color: white; margin: 0 0 10px 0;">🔊 Audio Model</h3>
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> Wav2Vec2</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> Audio waveform</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Harmful probability</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Weight:</b> 20%</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Phân tích âm thanh, phát hiện tiếng la hét, âm thanh bạo lực,
                và ngữ điệu tiêu cực.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Fusion explanation
    st.markdown("---")
    st.markdown("### 🔗 Late Fusion Strategy")

    st.markdown(
        """
    **Cách kết hợp kết quả từ 3 models:**
    
    ```python
    def late_fusion(text_score, video_score, audio_score):
        # Weighted average fusion
        weights = {"text": 0.4, "video": 0.4, "audio": 0.2}
        
        avg_score = (
            text_score * weights["text"] +
            video_score * weights["video"] +
            audio_score * weights["audio"]
        )
        
        # Decision threshold
        threshold = 0.5
        verdict = "Harmful" if avg_score >= threshold else "Safe"
        
        return avg_score, verdict
    ```
    
    **Tại sao chọn tỷ lệ 40-40-20?**
    - Text (40%): Chứa nhiều thông tin ngữ nghĩa nhất
    - Video (40%): Quan trọng cho phát hiện visual
    - Audio (20%): Bổ sung thông tin, nhưng nhiễu hơn
    """
    )


def _render_documentation():
    """Render project documentation"""
    st.subheader("📖 Tài liệu Dự án")

    st.markdown(
        """
    ### 📁 Project Structure
    
    ```
    UIT-SE363-Big-Data-Pipeline/
    ├── 📂 streaming/                # Main application
    │   ├── 📂 dashboard/            # Streamlit dashboard
    │   │   ├── app.py              # Main entry point
    │   │   ├── config.py           # Configuration
    │   │   ├── styles.py           # CSS styles
    │   │   ├── helpers.py          # Utility functions
    │   │   └── 📂 pages/           # Page modules
    │   │
    │   ├── 📂 airflow/              # Workflow orchestration
    │   │   ├── dags/               # DAG definitions
    │   │   └── Dockerfile.airflow
    │   │
    │   ├── 📂 tiktok-pipeline/      # Core pipeline code
    │   │   ├── producer/           # Kafka producer
    │   │   ├── consumer/           # Spark consumer
    │   │   └── models/             # AI model wrappers
    │   │
    │   └── docker-compose.yml      # Service orchestration
    │
    ├── 📂 train_eval_module/        # Model training
    │   ├── text/                   # Text model training
    │   ├── video/                  # Video model training
    │   └── audio/                  # Audio model training
    │
    └── 📂 processed_data/           # Training datasets
    ```
    """
    )

    st.markdown("---")
    st.markdown("### 🚀 Quick Start Guide")

    st.code(
        """
# 1. Clone repository
git clone https://github.com/your-repo/UIT-SE363-Big-Data-Pipeline.git
cd UIT-SE363-Big-Data-Pipeline/streaming

# 2. Start all services
docker-compose up -d

# 3. Access Dashboard
open http://localhost:8501

# 4. Run Pipeline
# Via Dashboard → System Operations → Trigger DAGs
# Or via Airflow UI: http://localhost:8080
    """,
        language="bash",
    )

    st.markdown("---")
    st.markdown("### 🔗 Useful Links")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.link_button(
            "📊 Dashboard", EXTERNAL_URLS["dashboard"], use_container_width=True
        )
        st.link_button("🌐 Airflow", EXTERNAL_URLS["airflow"], use_container_width=True)

    with col2:
        st.link_button(
            "📦 MinIO", EXTERNAL_URLS["minio_console"], use_container_width=True
        )
        st.link_button(
            "📈 Spark UI", EXTERNAL_URLS["spark_ui"], use_container_width=True
        )

    with col3:
        st.link_button(
            "📚 GitHub", "https://github.com/your-repo", use_container_width=True
        )
        st.link_button(
            "📖 Docs", "https://docs.your-project.com", use_container_width=True
        )

    st.markdown("---")
    st.markdown("### 👥 Team")

    st.markdown(
        """
    **UIT - SE363 Big Data Platform Application Development**
    
    | Role | Name | Student ID |
    |------|------|------------|
    | Team Lead | [Your Name] | [ID] |
    | Backend Dev | [Name] | [ID] |
    | AI Engineer | [Name] | [ID] |
    | DevOps | [Name] | [ID] |
    """
    )
