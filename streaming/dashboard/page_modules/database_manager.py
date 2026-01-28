"""
Database Manager Page - Database Administration & Query Tool
"""

import streamlit as st
import pandas as pd
from helpers import (
    render_header,
    get_database_tables,
    get_table_info,
    execute_query,
    get_db_connection,
)


def render_database_manager():
    """Render the database management page"""
    render_header(
        title="Database Manager",
        subtitle="Quản lý và truy vấn PostgreSQL Database.",
        icon="🗄️",
    )

    # Help Panel
    with st.expander("📖 Hướng dẫn sử dụng Database Manager", expanded=False):
        st.markdown(
            """
        ### 🎯 Mục đích
        Trang này cho phép bạn **quản lý trực tiếp** PostgreSQL database của hệ thống.
        
        ### 🔧 Chức năng
        - **📋 Table Browser**: Xem danh sách tables và schema
        - **🔍 Query Tool**: Chạy SQL queries trực tiếp
        - **📊 Statistics**: Xem thống kê database
        - **📥 Export**: Xuất dữ liệu ra CSV
        
        ### ⚠️ Lưu ý an toàn
        - Chỉ **SELECT** queries được phép
        - Không thể chạy **DELETE/UPDATE/DROP** từ giao diện này
        - Backup data trước khi thực hiện thay đổi lớn
        
        ### 📊 Main Tables
        | Table | Description |
        |-------|-------------|
        | `processed_results` | Kết quả phân loại AI |
        | `system_logs` | Logs hệ thống |
        """
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Table Browser", "🔍 Query Tool", "📊 Statistics", "🔧 Maintenance"]
    )

    with tab1:
        _render_table_browser()

    with tab2:
        _render_query_tool()

    with tab3:
        _render_statistics()

    with tab4:
        _render_maintenance()


def _render_table_browser():
    """Render table browser section"""
    st.subheader("📋 Database Tables")

    # Get list of tables
    tables = get_database_tables()

    if not tables:
        st.warning("Không thể kết nối database hoặc không có tables")
        return

    st.success(f"✅ Tìm thấy **{len(tables)}** tables")

    # Table selector
    selected_table = st.selectbox(
        "Chọn table để xem:",
        tables,
        index=0 if tables else None,
    )

    if selected_table:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📐 Schema")
            schema_info = get_table_info(selected_table)
            if schema_info is not None and not schema_info.empty:
                st.dataframe(schema_info, use_container_width=True, hide_index=True)
            else:
                st.info("Không có thông tin schema")

        with col2:
            st.markdown("### 📊 Preview Data")

            # Row limit
            row_limit = st.slider("Số rows hiển thị:", 5, 100, 20)

            # Fetch data
            query = f"SELECT * FROM {selected_table} LIMIT {row_limit}"
            data, error = execute_query(query)

            if error:
                st.error(f"Lỗi: {error}")
            elif data is not None and not data.empty:
                st.dataframe(data, use_container_width=True, hide_index=True)

                # Row count
                count_query = f"SELECT COUNT(*) as total FROM {selected_table}"
                count_result, _ = execute_query(count_query)
                if count_result is not None:
                    total_rows = count_result.iloc[0]["total"]
                    st.caption(f"Tổng số rows: **{total_rows:,}**")
            else:
                st.info("Table rỗng")


def _render_query_tool():
    """Render SQL query tool"""
    st.subheader("🔍 SQL Query Tool")

    st.warning(
        "⚠️ **Chỉ SELECT queries được phép**. DELETE/UPDATE/DROP bị vô hiệu hóa vì lý do an toàn."
    )

    # Query templates
    st.markdown("### 📝 Quick Templates")

    templates = {
        "Tất cả kết quả": "SELECT * FROM processed_results ORDER BY processed_at DESC LIMIT 100",
        "Chỉ Harmful": "SELECT * FROM processed_results WHERE category = 'Harmful' ORDER BY avg_score DESC",
        "Chỉ Safe": "SELECT * FROM processed_results WHERE category = 'Safe' ORDER BY avg_score ASC",
        "Thống kê theo ngày": """
            SELECT 
                DATE(processed_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN category = 'Harmful' THEN 1 ELSE 0 END) as harmful,
                SUM(CASE WHEN category = 'Safe' THEN 1 ELSE 0 END) as safe
            FROM processed_results 
            GROUP BY DATE(processed_at)
            ORDER BY date DESC
        """,
        "Top 10 Harmful scores": "SELECT video_id, avg_score, text_score, video_score FROM processed_results ORDER BY avg_score DESC LIMIT 10",
        "Count by category": "SELECT category, COUNT(*) as count FROM processed_results GROUP BY category",
    }

    template_choice = st.selectbox(
        "Chọn template:", ["Custom"] + list(templates.keys())
    )

    if template_choice != "Custom":
        default_query = templates[template_choice]
    else:
        default_query = "SELECT * FROM processed_results LIMIT 10"

    # Query input
    query = st.text_area(
        "SQL Query:",
        value=default_query,
        height=150,
        help="Nhập SQL query. Chỉ SELECT được phép.",
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        run_query = st.button("▶️ Execute", type="primary", use_container_width=True)

    with col2:
        st.caption("💡 Tip: Dùng LIMIT để tránh query quá lớn")

    # Execute query
    if run_query:
        # Safety check
        query_upper = query.upper().strip()
        if any(
            kw in query_upper
            for kw in ["DELETE", "UPDATE", "DROP", "TRUNCATE", "ALTER", "INSERT"]
        ):
            st.error("❌ **Query không được phép!** Chỉ SELECT queries được chấp nhận.")
        else:
            with st.spinner("Đang thực thi query..."):
                result, error = execute_query(query)

                if error:
                    st.error(f"❌ **Lỗi:** {error}")
                elif result is not None:
                    st.success(f"✅ Query thành công! Trả về **{len(result):,}** rows")

                    # Display results
                    st.dataframe(
                        result, use_container_width=True, hide_index=True, height=400
                    )

                    # Download button
                    csv = result.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"query_result_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("Query không trả về kết quả")


def _render_statistics():
    """Render database statistics"""
    st.subheader("📊 Database Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Overview")

        # Total records
        query = "SELECT COUNT(*) as total FROM processed_results"
        result, _ = execute_query(query)
        total = result.iloc[0]["total"] if result is not None else 0

        # Category breakdown
        query2 = "SELECT category, COUNT(*) as count FROM processed_results GROUP BY category"
        cat_result, _ = execute_query(query2)

        st.metric("📹 Total Videos Processed", f"{total:,}")

        if cat_result is not None and not cat_result.empty:
            for _, row in cat_result.iterrows():
                cat = row["category"]
                count = row["count"]
                icon = "⚠️" if cat == "Harmful" else "✅"
                st.metric(f"{icon} {cat}", f"{count:,}")

    with col2:
        st.markdown("### 📉 Score Distribution")

        query = """
            SELECT 
                ROUND(avg_score::numeric, 1) as score_bucket,
                COUNT(*) as count
            FROM processed_results
            GROUP BY ROUND(avg_score::numeric, 1)
            ORDER BY score_bucket
        """
        dist_result, _ = execute_query(query)

        if dist_result is not None and not dist_result.empty:
            import plotly.express as px

            fig = px.bar(
                dist_result,
                x="score_bucket",
                y="count",
                title="Distribution of Average Scores",
                labels={"score_bucket": "Score", "count": "Count"},
            )
            fig.update_layout(
                xaxis_title="Score Bucket",
                yaxis_title="Count",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    # Processing timeline
    st.markdown("---")
    st.markdown("### 📅 Processing Timeline")

    query = """
        SELECT 
            DATE(processed_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN category = 'Harmful' THEN 1 ELSE 0 END) as harmful,
            SUM(CASE WHEN category = 'Safe' THEN 1 ELSE 0 END) as safe
        FROM processed_results 
        WHERE processed_at IS NOT NULL
        GROUP BY DATE(processed_at)
        ORDER BY date DESC
        LIMIT 30
    """
    timeline_result, _ = execute_query(query)

    if timeline_result is not None and not timeline_result.empty:
        import plotly.express as px

        fig = px.line(
            timeline_result,
            x="date",
            y=["total", "harmful", "safe"],
            title="Videos Processed Over Time",
            labels={"value": "Count", "date": "Date"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu timeline")


def _render_maintenance():
    """Render database maintenance section"""
    st.subheader("🔧 Database Maintenance")

    st.warning(
        "⚠️ **Khu vực quản trị viên!** Các thao tác này có thể ảnh hưởng đến dữ liệu."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Health Check")

        if st.button("🔍 Check Connection", use_container_width=True):
            try:
                conn = get_db_connection()
                if conn:
                    st.success("✅ Database connection OK")
                    conn.close()
                else:
                    st.error("❌ Cannot connect to database")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")

        if st.button("📋 Table Sizes", use_container_width=True):
            query = """
                SELECT 
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                    pg_size_pretty(pg_relation_size(relid)) as data_size
                FROM pg_catalog.pg_statio_user_tables 
                ORDER BY pg_total_relation_size(relid) DESC
            """
            result, error = execute_query(query)
            if result is not None:
                st.dataframe(result, use_container_width=True, hide_index=True)
            else:
                st.error(f"Error: {error}")

    with col2:
        st.markdown("### 📥 Export Data")

        export_table = st.selectbox(
            "Table to export:",
            get_database_tables() or [],
            key="export_table",
        )

        if export_table:
            if st.button("📥 Export Full Table", use_container_width=True):
                with st.spinner("Exporting..."):
                    query = f"SELECT * FROM {export_table}"
                    result, error = execute_query(query)

                    if result is not None:
                        csv = result.to_csv(index=False)
                        st.download_button(
                            label=f"💾 Download {export_table}.csv",
                            data=csv,
                            file_name=f"{export_table}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key="export_csv_btn",
                        )
                        st.success(f"✅ Exported {len(result):,} rows")
                    else:
                        st.error(f"Export failed: {error}")

    # Database info
    st.markdown("---")
    st.markdown("### ℹ️ Database Information")

    info_query = """
        SELECT 
            current_database() as database_name,
            pg_size_pretty(pg_database_size(current_database())) as database_size,
            (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as active_connections
    """
    info_result, _ = execute_query(info_query)

    if info_result is not None:
        st.json(
            {
                "Database": info_result.iloc[0]["database_name"],
                "Size": info_result.iloc[0]["database_size"],
                "Active Connections": int(info_result.iloc[0]["active_connections"]),
            }
        )
