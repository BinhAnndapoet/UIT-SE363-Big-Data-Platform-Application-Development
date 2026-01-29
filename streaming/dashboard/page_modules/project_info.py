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
            A[TikTok Web] --> B[Crawler Service]
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
            G --> H[CafeBERT - Text]
            G --> I[VideoMAE - Video]
            H --> K[Late Fusion + Attention]
            I --> K
        end
        
        subgraph "💾 Data Storage"
            K --> L[PostgreSQL]
            L --> M[Streamlit Dashboard]
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
        | Crawler | SeleniumWire + TikTok API | Intercept API JSON, lấy link+caption |
        | Downloader | yt-dlp (Mobile emulation) | Tải video từ TikTok |
        | Audio Extract | FFmpeg | Trích xuất audio WAV (chưa dùng AI) |
        | Storage | MinIO (S3-compatible) | Lưu trữ video/audio |
        | Producer | kafka-python | Gửi message vào Kafka |
        
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
        | Streaming | Apache Spark 3.5 | Real-time micro-batch processing |
        | AI Fusion | PyTorch + Transformers | Multi-modal classification |
        
        #### 💾 Storage Layer
        | Component | Technology | Purpose |
        |-----------|------------|---------|
        | Database | PostgreSQL 16 | Structured results |
        | Object Store | MinIO | Video/Audio files |
        | Model Registry | MLflow (optional) | Model versioning |
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
    with st.expander("**1️⃣ Stage 1: Data Collection (Crawler + Downloader)**", expanded=True):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                    CRAWLER + DOWNLOADER                       │
        ├─────────────────────────────────────────────────────────────┤
        │  Step 1: SeleniumWire intercept TikTok API JSON               │
        │  Step 2: Extract video_id, author, caption từ API            │
        │  Step 3: yt-dlp tải video (Mobile iPhone emulation)          │
        │  Step 4: FFmpeg trích xuất audio (.wav)                       │
        │  Step 5: Upload lên MinIO (video + audio buckets)            │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Files chính:**
        - `ingestion/crawler.py` - SeleniumWire + API intercept
        - `ingestion/downloader.py` - yt-dlp mobile emulation
        - `ingestion/main_worker.py` - Pipeline orchestrator
        - `ingestion/audio_processor.py` - FFmpeg audio extraction
        
        **MinIO structure:**
        ```
        tiktok-raw-videos/            tiktok-raw-audios/
        ├── raw/harmful/              ├── raw/harmful/
        │   └── {video_id}.mp4        │   └── {video_id}.wav
        └── raw/safe/                 └── raw/safe/
            └── {video_id}.mp4            └── {video_id}.wav
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
        │  Topic:    tiktok_raw_data                                   │
        │  Producer: main_worker.py (sau khi upload MinIO)            │
        │  Consumer: Spark Structured Streaming                       │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Kafka Message Schema (thực tế):**
        ```json
        {
            "video_id": "7123456789",
            "minio_video_path": "tiktok-raw-videos/raw/harmful/7123456789.mp4",
            "minio_audio_path": "tiktok-raw-audios/raw/harmful/7123456789.wav",
            "clean_text": "Caption đã được làm sạch...",
            "csv_label": "harmful",
            "timestamp": 1705312200.123
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
        │                  SPARK STRUCTURED STREAMING                  │
        ├─────────────────────────────────────────────────────────────┤
        │  Input:    Kafka topic (tiktok_raw_data)                     │
        │  Process:  Micro-batch (maxOffsetsPerTrigger=5)             │
        │  Text:     Lấy từ clean_text (caption, KHÔNG dùng Whisper)  │
        │  Video:    Download từ MinIO → Extract 16 frames            │
        │  Audio:    Chưa sử dụng (dự phòng cho tương lai)            │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Processing steps (thực tế):**
        1. Nhận Kafka message (JSON)
        2. Parse: video_id, minio_video_path, clean_text, csv_label
        3. Download video từ MinIO (boto3)
        4. Decord: Trích 16 frames từ video
        5. **Text đã có sẵn** (caption từ TikTok API, không cần Whisper)
        6. Gửi song song đến AI models
        """
        )

    # Stage 4
    with st.expander("**4️⃣ Stage 4: AI Analysis (Multi-Modal)**"):
        st.markdown(
            """
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                  AI PIPELINE (AUTO-FALLBACK)                 │
        ├─────────────────────────────────────────────────────────────┤
        │  Step 1: Thử load FUSION MODEL trước                         │
        │    • Text: uitnlp/CafeBERT backbone                         │
        │    • Video: MCG-NJU/VideoMAE-base backbone                  │
        │    • Fusion: Cross-Attention + Gating (50-50 weights)       │
        │    • Output: Single fusion_score từ softmax [0-1]           │
        ├─────────────────────────────────────────────────────────────┤
        │  Fallback: Nếu FUSION không load được → LATE_SCORE          │
        │    • Chạy 2 models riêng (text + video)                     │
        │    • avg_score = text_score * 0.3 + video_score * 0.7       │
        │    • Configurable via env: TEXT_WEIGHT (0 to 1)             │
        └─────────────────────────────────────────────────────────────┘
        ```
        
        **Logic trong spark_processor.py:**
        ```python
        # Luôn thử FUSION trước
        model, tokenizer, processor = get_fusion_model()
        if model is None:
            # FUSION không load được → Auto-fallback về LATE_SCORE
            actual_use_fusion = False
            log_to_db("⚠️ FUSION model not available, falling back to LATE_SCORE")
        else:
            actual_use_fusion = True
            log_to_db("✅ FUSION model loaded successfully!")
        ```
        
        **FUSION mode (50-50 weights đã train):**
        ```python
        fusion_config = {
            "video_weight": 0.5,  # Đồng bộ với train_eval_module
            "text_weight": 0.5,   # Đồng bộ với train_eval_module  
            "fusion_type": "attention",
        }
        ```
        
        **LATE_SCORE mode (fallback với 30-70 default):**
        ```python
        TEXT_WEIGHT = float(os.getenv("TEXT_WEIGHT", "0.3"))  # Default 30%
        VIDEO_WEIGHT = 1.0 - TEXT_WEIGHT  # Default 70%
        avg_score = (text_score * TEXT_WEIGHT) + (video_score * VIDEO_WEIGHT)
        ```
        
        > **Lưu ý:** FUSION là mode chính. LATE_SCORE chỉ được dùng khi không load được FUSION model.
        > Audio đã được trích xuất nhưng chưa tích hợp vào AI pipeline.
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
            video_id VARCHAR(50) PRIMARY KEY,
            raw_text TEXT,
            human_label VARCHAR(20),
            text_verdict VARCHAR(20),
            text_score DOUBLE PRECISION,
            video_verdict VARCHAR(20),
            video_score DOUBLE PRECISION,
            avg_score DOUBLE PRECISION,
            threshold DOUBLE PRECISION,
            final_decision VARCHAR(50),
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    Hệ thống sử dụng **Fusion Model (Text + Video)** với attention mechanism để kết hợp kết quả:
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
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> CafeBERT (uitnlp)</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> Vietnamese text/caption</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Harmful probability [0-1]</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Features:</b> Rule-based + AI</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Phân tích ngữ nghĩa văn bản tiếng Việt, kết hợp blacklist keywords
                với deep learning để phát hiện nội dung độc hại.
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
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> VideoMAE</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> 16 video frames</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Harmful probability [0-1]</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Base:</b> MCG-NJU/videomae-base</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Phân tích chuỗi video frames, sử dụng masked autoencoder
                để phát hiện nội dung bạo lực và không phù hợp.
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
            <h3 style="color: white; margin: 0 0 10px 0;">🔥 Fusion Model</h3>
            <p style="color: #ddd; margin: 5px 0;"><b>Architecture:</b> Late Fusion + Attention</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Input:</b> Text + Video features</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Output:</b> Final harmful score</p>
            <p style="color: #ddd; margin: 5px 0;"><b>Threshold:</b> 0.5 (configurable)</p>
            <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
            <p style="color: #aaa; font-size: 0.85em; line-height: 1.4;">
                Cross-attention fusion kết hợp text và video features
                với gating mechanism để quyết định cuối cùng.
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
    **Cách Fusion Model hoạt động:**
    
    ```python
    class LateFusionModel:
        def forward(self, text_input, video_frames):
            # 1. Extract features from backbones
            text_feat = text_backbone(text_input)       # CafeBERT [CLS] token
            video_feat = video_backbone(video_frames)   # VideoMAE mean pooling
            
            # 2. Project to same dimension (256)
            t_proj = text_proj(text_feat)   # (B, 256)
            v_proj = video_proj(video_feat) # (B, 256)
            
            # 3. Cross-Attention Fusion
            t_attended = cross_attn_t2v(t_proj, v_proj, v_proj)
            v_attended = cross_attn_v2t(v_proj, t_proj, t_proj)
            
            # 4. Gating mechanism
            concat = torch.cat([t_attended, v_attended], dim=1)
            gate = sigmoid(gate_layer(concat))  # [0-1] weight
            combined = gate * t_attended + (1 - gate) * v_attended
            
            # 5. Classification
            logits = classifier(combined)  # [safe, harmful]
            return softmax(logits)[:, 1]   # harmful probability
    ```
    
    **Tại sao chọn Late Fusion với Attention?**
    - Cross-attention cho phép text và video "tham khảo" lẫn nhau
    - Gating mechanism tự động học weight dựa trên context
    - Hiệu quả hơn simple weighted average (40-40-20)
    """
    )


def _render_documentation():
    """Render project documentation"""
    st.subheader("📖 Tài liệu Dự án")

    st.markdown(
        """
    ### 📁 Project Structure
    
    ```
    UIT-SE363-Big-Data-Platform-Application-Development/
    ├── 📂 streaming/                     # Main application
    │   ├── 📂 ingestion/               # Data collection
    │   │   ├── crawler.py              # SeleniumWire + TikTok API
    │   │   ├── downloader.py           # yt-dlp video download
    │   │   ├── main_worker.py          # Pipeline orchestrator
    │   │   └── audio_processor.py      # FFmpeg audio extraction
    │   │
    │   ├── 📂 processing/              # Spark + AI
    │   │   └── spark_processor.py      # Streaming + Fusion AI
    │   │
    │   ├── 📂 dashboard/               # Streamlit UI
    │   │   ├── app.py                  # Entry point
    │   │   ├── helpers.py              # DB queries
    │   │   └── page_modules/           # Tab pages
    │   │
    │   ├── 📂 airflow/                 # DAG orchestration
    │   │   └── dags/                   # 3 DAGs
    │   │
    │   ├── docker-compose.yml        # 12 services
    │   └── start_all.sh              # One-click start
    │
    ├── 📂 train_eval_module/          # Model training
    │   ├── text/                      # CafeBERT, XLM-RoBERTa
    │   ├── video/                     # VideoMAE
    │   └── fusion/                    # Late Fusion + Attention
    │
    └── 📂 processed_data/             # Training datasets
    ```
    """
    )

    st.markdown("---")
    st.markdown("### 🚀 Quick Start Guide")

    st.code(
        """
# 1. Clone repository
git clone https://github.com/TrungPhamDac/UIT-SE363-BigData.git
cd UIT-SE363-Big-Data-Platform-Application-Development/streaming

# 2. Start all services (one-click)
./start_all.sh
# Hoặc: docker compose up -d --build

# 3. Đợi services khởi động (~2-3 phút)
docker ps  # Kiểm tra status

# 4. Truy cập Dashboard
open http://localhost:8501

# 5. Khởi chạy Pipeline
# Dashboard → System Operations → Trigger DAGs
# Hoặc: Airflow UI http://localhost:8080 (admin/admin)
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
