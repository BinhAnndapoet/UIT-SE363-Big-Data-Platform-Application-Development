"""
Content Audit Page - Video Review & Gallery Mode
"""

import streamlit as st
import pandas as pd
from helpers import (
    get_video_url,
    find_blacklist_hits,
    highlight_keywords,
    render_header,
    get_all_data_paginated,
)
from config import BLACKLIST_KEYWORDS


def render_content_audit(df):
    """Render the content audit page with gallery mode"""
    render_header(
        title="Content Audit",
        subtitle="Kiểm duyệt nội dung video chi tiết với Gallery Mode.",
        icon="🔍",
    )

    # Help Panel
    with st.expander("📖 Hướng dẫn sử dụng Content Audit", expanded=False):
        st.markdown(
            """
        ### 🎯 Mục đích
        Trang này cho phép bạn **review chi tiết** từng video đã được AI phân loại.
        
        ### 🖼️ Gallery Mode
        - Xem **nhiều video cùng lúc** dạng grid
        - Filter theo **Category** (Harmful/Safe)
        - Click vào video để xem chi tiết
        - Pagination hỗ trợ xem **toàn bộ** collection
        
        ### 🔍 Detail View
        - Xem **video player** trực tiếp
        - Hiển thị **transcript/caption** với keyword highlighting
        - Xem **AI scores** chi tiết (text, video, audio)
        - **Blacklist keywords** được đánh dấu đỏ
        
        ### 📊 Filters
        - **Category**: Harmful / Safe / All
        - **Score Range**: Lọc theo điểm AI
        - **Search**: Tìm kiếm theo video ID hoặc text
        """
        )

    if df.empty:
        st.warning("⚠️ Chưa có dữ liệu. Vui lòng chạy Pipeline trước.")
        return

    # View Mode Toggle
    view_mode = st.radio(
        "📺 Chế độ xem:",
        ["🖼️ Gallery Mode", "📋 Detail View", "📊 Table View"],
        horizontal=True,
    )

    # Filters
    st.markdown("### 🔍 Bộ lọc")
    f1, f2, f3 = st.columns(3)

    with f1:
        category_filter = st.selectbox(
            "Category:",
            ["All", "Harmful", "Safe"],
            index=0,
        )

    with f2:
        if "avg_score" in df.columns:
            score_range = st.slider(
                "Score Range:",
                0.0,
                1.0,
                (0.0, 1.0),
                step=0.05,
            )
        else:
            score_range = (0.0, 1.0)

    with f3:
        search_query = st.text_input(
            "🔎 Search:", placeholder="Video ID hoặc keyword..."
        )

    # Apply filters
    filtered_df = df.copy()

    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]

    if "avg_score" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["avg_score"] >= score_range[0])
            & (filtered_df["avg_score"] <= score_range[1])
        ]

    if search_query:
        mask = filtered_df["video_id"].astype(str).str.contains(
            search_query, case=False, na=False
        ) | (
            filtered_df["transcript"].str.contains(search_query, case=False, na=False)
            if "transcript" in filtered_df.columns
            else False
        )
        filtered_df = filtered_df[mask]

    st.info(f"📊 Hiển thị **{len(filtered_df):,}** / {len(df):,} videos")

    # Render based on view mode
    if "Gallery" in view_mode:
        _render_gallery_mode(filtered_df)
    elif "Detail" in view_mode:
        _render_detail_view(filtered_df)
    else:
        _render_table_view(filtered_df)


def _render_gallery_mode(df):
    """Render gallery mode with pagination"""
    st.subheader("🖼️ Video Gallery")

    if df.empty:
        st.warning("Không có video nào phù hợp với bộ lọc")
        return

    # Initialize session state for pagination
    if "gallery_page" not in st.session_state:
        st.session_state.gallery_page = 1
    if "items_per_page" not in st.session_state:
        st.session_state.items_per_page = 12

    # Pagination settings
    items_per_page = st.select_slider(
        "Videos per page:",
        options=[6, 12, 18, 24, 30],
        value=st.session_state.items_per_page,
        key="items_slider",
    )

    # Update session state if slider changed
    if items_per_page != st.session_state.items_per_page:
        st.session_state.items_per_page = items_per_page
        st.session_state.gallery_page = (
            1  # Reset to page 1 when changing items per page
        )

    total_pages = max(1, (len(df) + items_per_page - 1) // items_per_page)

    # Ensure current page is valid
    if st.session_state.gallery_page > total_pages:
        st.session_state.gallery_page = total_pages

    current_page = st.session_state.gallery_page

    # Pagination controls - clear button layout
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])

    with col_prev:
        if current_page > 1:
            if st.button("◀️ Previous Page", key="prev_btn", use_container_width=True):
                st.session_state.gallery_page = current_page - 1
                st.rerun()
        else:
            st.button(
                "◀️ Previous Page",
                key="prev_btn_disabled",
                disabled=True,
                use_container_width=True,
            )

    with col_info:
        st.markdown(
            f"<div style='text-align: center; padding: 10px 15px; background: linear-gradient(135deg, #25F4EE20 0%, #FE2C5520 100%); border: 1px solid #ffffff20; border-radius: 8px;'>"
            f"<b style='color: #ffffff;'>Page {current_page} / {total_pages}</b> <span style='color: #aaa;'>({len(df)} videos)</span></div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if current_page < total_pages:
            if st.button("Next Page ▶️", key="next_btn", use_container_width=True):
                st.session_state.gallery_page = current_page + 1
                st.rerun()
        else:
            st.button(
                "Next Page ▶️",
                key="next_btn_disabled",
                disabled=True,
                use_container_width=True,
            )

    st.markdown("---")

    # Get current page data
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(df))
    page_df = df.iloc[start_idx:end_idx]

    # Render grid
    cols_per_row = 3
    rows = (len(page_df) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            item_idx = row * cols_per_row + col_idx
            if item_idx < len(page_df):
                item = page_df.iloc[item_idx]
                with cols[col_idx]:
                    _render_video_card(item)


def _render_video_card(item):
    """Render a single video card in gallery"""
    is_harmful = item.get("Category", "Safe") == "Harmful"
    badge_class = "badge-harm" if is_harmful else "badge-safe"
    badge_text = "⚠️ Harmful" if is_harmful else "✅ Safe"

    video_url = get_video_url(item.get("video_id", ""), item.get("Category", "Safe"))
    score = item.get("avg_score", 0)

    st.markdown(
        f"""
    <div class="video-card">
        <div class="video-card-header">
            <span class="{badge_class}">{badge_text}</span>
            <span style="color: #aaa; font-size: 0.8em;">Score: {score:.3f}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Video ID (clickable to expand)
    video_id = item.get("video_id", "Unknown")

    with st.expander(f"📹 {str(video_id)[:20]}...", expanded=False):
        # Video player
        if video_url:
            st.video(video_url)
        else:
            st.warning("Video không khả dụng")

        # Quick stats
        st.markdown(
            f"""
        - **ID**: `{video_id}`
        - **Text**: {item.get('text_verdict', 'N/A')} ({item.get('text_score', 0):.3f})
        - **Video**: {item.get('video_verdict', 'N/A')} ({item.get('video_score', 0):.3f})
        """
        )

        # Blacklist check
        transcript = item.get("transcript", "")
        if transcript:
            hits = find_blacklist_hits(transcript)
            if hits:
                st.error(f"🚨 Blacklist: {', '.join(hits)}")


def _render_detail_view(df):
    """Render detailed single video view"""
    st.subheader("📋 Chi tiết Video")

    if df.empty:
        st.warning("Không có video nào phù hợp với bộ lọc")
        return

    # Video selector
    video_ids = df["video_id"].tolist()
    selected_id = st.selectbox(
        "Chọn Video ID:",
        video_ids,
        format_func=lambda x: f"{x} - {df[df['video_id']==x]['Category'].values[0] if len(df[df['video_id']==x]) > 0 else 'Unknown'}",
    )

    if selected_id:
        video_data = df[df["video_id"] == selected_id].iloc[0]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 📹 Video Player")
            video_url = get_video_url(selected_id, video_data.get("Category", "Safe"))
            if video_url:
                st.video(video_url)
            else:
                st.error("❌ Video không khả dụng")
                st.info(f"Expected URL: {video_url}")

        with col2:
            st.markdown("### 📊 AI Analysis Results")

            # Category badge
            is_harmful = video_data.get("Category", "Safe") == "Harmful"
            if is_harmful:
                st.error("⚠️ **HARMFUL CONTENT DETECTED**")
            else:
                st.success("✅ **SAFE CONTENT**")

            # Scores
            st.markdown("#### 🎯 Điểm số chi tiết")

            scores_df = pd.DataFrame(
                {
                    "Model": ["Text", "Video", "Audio", "Average"],
                    "Score": [
                        video_data.get("text_score", 0),
                        video_data.get("video_score", 0),
                        video_data.get("audio_score", 0),
                        video_data.get("avg_score", 0),
                    ],
                    "Verdict": [
                        video_data.get("text_verdict", "N/A"),
                        video_data.get("video_verdict", "N/A"),
                        video_data.get("audio_verdict", "N/A"),
                        video_data.get("Category", "N/A"),
                    ],
                }
            )

            st.dataframe(scores_df, use_container_width=True, hide_index=True)

            # Threshold info
            st.caption("Threshold: 0.5 (Score >= 0.5 → Harmful)")

        # Transcript section
        st.markdown("---")
        st.markdown("### 📝 Transcript / Caption")

        transcript = video_data.get("transcript", "")
        if transcript and str(transcript) != "nan":
            # Find blacklist hits
            hits = find_blacklist_hits(str(transcript))

            if hits:
                st.error(
                    f"🚨 **Phát hiện {len(hits)} từ khóa blacklist:** {', '.join(hits)}"
                )

            # Highlighted transcript
            highlighted = highlight_keywords(str(transcript), BLACKLIST_KEYWORDS)
            st.markdown(
                f"""
            <div style="
                background: #1a1a2e;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {'#FE2C55' if is_harmful else '#25F4EE'};
                line-height: 1.6;
            ">
                {highlighted}
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.info("📭 Không có transcript cho video này")

        # Metadata
        st.markdown("---")
        st.markdown("### 📋 Metadata")

        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"""
            - **Video ID**: `{selected_id}`
            - **Processed At**: {video_data.get('processed_at', 'N/A')}
            """
            )
        with meta_col2:
            st.markdown(
                f"""
            - **Source**: TikTok
            - **Status**: Processed ✅
            """
            )


def _render_table_view(df):
    """Render table view of all videos"""
    st.subheader("📊 Table View")

    # Column selector
    available_cols = df.columns.tolist()
    default_cols = [
        "video_id",
        "Category",
        "avg_score",
        "text_verdict",
        "video_verdict",
        "processed_at",
    ]
    selected_cols = st.multiselect(
        "Chọn cột hiển thị:",
        available_cols,
        default=[c for c in default_cols if c in available_cols],
    )

    if selected_cols:
        display_df = df[selected_cols].copy()

        # Format scores
        for col in display_df.columns:
            if "score" in col.lower():
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"
                )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"content_audit_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Vui lòng chọn ít nhất 1 cột để hiển thị")
