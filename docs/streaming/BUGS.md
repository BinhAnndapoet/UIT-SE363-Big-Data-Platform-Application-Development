# 🐛 BUGS.md - Known Issues & Fixes

## Overview
Tài liệu này ghi nhận các bugs đã gặp và cách khắc phục trong quá trình phát triển TikTok Safety Big Data Pipeline.

---

## 🔴 Critical Bugs (Đã Fix)

### BUG-001: DAG Always Shows "Queued" Status
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Critical  
**Triệu chứng:**
- Pipeline trigger xong nhưng status luôn hiện "queued"
- DAG không thực sự chạy

**Nguyên nhân:**
- DAGs đang ở trạng thái PAUSED trong Airflow
- Khi DAG paused, trigger mới sẽ vào hàng đợi nhưng không chạy

**Giải pháp:**
```python
# helpers.py - trigger_dag() function
def trigger_dag(dag_id):
    # First unpause the DAG
    unpause_url = f"{AIRFLOW_API_URL}/{dag_id}"
    requests.patch(unpause_url, json={"is_paused": False}, auth=AIRFLOW_AUTH)
    
    # Then trigger it
    url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns"
    response = requests.post(url, json={"conf": {}}, auth=AIRFLOW_AUTH)
    return response.status_code == 200
```

**File affected:** `streaming/dashboard/helpers.py`

---

### BUG-002: DAG Run History JSON Parse Error
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Critical  
**Triệu chứng:**
- Dashboard crash với error: `st.json() received string "unknown"`
- Status Monitor tab không hiển thị được

**Nguyên nhân:**
- `get_dag_status()` trả về string "unknown" khi không có data
- Code gọi `st.json()` với string thay vì dict

**Giải pháp:**
- Thay thế `st.json()` bằng colored status badges
- Dùng `_render_dag_status_badge()` function

**File affected:** `streaming/dashboard/page_modules/system_operations.py`

---

### BUG-003: Gallery Pagination Buttons Show as +/-
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Medium  
**Triệu chứng:**
- Pagination buttons hiển thị "+" và "-" thay vì "Previous" và "Next"
- Buttons không click được

**Nguyên nhân:**
- Sử dụng `st.button()` với ký tự đặc biệt trong label
- Layout columns không đúng

**Giải pháp:**
```python
# Fixed button labels
if st.button("◀️ Previous", key="prev_page"):
    st.session_state.gallery_page -= 1
    st.rerun()

if st.button("Next Page ▶️", key="next_page"):
    st.session_state.gallery_page += 1
    st.rerun()
```

**File affected:** `streaming/dashboard/page_modules/content_audit.py`

---

### BUG-004: Video URLs Point to localhost
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Critical  
**Triệu chứng:**
- Videos không play được trên remote browser
- URL hiển thị `localhost:9000` thay vì Tailscale IP

**Nguyên nhân:**
- `MINIO_PUBLIC_ENDPOINT` hardcode localhost
- Config không đọc từ environment variable

**Giải pháp:**
```python
# config.py
PUBLIC_HOST = extract_host_from_minio_endpoint()  # 100.69.255.87

EXTERNAL_URLS = {
    "airflow": f"http://{PUBLIC_HOST}:8080",
    "minio_console": f"http://{PUBLIC_HOST}:9001",
}
```

**File affected:** `streaming/dashboard/config.py`

---

### BUG-005: Refresh Status Button Not Working
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Medium  
**Triệu chứng:**
- Click "Refresh Status" không có phản hồi
- Data không cập nhật

**Nguyên nhân:**
- `st.rerun()` không clear cache
- Cached data TTL quá dài

**Giải pháp:**
```python
if st.button("🔄 Refresh Page", key="refresh_btn"):
    st.cache_data.clear()  # Clear cache trước
    st.rerun()
```

**File affected:** `streaming/dashboard/page_modules/system_operations.py`

---

## 🟡 Medium Bugs (Đã Fix)

### BUG-006: Import Path Error in main_worker.py
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Medium  
**Triệu chứng:**
- `ModuleNotFoundError: No module named 'modules'`
- Ingestion worker không chạy được

**Nguyên nhân:**
- Folder structure thay đổi sau refactor
- Import path cũ không còn đúng

**Giải pháp:**
```python
# main_worker.py - Updated imports
from clients.minio_kafka_clients import MinioClient, KafkaClient
from clients.data_cleaner import clean_text_advanced
from downloader import download_video_to_temp_mobile
from audio_processor import extract_audio_single
```

**File affected:** `streaming/ingestion/main_worker.py`

---

### BUG-007: AI Model Cards CSS Not Displaying
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Low  
**Triệu chứng:**
- AI Model cards không hiện đúng style
- Background color không apply

**Nguyên nhân:**
- CSS selector conflict
- Streamlit unsafe_allow_html CSS override

**Giải pháp:**
- Inline CSS với `!important` flags
- Sử dụng unique class names

**File affected:** `streaming/dashboard/page_modules/project_info.py`

---

### BUG-008: Page Info Background Too Light
**Ngày phát hiện:** 2025-01-01  
**Mức độ:** Low  
**Triệu chứng:**
- Page info section background quá nhạt
- Text khó đọc

**Giải pháp:**
```python
st.markdown(f"""
<div style="
    background: rgba(30, 30, 60, 0.3);  # Thay đổi từ 0.1 -> 0.3
    ...
">
""", unsafe_allow_html=True)
```

**File affected:** `streaming/dashboard/page_modules/content_audit.py`

---

## 🟢 Known Issues (Pending)

### ISSUE-001: Comment-VideoID Mapping
**Status:** Investigating  
**Triệu chứng:**
- Comments có thể không match đúng video_id
- Data preprocessing chưa tối ưu

**Root Cause (đang phân tích):**
- Crawler lấy description thay vì comments thực tế
- yt-dlp không trả về comments API

**Proposed Fix:**
- Integrate logic từ `preprocess/merge_comments_new.py`
- Implement proper comment aggregation per video_id

---

### ISSUE-002: Crawler Captcha/Block
**Status:** Known limitation  
**Triệu chứng:**
- TikTok block sau một thời gian crawl
- Captcha xuất hiện

**Mitigations:**
- Cookies refresh
- Random delays (8-12s)
- Browser restart sau 45 phút

---

### ISSUE-003: System Logs Table Missing
**Status:** Optional feature  
**Triệu chứng:**
- `system_logs` table không tồn tại trong một số setup

**Fix:**
```sql
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    component VARCHAR(100),
    message TEXT,
    dag_id VARCHAR(100),
    task_name VARCHAR(100)
);
```

---

## 📝 Bug Report Template

```markdown
### BUG-XXX: [Title]
**Ngày phát hiện:** YYYY-MM-DD  
**Mức độ:** Critical/Medium/Low  
**Triệu chứng:**
- 

**Nguyên nhân:**
- 

**Giải pháp:**
```code
```

**File affected:** 
```

---

## 📊 Statistics

| Status | Count |
|--------|-------|
| Fixed | 8 |
| Pending | 3 |
| Total | 11 |

---

## 🔄 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-01 | 1.0 | Initial bug tracking |
| 2025-01-01 | 1.1 | Fixed DAG status, pagination, video URLs |
| 2025-01-01 | 1.2 | Added task logs viewer, UI reorder |
