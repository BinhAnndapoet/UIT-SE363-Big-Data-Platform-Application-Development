"""
Dashboard Monitor Page - Analytics and KPIs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from helpers import render_header, render_help_panel, get_system_stats


def render_dashboard_monitor(df):
    """Render the main dashboard monitor page"""
    render_header(
        title="Analytics Dashboard",
        subtitle="Hệ thống giám sát thời gian thực luồng dữ liệu TikTok.",
        icon="📊",
    )

    # Help Panel
    with st.expander("📖 Hướng dẫn sử dụng Dashboard", expanded=False):
        st.markdown(
            """
        ### 🎯 Mục đích
        Dashboard này hiển thị **thống kê real-time** về các video TikTok đã được xử lý bởi hệ thống AI.
        
        ### 📊 Các chỉ số quan trọng (KPIs)
        - **Total Processed**: Tổng số video đã phân tích
        - **Harmful Detected**: Số video phát hiện có nội dung độc hại
        - **Safe Content**: Số video an toàn
        - **Risk Score**: Điểm rủi ro trung bình (0-10)
        
        ### 📈 Biểu đồ
        - **Pie Chart**: Tỷ lệ phân bố Harmful vs Safe
        - **Timeline**: Số lượng video xử lý theo thời gian
        - **Score Distribution**: Phân bố điểm số AI
        
        ### 🔄 Auto-refresh
        Dashboard tự động cập nhật mỗi **30 giây**.
        """
        )

    if df.empty:
        st.warning(
            "⚠️ Hệ thống chưa có dữ liệu. Vui lòng chuyển sang tab **System Operations** để chạy Pipeline."
        )

        # Show quick start guide
        st.info(
            """
        ### 🚀 Quick Start Guide
        1. Vào **System Operations** → Click **🚀 KÍCH HOẠT CRAWLER**
        2. Đợi Crawler hoàn tất (khoảng 2-5 phút)
        3. Click **⚡ KÍCH HOẠT STREAMING** để xử lý AI
        4. Quay lại Dashboard để xem kết quả
        """
        )
        return

    # Row 1: KPI Metrics
    st.subheader("📌 Chỉ số Quan trọng (KPIs)")
    m1, m2, m3, m4 = st.columns(4)

    total = len(df)
    harmful = len(df[df["Category"] == "Harmful"])
    safe = total - harmful
    risk_score = df["avg_score"].mean() if "avg_score" in df.columns else 0
    risk_score_10 = risk_score * 10

    with m1:
        st.metric(
            label="📹 Total Processed",
            value=f"{total:,}",
            delta=(
                f"+{len(df[df['processed_at'] > pd.Timestamp.now() - pd.Timedelta(hours=1)])} (1h)"
                if "processed_at" in df.columns
                else None
            ),
        )
    with m2:
        st.metric(
            label="⚠️ Harmful Detected",
            value=f"{harmful:,}",
            delta=f"{harmful/total*100:.1f}%" if total > 0 else "0%",
            delta_color="inverse",
        )
    with m3:
        st.metric(
            label="✅ Safe Content",
            value=f"{safe:,}",
            delta=f"{safe/total*100:.1f}%" if total > 0 else "0%",
        )
    with m4:
        st.metric(
            label="🎯 Avg Risk Score",
            value=f"{risk_score_10:.1f}/10",
            delta=(
                "Low Risk"
                if risk_score_10 < 4
                else ("Medium" if risk_score_10 < 7 else "High Risk")
            ),
            delta_color=(
                "normal"
                if risk_score_10 < 4
                else ("off" if risk_score_10 < 7 else "inverse")
            ),
        )

    st.markdown("---")

    # Row 2: Charts
    st.subheader("📈 Phân tích Trực quan")
    c1, c2 = st.columns(2)

    with c1:
        # Pie Chart - Enhanced
        fig_pie = px.pie(
            df,
            names="Category",
            title="🎯 Tỷ lệ Phân loại Nội dung",
            color="Category",
            color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
            hole=0.4,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont_size=14,
            marker=dict(line=dict(color="white", width=2)),
        )
        fig_pie.update_layout(
            font=dict(family="Inter", size=12),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
            ),
            margin=dict(t=60, b=60, l=20, r=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        # Timeline Chart
        if "processed_at" in df.columns:
            df_time = df.copy()
            df_time["hour"] = df_time["processed_at"].dt.floor("H")
            time_agg = (
                df_time.groupby(["hour", "Category"]).size().reset_index(name="count")
            )

            fig_time = px.area(
                time_agg,
                x="hour",
                y="count",
                color="Category",
                title="📅 Timeline: Video được xử lý theo thời gian",
                color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
            )
            fig_time.update_layout(
                font=dict(family="Inter", size=12),
                xaxis_title="Thời gian",
                yaxis_title="Số lượng",
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5
                ),
                margin=dict(t=60, b=80, l=20, r=20),
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Không có dữ liệu timeline")

    # Row 3: Score Distribution
    st.subheader("🔬 Phân bố Điểm số AI")
    c3, c4 = st.columns(2)

    with c3:
        if "avg_score" in df.columns:
            fig_hist = px.histogram(
                df,
                x="avg_score",
                nbins=20,
                color="Category",
                title="📊 Phân bố Average Score",
                color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                barmode="overlay",
                opacity=0.7,
            )
            fig_hist.update_layout(
                font=dict(family="Inter", size=12),
                xaxis_title="Average Score (0-1)",
                yaxis_title="Số lượng",
                bargap=0.1,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    with c4:
        if "text_score" in df.columns and "video_score" in df.columns:
            fig_scat = px.scatter(
                df,
                x="text_score",
                y="video_score",
                color="Category",
                title="🔍 Text Score vs Video Score",
                color_discrete_map={"Harmful": "#FE2C55", "Safe": "#25F4EE"},
                opacity=0.6,
                hover_data=["video_id"],
            )
            fig_scat.update_traces(marker=dict(size=8))
            fig_scat.update_layout(
                font=dict(family="Inter", size=12),
                xaxis_title="Text Model Score",
                yaxis_title="Video Model Score",
            )
            st.plotly_chart(fig_scat, use_container_width=True)

    # Row 4: Recent Activity Table
    st.subheader("🕐 Hoạt động Gần đây")

    recent_df = df.head(10)[
        [
            "video_id",
            "Category",
            "avg_score",
            "text_verdict",
            "video_verdict",
            "processed_at",
        ]
    ].copy()
    recent_df["avg_score"] = recent_df["avg_score"].apply(
        lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
    )
    recent_df["processed_at"] = recent_df["processed_at"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    st.dataframe(
        recent_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "video_id": st.column_config.TextColumn("Video ID", width="medium"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "avg_score": st.column_config.TextColumn("Score", width="small"),
            "text_verdict": st.column_config.TextColumn("Text", width="small"),
            "video_verdict": st.column_config.TextColumn("Video", width="small"),
            "processed_at": st.column_config.TextColumn("Time", width="medium"),
        },
    )
