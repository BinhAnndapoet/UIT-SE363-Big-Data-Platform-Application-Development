"""
TikTok Safety Dashboard - Main Entry Point
Modular version with separate pages and helpers
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# Import modules
from config import DB_CONFIG, MINIO_CONF, APP_CONFIG
from styles import get_styles
from helpers import get_data

# Import pages
from page_modules import (
    render_dashboard_monitor,
    render_system_operations,
    render_content_audit,
    render_project_info,
    render_database_manager,
)

# --- 1. PAGE CONFIG ---
st.set_page_config(
    layout="wide",
    page_title="SE363 | Big Data Platform Project",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# --- 2. APPLY STYLES ---
st.markdown(get_styles(), unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/en/thumb/a/a9/TikTok_logo.svg/2560px-TikTok_logo.svg.png",
    width=140,
)

with st.sidebar:
    selected = option_menu(
        "Navigation",
        [
            "Dashboard Monitor",
            "System Operations",
            "Content Audit",
            "Database Manager",
            "Project Info",
        ],
        icons=["activity", "cpu", "shield-check", "database", "info-circle"],
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
    st.caption("Version 3.0 | Modular Release 2025")

# --- 4. AUTO REFRESH (Only for Dashboard Monitor page) ---
# Disable auto-refresh on System Operations to prevent page reset while viewing logs
if selected == "Dashboard Monitor":
    st_autorefresh(interval=APP_CONFIG["refresh_interval"], key="global_refresh")

# --- 5. LOAD DATA ---
df = get_data()

# --- 6. RENDER SELECTED PAGE ---
if selected == "Dashboard Monitor":
    render_dashboard_monitor(df)

elif selected == "System Operations":
    render_system_operations()

elif selected == "Content Audit":
    render_content_audit(df)

elif selected == "Database Manager":
    render_database_manager()

elif selected == "Project Info":
    render_project_info()
