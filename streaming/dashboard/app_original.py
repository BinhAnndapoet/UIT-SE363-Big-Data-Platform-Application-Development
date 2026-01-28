import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu
import os
import re

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(
    layout="wide",
    page_title="SE363 | Big Data Platform Project",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# Database Config
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "tiktok_safety_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


# SQLAlchemy engine (pandas compatible, no warnings)
def get_db_engine():
    url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    return create_engine(url)


# MinIO Config
MINIO_CONF = {
    "public_endpoint": os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000"),
    "bucket": os.getenv("MINIO_BUCKET_VIDEOS", "tiktok-raw-videos"),
}

# Airflow Config
AIRFLOW_API_URL = "http://airflow-webserver:8080/api/v1/dags"
AIRFLOW_AUTH = (
    os.getenv("AIRFLOW_ADMIN_USERNAME", "admin"),
    os.getenv("AIRFLOW_ADMIN_PASSWORD", "admin"),
)

# --- 2. ADVANCED CSS STYLING ---
st.markdown(
    """
<style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8F9FA;
    }

    /* CUSTOM HEADER COMPONENT STYLE */
    .header-container {
        background-color: white;
        padding: 20px 30px;
        border-radius: 12px;
        border-left: 6px solid #FE2C55; /* TikTok Red */
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        display: flex;
        flex-direction: column;
    }
    .header-title {
        color: #161823;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .header-subtitle {
        color: #8A8B91;
        font-size: 15px;
        margin-top: 8px;
        font-weight: 400;
    }

    /* CARD STYLING */
    .stContainer {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #EBEBEB;
        margin-bottom: 20px;
    }

    /* METRICS CARD OVERRIDE */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #25F4EE; /* TikTok Cyan */
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }

    /* TERMINAL LOGS */
    .terminal-box {
        background-color: #121212;
        color: #00FF9C; /* Matrix Green */
        font-family: 'Consolas', 'Monaco', monospace;
        padding: 15px;
        border-radius: 8px;
        height: 350px;
        overflow-y: auto;
        font-size: 13px;
        border: 1px solid #333;
    }

    /* BADGES */
    .badge-harm { background-color: #FE2C55; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-safe { background-color: #25F4EE; color: #161823; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    
    /* BUTTONS */
    div.stButton > button:first-child {
        font-weight: 600;
        border-radius: 8px;
        height: 45px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- 3. HELPER FUNCTIONS ---


def render_header(title, subtitle, icon="🛡️"):
    """Hàm vẽ Header chuẩn thống nhất cho toàn bộ App"""
    st.markdown(
        f"""
    <div class="header-container">
        <div class="header-title">
            <span>{icon}</span> {title}
        </div>
        <div class="header-subtitle">{subtitle}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=5)
def get_data():
    try:
        engine = get_db_engine()
        query = """
            SELECT video_id, raw_text, human_label, text_verdict, video_verdict, 
                   text_score, video_score, avg_score, final_decision, processed_at 
            FROM processed_results 
            ORDER BY processed_at DESC LIMIT 500;
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            df["final_decision"] = df["final_decision"].str.lower().str.strip()
            df["processed_at"] = pd.to_datetime(df["processed_at"])
            df["Category"] = df["final_decision"].apply(
                lambda x: "Harmful" if "harmful" in x else "Safe"
            )
        return df
    except:
        return pd.DataFrame()


def get_recent_logs(dag_id, limit=30):
    try:
        engine = get_db_engine()
        query = f"SELECT created_at, log_level, message FROM system_logs WHERE dag_id = '{dag_id}' ORDER BY created_at DESC LIMIT {limit};"
        df = pd.read_sql(query, engine)
        return df
    except:
        return pd.DataFrame()


def get_dag_status(dag_id):
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns?limit=1&order_by=-execution_date"
        res = requests.get(url, auth=AIRFLOW_AUTH)
        if res.status_code == 200 and res.json()["dag_runs"]:
            return res.json()["dag_runs"][0]["state"]
        return "unknown"
    except:
        return "error"


def infer_streaming_engine_state(
    processed_df: pd.DataFrame, active_window_seconds: int = 180
):
    """Suy luận trạng thái AI engine dựa trên dữ liệu output (processed_results).

    Vì Spark Streaming đang chạy như service riêng (spark-processor), đôi khi Airflow DAG không ở trạng thái `running`
    nhưng engine vẫn đang hoạt động / đang chờ Kafka.
    """
    if (
        processed_df is None
        or processed_df.empty
        or "processed_at" not in processed_df.columns
    ):
        return {
            "state": "waiting",
            "label": "🕒 WAITING (Chưa có output)",
            "hint": "Chưa thấy record nào trong processed_results. Nếu bạn vừa start hệ thống: hãy chạy Ingestion (DAG 2) để đẩy dữ liệu vào Kafka.",
            "last_processed_at": None,
        }

    try:
        last_ts = pd.to_datetime(processed_df["processed_at"]).max()
    except Exception:
        last_ts = None

    if last_ts is None or pd.isna(last_ts):
        return {
            "state": "waiting",
            "label": "🕒 WAITING (Chưa có output)",
            "hint": "Chưa parse được processed_at.",
            "last_processed_at": None,
        }

    age_sec = (
        pd.Timestamp.utcnow().tz_localize(None) - last_ts.to_pydatetime()
    ).total_seconds()
    if age_sec <= active_window_seconds:
        return {
            "state": "active",
            "label": "🔥 ACTIVE (Đang xử lý)",
            "hint": f"Có output mới cách đây ~{int(age_sec)}s.",
            "last_processed_at": last_ts,
        }

    return {
        "state": "idle",
        "label": "💤 STANDBY (Đang chờ Kafka)",
        "hint": f"Output gần nhất cách đây ~{int(age_sec)}s. Engine có thể đang chạy nhưng chưa có message mới.",
        "last_processed_at": last_ts,
    }


def trigger_dag(dag_id):
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns"
        response = requests.post(url, json={"conf": {}}, auth=AIRFLOW_AUTH)
        return response.status_code == 200
    except:
        return False


def get_video_url(vid_id, label):
    clean_label = str(label).lower().strip()
    if "harm" in clean_label:
        clean_label = "harmful"
    elif "safe" in clean_label:
        clean_label = "safe"
    elif clean_label in ["unknown", "unlabeled", "none", "nan", ""]:
        clean_label = "unknown"
    else:
        # fallback an toàn
        clean_label = "unknown"
    return f"{MINIO_CONF['public_endpoint']}/{MINIO_CONF['bucket']}/raw/{clean_label}/{vid_id}.mp4"


# --- 3b. Moderation helpers (rule keyword explanation) ---
# NOTE: danh sách này mirror từ Spark processor để moderator nhìn thấy “vì sao text bị flag”.
BLACKLIST_KEYWORDS = [
    "gaixinh",
    "gái xinh",
    "nhảy sexy",
    "nhay sexy",
    "khoe body",
    "khoe dáng",
    "bikini",
    "hở bạo",
    "sugar baby",
    "sugarbaby",
    "sgbb",
    "nuôi baby",
    "phòng the",
    "phong the",
    "chuyện người lớn",
    "18+",
    "lộ clip",
    "khoe hàng",
    "đánh nhau",
    "danh nhau",
    "đánh ghen",
    "danh ghen",
    "bóc phốt",
    "boc phot",
    "drama",
    "showbiz",
    "xăm trổ",
    "giang hồ",
    "biến căng",
    "check var",
    "hỗn chiến",
    "bạo lực học đường",
    "chửi bậy",
    "tài xỉu",
    "xóc đĩa",
    "xoc dia",
    "nổ hũ",
    "no hu",
    "bắn cá",
    "soi kèo",
    "cho vay",
    "bốc bát họ",
    "kiếm tiền online",
    "lừa đảo",
    "app vay tiền",
    "nhóm kéo",
    "kéo tài xỉu",
    "cá độ",
    "lô đề",
    "bay lắc",
    "dân chơi",
    "trà đá vỉa hè",
    "nhậu nhẹt",
    "say rượu",
    "hút thuốc",
    "vape",
    "pod",
    "cần sa",
    "ke",
    "kẹo",
    "gọi vong",
    "xem bói",
    "bùa ngải",
    "kumathong",
    "kumanthong",
    "tâm linh",
]


def find_blacklist_hits(text: str, max_hits: int = 8):
    if not text:
        return []
    tl = str(text).lower()
    hits = []
    for kw in BLACKLIST_KEYWORDS:
        if kw in tl:
            hits.append(kw)
            if len(hits) >= max_hits:
                break
    return hits


def highlight_keywords(text: str, keywords):
    if not text:
        return ""
    out = str(text)
    # highlight đơn giản (không perfect cho unicode/overlap) nhưng đủ cho moderator đọc nhanh
    for kw in sorted(set(keywords), key=len, reverse=True):
        try:
            out = re.sub(
                re.escape(kw),
                lambda m: f"**{m.group(0)}**",
                out,
                flags=re.IGNORECASE,
            )
        except Exception:
            pass
    return out


# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/en/thumb/a/a9/TikTok_logo.svg/2560px-TikTok_logo.svg.png",
    width=140,
)

with st.sidebar:
    selected = option_menu(
        "Navigation",
        ["Dashboard Monitor", "System Operations", "Content Audit", "Project Info"],
        icons=["activity", "cpu", "shield-check", "info-circle"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#FE2C55"},
        },
    )

    st.markdown("---")
    st.markdown("### 👨‍🎓 Thông Tin Đồ Án")
    st.info(
        """
    **Đề tài:** Xây dựng hệ thống Big Data phát hiện nội dung độc hại trên TikTok.
    
    **Môn học:** SE363 - Phát triển Ứng dụng Big Data Platform
    
    **GVHD:** ThS. Đỗ Trọng Hợp
    
    **Nhóm: 16**
    - Bùi Nhật Anh Khôi (23520761)
    - Đinh Lê Bình Anh (23520004)
    - Phạm Quốc Nam (23520984)
    """
    )
    st.caption("Version 2.3 | Release 2025")

# Refresh Loop
# Refresh mỗi 30 giây (30000ms) thay vì 5 giây
st_autorefresh(interval=30000, key="global_refresh")

# Load Data
df = get_data()

# ==========================================
# PAGE 1: DASHBOARD (THỐNG KÊ)
# ==========================================
if selected == "Dashboard Monitor":
    render_header(
        title="Analytics Dashboard",
        subtitle="Hệ thống giám sát thời gian thực luồng dữ liệu TikTok.",
        icon="📊",
    )

    if df.empty:
        st.warning(
            "⚠️ Hệ thống chưa có dữ liệu. Vui lòng chuyển sang tab **System Operations** để chạy Crawler."
        )
    else:
        # Row 1: KPI Metrics
        with st.container():
            st.subheader("📌 Chỉ số Quan trọng (KPIs)")
            m1, m2, m3, m4 = st.columns(4)

            total = len(df)
            harmful = len(df[df["Category"] == "Harmful"])
            safe = total - harmful
            risk_score = df["avg_score"].mean()  # 0..1
            risk_score_10 = risk_score * 10

            m1.metric("Tổng Video Xử Lý", f"{total:,}", "Videos")
            m2.metric(
                "Nội dung Độc hại",
                f"{harmful:,}",
                f"{(harmful/total*100):.1f}% Rate",
                delta_color="inverse",
            )
            m3.metric("Nội dung An toàn", f"{safe:,}", f"{(safe/total*100):.1f}% Rate")
            m4.metric("Điểm Rủi ro TB", f"{risk_score_10:.2f}", "Thang 0–10")

        # Row 2: Charts
        col_chart1, col_chart2 = st.columns([2, 1])

        with col_chart1:
            with st.container():
                st.subheader("📈 Xu hướng Phát hiện theo Thời gian")
                if not df.empty:
                    time_df = (
                        df.set_index("processed_at")
                        .resample("h")["Category"]
                        .value_counts()
                        .unstack()
                        .fillna(0)
                    )
                    fig = px.area(
                        time_df,
                        color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                    )
                    fig.update_layout(
                        xaxis_title="Thời gian (Giờ)",
                        yaxis_title="Số lượng Video",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend_title="",
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            with st.container():
                st.subheader("🎯 Tỷ lệ Phân loại")
                fig_pie = px.pie(
                    df,
                    names="Category",
                    hole=0.5,
                    color="Category",
                    color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                )
                fig_pie.update_layout(
                    showlegend=True,
                    margin=dict(t=0, b=0, l=0, r=0),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                    ),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        # Row 3: Deep Dive
        with st.container():
            st.subheader("🔍 Phân tích Chuyên sâu (Risk Analysis)")
            c3, c4 = st.columns(2)
            with c3:
                # hiển thị thang 0–10 cho trực quan
                df_plot = df.copy()
                df_plot["risk_score_10"] = df_plot["avg_score"] * 10
                fig_hist = px.histogram(
                    df_plot,
                    x="risk_score_10",
                    nbins=20,
                    color="Category",
                    title="Phân bố Điểm Rủi ro",
                    color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                )
                fig_hist.update_layout(
                    xaxis_title="Risk Score (0–10)", yaxis_title="Số lượng Video"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            with c4:
                fig_scat = px.scatter(
                    df,
                    x="text_score",
                    y="video_score",
                    color="Category",
                    title="Tương quan Text Model vs Video Model",
                    hover_data=["video_id"],
                    color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                )
                fig_scat.update_layout(
                    xaxis_title="Text Model Confidence",
                    yaxis_title="Video Model Confidence",
                )
                st.plotly_chart(fig_scat, use_container_width=True)

# ==========================================
# PAGE 2: OPERATIONS (VẬN HÀNH) - ĐÃ CHIA ĐÔI
# ==========================================
elif selected == "System Operations":
    render_header(
        title="Operations Center",
        subtitle="Trung tâm điều khiển Pipeline ETL (Airflow) và giám sát Logs hệ thống.",
        icon="⚙️",
    )

    # 1. Control Panel
    col_sys1, col_sys2 = st.columns(2)

    # Crawler Card
    with col_sys1:
        with st.container():
            status = get_dag_status("1_TIKTOK_ETL_COLLECTOR")
            st.markdown("### 🕷️ Crawler Service")

            if status == "running":
                st.warning(f"**Status:** ⏳ RUNNING (Đang chạy...)")
            elif status == "success":
                st.success(f"**Status:** ✅ STANDBY (Sẵn sàng)")
            elif status == "failed":
                st.error(f"**Status:** ❌ FAILED (Lỗi)")
            else:
                st.info(f"**Status:** 💤 IDLE (Chờ lệnh)")

            st.caption(
                "Kích hoạt Selenium-Wire để bắt gói tin JSON từ TikTok Hashtags."
            )
            if st.button("🚀 KÍCH HOẠT CRAWLER", use_container_width=True):
                if trigger_dag("1_TIKTOK_ETL_COLLECTOR"):
                    st.toast("Lệnh đã gửi tới Airflow thành công!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Không thể kết nối tới Airflow Webserver.")

    # Streaming Card
    with col_sys2:
        with st.container():
            dag_status = get_dag_status("2_TIKTOK_STREAMING_PIPELINE")
            inferred = infer_streaming_engine_state(df)
            st.markdown("### 🌊 AI Streaming Engine")

            # Ưu tiên hiển thị DAG đang chạy (nếu có), nếu không thì suy luận từ output.
            if dag_status == "running":
                st.success("**Status:** 🔥 ACTIVE (DAG đang chạy)")
                st.caption(
                    "Airflow DAG 2 đang thực thi (Ingestion Worker). Spark engine chạy ở service spark-processor."
                )
            elif dag_status in ["failed", "error"]:
                st.error(f"**Status:** ❌ {dag_status.upper()} (Airflow)")
                st.caption(
                    "Airflow báo lỗi. Spark engine có thể vẫn đang chạy, nhưng ingestion không đẩy dữ liệu mới."
                )
            else:
                # success/queued/none/...: fallback về output
                if inferred["state"] == "active":
                    st.success(f"**Status:** {inferred['label']}")
                elif inferred["state"] == "idle":
                    st.info(f"**Status:** {inferred['label']}")
                else:
                    st.warning(f"**Status:** {inferred['label']}")

                st.caption(f"Airflow DAG trạng thái gần nhất: `{dag_status}`")
                if inferred.get("last_processed_at") is not None:
                    st.caption(
                        f"🕒 Output gần nhất: {inferred['last_processed_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                st.caption(inferred.get("hint", ""))

            st.caption(
                "Kích hoạt Spark Streaming đọc Kafka và chấm điểm nội dung bằng AI."
            )
            if st.button(
                "⚡ KÍCH HOẠT STREAMING", use_container_width=True, type="primary"
            ):
                if trigger_dag("2_TIKTOK_STREAMING_PIPELINE"):
                    st.toast("AI Engine đang khởi động...", icon="🧠")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Lỗi kết nối Airflow.")

    # 2. Logs Interface (CHIA 2 CỘT NHƯ YÊU CẦU)
    st.markdown("---")
    st.markdown("### 📟 Live Terminal Logs")

    l1, l2 = st.columns(2)

    with l1:
        st.markdown("**🕷️ Crawler Logs (Ingestion)**")
        logs = get_recent_logs("1_TIKTOK_ETL_COLLECTOR", limit=50)
        html = '<div class="terminal-box">'
        if not logs.empty:
            for _, row in logs.iterrows():
                ts = row["created_at"].strftime("%H:%M:%S")
                color = "#FF5252" if row["log_level"] == "ERROR" else "#69F0AE"
                html += f"<div><span style='color:#64748b'>[{ts}]</span> <span style='color:{color}'><b>{row['log_level']}</b></span>: {row['message']}</div>"
        else:
            html += "<div><span style='color:#666'>_ Hệ thống đang chờ log từ Crawler...</span></div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with l2:
        st.markdown("**🧠 Spark AI Logs (Processing)**")
        logs = get_recent_logs("2_TIKTOK_STREAMING_PIPELINE", limit=50)
        html = '<div class="terminal-box">'
        if not logs.empty:
            for _, row in logs.iterrows():
                ts = row["created_at"].strftime("%H:%M:%S")
                msg = row["message"]
                if "DETECTED" in msg:
                    msg = f"<span style='color:#FF5252; font-weight:bold'>{msg}</span>"
                elif "SAFE" in msg:
                    msg = f"<span style='color:#69F0AE; font-weight:bold'>{msg}</span>"
                html += f"<div><span style='color:#64748b'>[{ts}]</span> {msg}</div>"
        else:
            # Fallback: nếu chưa có system_logs từ Spark, hiển thị các event gần nhất từ processed_results
            if df is not None and not df.empty and "processed_at" in df.columns:
                fallback = df[
                    ["processed_at", "video_id", "final_decision", "avg_score"]
                ].head(20)
                for _, r in fallback.iterrows():
                    try:
                        ts = pd.to_datetime(r["processed_at"]).strftime("%H:%M:%S")
                    except Exception:
                        ts = "--:--:--"
                    decision = str(r.get("final_decision", ""))
                    score = r.get("avg_score", "")
                    vid = str(r.get("video_id", ""))
                    color = "#FF5252" if "harm" in decision.lower() else "#69F0AE"
                    html += (
                        f"<div><span style='color:#64748b'>[{ts}]</span> "
                        f"<span style='color:{color}; font-weight:bold'>{decision.upper()}</span> "
                        f"score={score} vid={vid}</div>"
                    )
                html += "<div style='margin-top:8px; color:#666'>_ (Fallback) Hiển thị từ processed_results vì Spark chưa ghi system_logs.</div>"
            else:
                html += "<div><span style='color:#666'>_ Chưa có log Spark. Nếu Spark đang chạy, nó có thể đang chờ Kafka hoặc chưa có output.</span></div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

# ==========================================
# PAGE 3: CONTENT AUDIT (DUYỆT)
# ==========================================
elif selected == "Content Audit":
    render_header(
        title="Content Moderation Audit",
        subtitle="Giao diện duyệt video chi tiết dành cho quản trị viên (Moderator).",
        icon="🎬",
    )

    # Filter Bar
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            filter_mode = st.selectbox(
                "🎯 Bộ lọc nội dung:",
                ["Toàn bộ", "⚠️ Nguy hiểm (Harmful)", "✅ An toàn (Safe)"],
            )
        with c2:
            st.info(
                "💡 **Mẹo:** Bấm vào Video để xem trước. Điểm Risk Score càng cao (gần 10) thì độ nguy hại càng lớn."
            )

        # Calibration controls (không ghi ngược DB, chỉ để moderator test)
        with c3:
            with st.expander(
                "🧪 Test thủ công: chỉnh weight/threshold", expanded=False
            ):
                w_text = st.slider(
                    "Text weight (w_text)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                )
                threshold = st.slider(
                    "Threshold (0–1)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                )
                st.caption(
                    f"Công thức test: score = w_text·text_score + (1-w_text)·video_score. Quyết định harmful nếu score ≥ {threshold:.2f}."
                )

    # Data Filtering
    if filter_mode == "⚠️ Nguy hiểm (Harmful)":
        view_df = df[df["Category"] == "Harmful"]
    elif filter_mode == "✅ An toàn (Safe)":
        view_df = df[df["Category"] == "Safe"]
    else:
        view_df = df

    if view_df.empty:
        st.warning("📭 Không tìm thấy video nào phù hợp với bộ lọc này.")
    else:
        st.markdown(f"**Kết quả:** Tìm thấy {len(view_df)} video.")

        # Quick evaluation vs human_label (nếu có)
        try:
            eval_df = view_df.copy()
            eval_df["human_label_norm"] = (
                eval_df["human_label"].astype(str).str.lower().str.strip()
            )
            eval_df = eval_df[eval_df["human_label_norm"].isin(["safe", "harmful"])]
            if not eval_df.empty:
                eval_df["score_custom"] = eval_df["text_score"].fillna(
                    0
                ) * w_text + eval_df["video_score"].fillna(0) * (1 - w_text)
                eval_df["pred_custom"] = eval_df["score_custom"].apply(
                    lambda s: "harmful" if float(s) >= threshold else "safe"
                )
                acc = (eval_df["pred_custom"] == eval_df["human_label_norm"]).mean()
                st.caption(
                    f"🧪 Đánh giá nhanh (so với human_label, n={len(eval_df)}): accuracy ≈ {acc*100:.1f}% (chỉ để tham khảo)."
                )
                cm = pd.crosstab(
                    eval_df["human_label_norm"],
                    eval_df["pred_custom"],
                    rownames=["Human"],
                    colnames=["Pred"],
                ).reindex(
                    index=["safe", "harmful"], columns=["safe", "harmful"], fill_value=0
                )
                st.dataframe(cm, use_container_width=True)
            else:
                st.caption(
                    "🧪 Không có human_label hợp lệ (safe/harmful) để so sánh. Crawler/CSV có thể đang ghi nhãn thiếu hoặc unknown."
                )
        except Exception:
            pass

        for index, row in view_df.head(10).iterrows():
            with st.container():
                col_vid, col_meta, col_ai = st.columns([1.5, 2, 1.5])

                # Cột Video
                with col_vid:
                    try:
                        # QUAN TRỌNG: video được lưu theo nhãn CSV/human_label (raw/<label>/...),
                        # không phải theo AI final_decision. Nếu dùng Category sẽ dễ bị "Video Missing".
                        storage_label = (
                            str(row.get("human_label", "")).lower().strip()
                            if row.get("human_label", None) is not None
                            else ""
                        )
                        if storage_label not in ["safe", "harmful", "unknown"]:
                            storage_label = (
                                str(row.get("Category", "unknown")).lower().strip()
                            )
                        st.video(get_video_url(row["video_id"], storage_label))
                    except:
                        st.error("Video File Missing in MinIO")
                    st.caption(f"**ID:** `{row['video_id']}`")

                # Cột Thông tin
                with col_meta:
                    st.markdown("#### Metadata Info")
                    if row["Category"] == "Harmful":
                        st.markdown(
                            f"<span class='badge-harm'>HARMFUL CONTENT</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<span class='badge-safe'>SAFE CONTENT</span>",
                            unsafe_allow_html=True,
                        )

                    st.markdown("**📝 Caption:**")
                    raw_text = (
                        row["raw_text"] if row.get("raw_text", None) is not None else ""
                    )
                    hits = find_blacklist_hits(raw_text)

                    # Hiển thị rõ caption + highlight keyword (nếu có)
                    if raw_text:
                        if hits:
                            st.warning(
                                "Phát hiện từ khóa nhạy cảm trong caption (rule-based)."
                            )
                            st.markdown(
                                highlight_keywords(raw_text, hits),
                                help=f"Keyword hit: {', '.join(hits)}",
                            )
                        else:
                            st.info(raw_text)
                    else:
                        st.info("(Không có mô tả)")

                    if hits:
                        st.caption(f"🔎 Keyword hit: {', '.join(hits)}")
                    st.text(
                        f"🕒 Detected: {row['processed_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                # Cột AI
                with col_ai:
                    st.markdown("#### 🤖 AI Verdict")
                    score = (
                        float(row["avg_score"])
                        if row.get("avg_score", None) is not None
                        else 0.0
                    )
                    score_10 = score * 10
                    st.progress(
                        min(max(score, 0.0), 1.0),
                        text=f"Risk Score: {score_10:.1f}/10 (raw={score:.2f})",
                    )

                    # Test lại quyết định với tham số thủ công
                    try:
                        text_s = float(row.get("text_score", 0) or 0)
                        video_s = float(row.get("video_score", 0) or 0)
                        score_custom = text_s * w_text + video_s * (1 - w_text)
                        pred_custom = "harmful" if score_custom >= threshold else "safe"
                        st.caption(
                            f"🧪 Test: score={score_custom:.2f} → `{pred_custom}` (w_text={w_text:.2f}, thr={threshold:.2f})"
                        )
                    except Exception:
                        pass

                    st.markdown(
                        f"""
                    - **Text Model:** `{row['text_verdict']}` ({row['text_score']:.2f})
                    - **Video Model:** `{row['video_verdict']}` ({row['video_score']:.2f})
                    - **Human Label:** `{row['human_label']}`
                    - **Final Decision (Saved):** `{row['final_decision']}`
                    """
                    )

# ==========================================
# PAGE 4: PROJECT INFO (HƯỚNG DẪN)
# ==========================================
elif selected == "Project Info":
    render_header(
        title="Project Documentation",
        subtitle="Tài liệu kiến trúc hệ thống và hướng dẫn sử dụng đồ án.",
        icon="📘",
    )

    st.markdown("### 1. Kiến trúc Hệ thống (Big Data Pipeline)")

    st.info(
        """
    **Luồng dữ liệu (Data Pipeline Architecture):**
    1.  **Ingestion Layer:** - Sử dụng **Selenium-Wire (Python)** để bắt gói tin JSON API từ TikTok Web.
        - Giả lập hành vi người dùng (Scroll, View) để vượt qua Anti-Bot.
    2.  **Message Queue:** Dữ liệu thô (JSON) được đẩy vào **Kafka Topic**.
    3.  **Processing Layer:** - **Spark Streaming** đọc dữ liệu Real-time từ Kafka.
        - Tải video về từ CDN TikTok và đẩy vào **MinIO Object Storage**.
    4.  **Intelligence Layer:** - Spark gọi các model AI (Text Classification & Video Classification) để chấm điểm nội dung.
    5.  **Serving Layer:** - Kết quả phân tích lưu vào **PostgreSQL**.
        - Dashboard **Streamlit** hiển thị báo cáo.
    """
    )

    st.markdown("---")
    st.markdown("### 2. Standard Operating Procedure (SOP)")

    col_step1, col_step2, col_step3 = st.columns(3)

    with col_step1:
        with st.container():
            st.markdown("#### Bước 1: Thu thập")
            st.write(
                "Vào **System Operations** > Bấm **🚀 KÍCH HOẠT CRAWLER**. Chờ log báo `[INFO] Hoàn tất`."
            )

    with col_step2:
        with st.container():
            st.markdown("#### Bước 2: Xử lý AI")
            st.write(
                "Vào **System Operations** > Bấm **⚡ KÍCH HOẠT STREAMING**. Hệ thống sẽ tự động xử lý khi có dữ liệu mới."
            )

    with col_step3:
        with st.container():
            st.markdown("#### Bước 3: Kiểm duyệt")
            st.write(
                "Vào **Dashboard Monitor** để xem thống kê hoặc **Content Audit** để xem chi tiết video."
            )

    st.success("© 2025 - Developed for SE363 Course at UIT.")
