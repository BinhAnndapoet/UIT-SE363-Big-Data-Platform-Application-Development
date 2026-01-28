"""
System Operations Page - Pipeline Control & Logs
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from helpers import (
    get_dag_status,
    trigger_dag,
    infer_streaming_engine_state,
    get_container_logs,
    get_recent_logs,
    render_header,
    get_data,
    clear_queued_dag_runs,
    get_dag_info,
    get_dag_run_history,
    get_task_instances,
    get_task_logs,
    pause_dag,
    mark_dag_run_state,
    mark_task_state,
)
from config import AIRFLOW_API_URL, EXTERNAL_URLS


def render_system_operations():
    """Render the system operations page"""

    # Initialize session state for log viewing
    if "active_log_key" not in st.session_state:
        st.session_state.active_log_key = None
    if "active_log_content" not in st.session_state:
        st.session_state.active_log_content = None
    if "selected_dag_tab2" not in st.session_state:
        st.session_state.selected_dag_tab2 = "1_TIKTOK_ETL_COLLECTOR"

    render_header(
        title="System Operations",
        subtitle="Điều khiển Pipeline, xem trạng thái hệ thống và logs.",
        icon="⚙️",
    )

    # Help Panel
    with st.expander("📖 Hướng dẫn vận hành hệ thống", expanded=False):
        st.markdown(
            """
        ### 🔧 Quy trình vận hành Pipeline
        
        #### 1️⃣ **Crawler Pipeline**
        - **Mục đích**: Thu thập video TikTok từ các hashtag
        - **Cách chạy**: Click **🚀 KÍCH HOẠT CRAWLER**
        - **Thời gian**: 2-5 phút tùy số lượng hashtag
        - **Output**: Video files được lưu vào MinIO bucket
        
        #### 2️⃣ **Streaming Pipeline**
        - **Mục đích**: Xử lý AI realtime các video mới
        - **Cách chạy**: Click **⚡ KÍCH HOẠT STREAMING**
        - **Components**: Kafka → Spark → AI Models → PostgreSQL
        - **Output**: Kết quả phân loại trong Database
        
        ### 📊 Giám sát trạng thái
        - **🟢 Running**: Pipeline đang hoạt động
        - **🟡 Queued**: Đang chờ xử lý
        - **🔴 Failed**: Có lỗi - xem logs để debug
        - **⚪ Not Run**: Chưa được kích hoạt
        
        ### 📋 System Logs
        - Xem logs của các containers: DB, MinIO, Airflow
        - Filter theo thời gian và log level
        """
        )

    tab1, tab2, tab3 = st.tabs(
        ["🔧 Pipeline Control", "📊 Status Monitor", "📋 System Logs"]
    )

    with tab1:
        _render_pipeline_control()

    with tab2:
        _render_status_monitor()

    with tab3:
        _render_system_logs()


def _render_pipeline_control():
    """Render pipeline control section - Quick Actions first, then Pipeline Control"""

    # ========== QUICK ACTIONS (ĐƯA LÊN TRÊN) ==========
    st.subheader("⚡ Quick Actions")

    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button(
            "🔄 Refresh Data",
            use_container_width=True,
            key="refresh_btn",
            help="Làm mới dữ liệu (không reset trang)",
        ):
            st.cache_data.clear()
            st.toast("✅ Đã làm mới dữ liệu!")
            # Don't call st.rerun() to avoid page reset

    with qa2:
        st.link_button(
            "🌐 Airflow UI",
            EXTERNAL_URLS["airflow"],
            use_container_width=True,
        )

    with qa3:
        st.link_button(
            "📦 MinIO Console",
            EXTERNAL_URLS["minio_console"],
            use_container_width=True,
        )

    with qa4:
        if st.button("🗑️ Clear Queued", use_container_width=True, type="secondary"):
            with st.spinner("Đang xóa các DAG runs đang queued..."):
                count1 = clear_queued_dag_runs("1_TIKTOK_ETL_COLLECTOR")
                count2 = clear_queued_dag_runs("2_TIKTOK_STREAMING_PIPELINE")
                if count1 >= 0 and count2 >= 0:
                    st.toast(f"✅ Đã xóa {count1 + count2} queued runs!")
                    st.cache_data.clear()  # Clear cache to show updated status
                else:
                    st.error("❌ Lỗi khi xóa queued runs")

    # ========== PIPELINE STATUS SUMMARY ==========
    st.markdown("---")
    st.subheader("📊 Pipeline Status Summary")

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        crawl_status = get_dag_status("1_TIKTOK_ETL_COLLECTOR")
        crawl_info = get_dag_info("1_TIKTOK_ETL_COLLECTOR")
        _render_pipeline_status_card("Crawler Pipeline", crawl_status, crawl_info)

        # Pause/Unpause button cho Crawler
        is_crawl_paused = crawl_info.get("is_paused", True)
        if is_crawl_paused:
            if st.button(
                "▶️ Unpause Crawler", key="unpause_crawl", use_container_width=True
            ):
                success = pause_dag("1_TIKTOK_ETL_COLLECTOR", is_paused=False)
                if success:
                    st.toast("✅ Crawler đã được kích hoạt!")
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi unpause")
        else:
            if st.button(
                "⏸️ Pause Crawler", key="pause_crawl", use_container_width=True
            ):
                success = pause_dag("1_TIKTOK_ETL_COLLECTOR", is_paused=True)
                if success:
                    st.toast("✅ Crawler đã được tạm dừng!")
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi pause")

    with status_col2:
        stream_status = get_dag_status("2_TIKTOK_STREAMING_PIPELINE")
        stream_info = get_dag_info("2_TIKTOK_STREAMING_PIPELINE")
        _render_pipeline_status_card("Streaming Pipeline", stream_status, stream_info)

        # Pause/Unpause button cho Streaming
        is_stream_paused = stream_info.get("is_paused", True)
        if is_stream_paused:
            if st.button(
                "▶️ Unpause Stream", key="unpause_stream", use_container_width=True
            ):
                success = pause_dag("2_TIKTOK_STREAMING_PIPELINE", is_paused=False)
                if success:
                    st.toast("✅ Streaming đã được kích hoạt!")
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi unpause")
        else:
            if st.button(
                "⏸️ Pause Stream", key="pause_stream", use_container_width=True
            ):
                success = pause_dag("2_TIKTOK_STREAMING_PIPELINE", is_paused=True)
                if success:
                    st.toast("✅ Streaming đã được tạm dừng!")
                    st.rerun()
                else:
                    st.error("❌ Lỗi khi pause")

    # ========== PIPELINE CONTROL (ĐƯA XUỐNG DƯỚI) ==========
    st.markdown("---")
    st.subheader("🚀 Điều khiển Pipeline")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Crawler Pipeline")
        st.markdown(
            """
        **Chức năng:** Thu thập video TikTok
        - Crawl từ danh sách hashtag
        - Download video về MinIO
        - Extract metadata
        """
        )

        if st.button(
            "🚀 KÍCH HOẠT CRAWLER", key="trigger_crawl", use_container_width=True
        ):
            with st.spinner("Đang kích hoạt Crawler..."):
                success = trigger_dag("1_TIKTOK_ETL_COLLECTOR")
                if success:
                    st.success("✅ Đã gửi lệnh tới Airflow thành công!")
                    st.balloons()
                else:
                    st.error("❌ Không thể kết nối Airflow. Kiểm tra service.")

    with col2:
        st.markdown("### Streaming Pipeline")
        st.markdown(
            """
        **Chức năng:** Phân tích AI realtime
        - Kafka consumer nhận events
        - Spark streaming xử lý
        - AI Models phân loại
        - Lưu kết quả PostgreSQL
        """
        )

        if st.button(
            "⚡ KÍCH HOẠT STREAMING", key="trigger_stream", use_container_width=True
        ):
            with st.spinner("Đang kích hoạt Streaming..."):
                success = trigger_dag("2_TIKTOK_STREAMING_PIPELINE")
                if success:
                    st.success("✅ AI Streaming Engine đang khởi động!")
                    st.balloons()
                else:
                    st.error("❌ Không thể kết nối Airflow. Kiểm tra service.")


def _render_pipeline_status_card(name, status, info):
    """Render a pipeline status card with all info"""
    status_colors = {
        "running": ("#25F4EE", "🟢"),
        "success": ("#00C851", "✅"),
        "queued": ("#FFD93D", "🟡"),
        "failed": ("#FE2C55", "🔴"),
        "error": ("#FE2C55", "⚠️"),
        "unknown": ("#888888", "❓"),
    }
    color, icon = status_colors.get(status, ("#888888", "❓"))
    is_paused = info.get("is_paused", True)
    pause_badge = (
        '<span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; margin-left: 8px;">PAUSED</span>'
        if is_paused
        else '<span style="background: #51cf66; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; margin-left: 8px;">ACTIVE</span>'
    )

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border: 1px solid {color}40;
        border-left: 4px solid {color};
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #ffffff;">{name}</b>
            {pause_badge}
        </div>
        <div style="margin-top: 10px;">
            <span style="font-size: 1.5em;">{icon}</span>
            <span style="color: {color}; font-weight: bold; margin-left: 8px; font-size: 1.1em;">{status.upper()}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_status_monitor():
    """Render status monitoring section with detailed task logs"""
    st.subheader("📊 System Status")

    # Streaming Engine State
    st.markdown("### Streaming Engine")
    df = get_data()
    engine_state = infer_streaming_engine_state(df)

    state_info = {
        "idle": ("⚪", "Hệ thống chờ", "Chưa có video mới cần xử lý"),
        "waiting": ("⚪", "Hệ thống chờ", "Chưa có video mới cần xử lý"),
        "consuming": ("🟢", "Đang nhận dữ liệu", "Kafka consumer đang active"),
        "active": ("🟢", "Đang hoạt động", "Pipeline đang xử lý video"),
        "processing": ("🟡", "Đang xử lý AI", "Spark đang phân tích video"),
        "done": ("✅", "Hoàn tất", "Batch xử lý xong"),
        "error": ("🔴", "Có lỗi", "Kiểm tra logs để debug"),
    }

    state_key = (
        engine_state.get("state", "waiting")
        if isinstance(engine_state, dict)
        else engine_state
    )
    icon, label, desc = state_info.get(state_key, ("❓", "Unknown", "Không xác định"))

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    ">
        <h3 style="margin: 0; color: white;">{icon} {label}</h3>
        <p style="color: #aaa; margin: 5px 0 0 0;">{desc}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # DAG Run History with Task Details
    st.markdown("---")
    st.markdown("### 📋 DAG Run History & Task Logs")

    # DAG selector - use session state to persist selection
    dag_options = ["1_TIKTOK_ETL_COLLECTOR", "2_TIKTOK_STREAMING_PIPELINE"]
    selected_dag = st.selectbox(
        "Chọn DAG để xem chi tiết:",
        dag_options,
        index=dag_options.index(st.session_state.selected_dag_tab2),
        format_func=lambda x: (
            "🕷️ Crawler Pipeline" if "COLLECTOR" in x else "⚡ Streaming Pipeline"
        ),
        key="dag_selector_tab2",
    )
    # Update session state when selection changes
    st.session_state.selected_dag_tab2 = selected_dag

    # Get run history
    runs = get_dag_run_history(selected_dag, limit=5)

    if runs:
        # Show run history in expandable sections
        for run in runs:
            run_id = run.get("dag_run_id", "Unknown")
            state = run.get("state", "unknown")
            start_date = run.get("start_date", "")

            # State styling
            state_colors = {
                "success": "🟢",
                "running": "🔵",
                "failed": "🔴",
                "queued": "🟡",
                "scheduled": "⏳",
            }
            state_icon = state_colors.get(state, "❓")

            with st.expander(
                f"{state_icon} **{run_id}** - {state.upper()}",
                expanded=(state in ["running", "failed"]),
            ):
                st.markdown(f"**Start:** {start_date or 'N/A'}")
                st.markdown(f"**End:** {run.get('end_date') or 'Running...'}")

                # Get tasks for this run
                tasks = get_task_instances(selected_dag, run_id)

                if tasks:
                    st.markdown("#### Tasks:")
                    for task in tasks:
                        task_id = task.get("task_id", "")
                        task_state = task.get("state", "unknown")
                        duration = task.get("duration", 0)

                        task_colors = {
                            "success": "✅",
                            "running": "🔄",
                            "failed": "❌",
                            "upstream_failed": "⬆️❌",
                            "skipped": "⏭️",
                        }
                        task_icon = task_colors.get(task_state, "❓")

                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.markdown(f"{task_icon} **{task_id}**")
                        with col2:
                            st.markdown(f"_{task_state}_")
                        with col3:
                            if duration:
                                st.markdown(f"`{duration:.1f}s`")

                        # Show logs button for failed or running tasks
                        if task_state in ["failed", "running", "success"]:
                            log_key = f"log_{run_id}_{task_id}"

                            # Use checkbox instead of button to maintain state
                            show_logs = st.checkbox(
                                f"📜 Xem Logs: {task_id}",
                                key=f"show_{log_key}",
                                value=(st.session_state.active_log_key == log_key),
                            )

                            if show_logs:
                                # Update active log key
                                st.session_state.active_log_key = log_key
                                try_num = task.get("try_number", 1)

                                # Fetch and cache logs
                                with st.spinner("Đang tải logs..."):
                                    logs = get_task_logs(
                                        selected_dag, run_id, task_id, try_num
                                    )

                                if logs:
                                    # Terminal-style log display (black bg, green text)
                                    st.markdown(
                                        f"""
                                        <div style="
                                            background-color: #0d1117;
                                            border: 1px solid #30363d;
                                            border-radius: 6px;
                                            padding: 16px;
                                            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                                            font-size: 12px;
                                            color: #39ff14;
                                            max-height: 400px;
                                            overflow-y: auto;
                                            white-space: pre-wrap;
                                            word-wrap: break-word;
                                        ">
                                        <pre style="margin: 0; color: #39ff14; background: transparent;">{logs[-5000:]}</pre>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                    # Download button for logs
                                    st.download_button(
                                        label="📥 Download Log",
                                        data=logs,
                                        file_name=f"{task_id}_{run_id}.log",
                                        mime="text/plain",
                                        key=f"dl_{log_key}",
                                    )
                                else:
                                    st.info("Không có logs")
                else:
                    st.info("Chưa có tasks được thực thi")
    else:
        st.info("Chưa có lịch sử chạy DAG")


def _render_dag_status_badge(status):
    """Render a colored status badge for DAG status"""
    status_styles = {
        "running": ("#25F4EE", "🟢", "Running"),
        "success": ("#00C851", "✅", "Success"),
        "queued": ("#FFD93D", "🟡", "Queued"),
        "failed": ("#FE2C55", "🔴", "Failed"),
        "error": ("#FE2C55", "⚠️", "Connection Error"),
        "unknown": ("#888888", "❓", "Unknown"),
    }
    color, icon, label = status_styles.get(status, ("#888888", "❓", status))
    st.markdown(
        f"""
    <div style="
        background: {color}20;
        border-left: 4px solid {color};
        padding: 10px 15px;
        border-radius: 4px;
        margin: 5px 0;
    ">
        <span style="font-size: 1.2em;">{icon}</span>
        <span style="color: {color}; font-weight: bold; margin-left: 8px;">{label}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_system_logs():
    """Render system logs viewer"""
    st.subheader("📋 System Logs")

    # Log source selector
    log_source = st.selectbox(
        "Chọn nguồn log:",
        [
            "Database (PostgreSQL)",
            "MinIO Storage",
            "Airflow Scheduler",
            "Kafka",
            "Spark",
        ],
        index=0,
    )

    # Container mapping
    container_map = {
        "Database (PostgreSQL)": "postgres",
        "MinIO Storage": "minio",
        "Airflow Scheduler": "airflow-scheduler",
        "Kafka": "kafka",
        "Spark": "spark-master",
    }

    container_name = container_map.get(log_source, "postgres")

    # Options
    col1, col2 = st.columns(2)
    with col1:
        num_lines = st.slider("Số dòng log:", 20, 200, 50, step=10)
    with col2:
        log_filter = st.text_input("Filter (regex):", placeholder="ERROR|WARN")

    # Fetch logs button
    if st.button("📥 Lấy Logs", use_container_width=True):
        with st.spinner(f"Đang lấy logs từ {log_source}..."):
            logs = get_container_logs(container_name, num_lines)

            if log_filter:
                import re

                try:
                    pattern = re.compile(log_filter, re.IGNORECASE)
                    logs = "\n".join(
                        [line for line in logs.split("\n") if pattern.search(line)]
                    )
                except re.error:
                    st.warning("Invalid regex pattern")

            if logs:
                st.markdown("```")
                st.code(logs, language="log")
                st.markdown("```")
            else:
                st.info("Không có logs hoặc container không tồn tại")

    # Application Logs from DB
    st.markdown("---")
    st.subheader("📝 Application Logs (Database)")

    recent_logs = get_recent_logs(50)
    if not recent_logs.empty:
        # Color code by log level
        def style_log_level(val):
            colors = {
                "ERROR": "background-color: #FE2C55; color: white",
                "WARN": "background-color: #FFD93D; color: black",
                "INFO": "background-color: #25F4EE; color: black",
            }
            return colors.get(val, "")

        st.dataframe(
            recent_logs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn(
                    "Time", format="YYYY-MM-DD HH:mm:ss"
                ),
                "level": st.column_config.TextColumn("Level", width="small"),
                "component": st.column_config.TextColumn("Component", width="medium"),
                "message": st.column_config.TextColumn("Message", width="large"),
            },
        )
    else:
        st.info("Chưa có application logs trong database")
