# 🎨 UI/UX CHECKLIST - STREAMING DASHBOARD
## Phân tích các vấn đề UI/UX hiện tại

> **Ngày tạo:** 2025-01-27  
> **Mục đích:** Liệt kê các vấn đề UI/UX cần cải thiện

---

## 📋 TỔNG QUAN DASHBOARD

### Pages hiện tại:
1. **Dashboard Monitor** - Real-time metrics, charts
2. **System Operations** - Pipeline control, logs
3. **Content Audit** - Video gallery, review
4. **Database Manager** - Query, export data
5. **Project Info** - Thông tin đồ án

---

## ⚠️ VẤN ĐỀ PHÁT HIỆN

### 1. System Operations Page

#### ✅ Hoạt động tốt:
- Buttons "🔄 Refresh Data", "🌐 Airflow UI", "📦 MinIO Console" hoạt động OK
- Pipeline status cards hiển thị đúng
- Pause/Unpause buttons hoạt động đúng

#### ⚠️ Cần cải thiện:

**1.1. Button "🗑️ Clear Queued"**
- **Vấn đề:** Không có confirmation dialog trước khi xóa
- **Impact:** Người dùng có thể vô tình xóa nhầm queued runs
- **Gợi ý:** Thêm confirmation dialog hoặc checkbox "I'm sure"

**1.2. Trigger DAG Buttons**
- **Vấn đề:** Sau khi click "🚀 KÍCH HOẠT CRAWLER" hoặc "⚡ KÍCH HOẠT STREAMING", không có feedback rõ ràng về status
- **Impact:** Không biết DAG đã trigger thành công hay chưa (chỉ có toast message)
- **Gợi ý:** Thêm loading spinner kéo dài, hoặc redirect đến Airflow UI

**1.3. Log Display**
- **Vấn đề:** Logs hiển thị trong textarea, khó scroll và search
- **Impact:** Khó debug khi logs dài
- **Gợi ý:** Dùng st.code() với syntax highlighting, hoặc tải log ra file

**1.4. DAG Status Update**
- **Vấn đề:** Status không tự động update sau khi trigger/pause
- **Impact:** Phải refresh page để thấy status mới
- **Gợi ý:** Auto-refresh status sau 5-10 giây, hoặc st.rerun() sau action

---

### 2. Content Audit Page

#### ✅ Hoạt động tốt:
- Pagination buttons (Previous/Next) hoạt động OK
- Video cards hiển thị đúng
- Expandable video details hoạt động OK

#### ⚠️ Cần cải thiện:

**2.1. Pagination Buttons**
- **Vấn đề:** Disabled buttons vẫn hiển thị (không có visual feedback rõ ràng)
- **Impact:** Không biết tại sao button bị disabled
- **Gợi ý:** Hide button hoặc thêm tooltip "First page" / "Last page"

**2.2. Video Player**
- **Vấn đề:** Video URL có thể không load được (MinIO permissions)
- **Impact:** Không xem được video
- **Gợi ý:** Thêm error handling, fallback image hoặc "Video unavailable" message

**2.3. Filter/Search**
- **Vấn đề:** Có `category_filter` selectbox nhưng không thấy filter logic rõ ràng
- **Impact:** Filter có thể không hoạt động đúng
- **Gợi ý:** Thêm search box, date range filter, score range filter

**2.4. Video Details**
- **Vấn đề:** Expandable details chỉ hiện text, không có visualization (charts, metrics trends)
- **Impact:** Khó phân tích chi tiết video
- **Gợi ý:** Thêm charts (text score vs video score), timeline, metadata

---

### 3. Dashboard Monitor Page

#### ⚠️ Cần kiểm tra:

**3.1. Auto-refresh**
- **Vấn đề:** Có auto-refresh nhưng refresh interval cố định
- **Impact:** Không thể adjust refresh rate
- **Gợi ý:** Thêm slider để adjust refresh interval (5s, 10s, 30s, 60s)

**3.2. Charts**
- **Vấn đề:** Chưa thấy code charts (cần kiểm tra dashboard_monitor.py)
- **Impact:** Không biết charts hiển thị như thế nào
- **Gợi ý:** Kiểm tra xem có confusion matrix, time series charts không

---

### 4. Database Manager Page

#### ✅ Hoạt động tốt:
- Query interface hoạt động OK
- Export buttons hoạt động OK

#### ⚠️ Cần cải thiện:

**4.1. SQL Editor**
- **Vấn đề:** Textarea không có syntax highlighting cho SQL
- **Impact:** Khó viết và debug SQL queries
- **Gợi ý:** Dùng st.code() hoặc third-party SQL editor component

**4.2. Query Results**
- **Vấn đề:** Results hiển thị trong st.dataframe, khó filter/sort
- **Impact:** Khó phân tích data
- **Gợi ý:** Dùng st.data_editor() với filtering, hoặc export ra CSV để phân tích

**4.3. Table Selection**
- **Vấn đề:** Selectbox "Select Table" - không biết table nào có gì
- **Impact:** Phải biết trước tên table
- **Gợi ý:** Thêm tooltip/show schema khi hover, hoặc "Show Tables" button

---

### 5. General UI/UX Issues

#### ⚠️ Cần cải thiện:

**5.1. Navigation**
- **Vấn đề:** Sidebar navigation OK nhưng không có breadcrumbs hoặc "Home" button
- **Impact:** Khó biết đang ở page nào (nhưng có sidebar highlight nên OK)
- **Gợi ý:** OK, không cần sửa

**5.2. Error Messages**
- **Vấn đề:** Error messages có thể không user-friendly (technical errors)
- **Impact:** Khó hiểu lỗi gì
- **Gợi ý:** Thêm error codes, suggestions, hoặc "Help" link

**5.3. Loading States**
- **Vấn đề:** Một số actions không có loading spinner rõ ràng
- **Impact:** Không biết action đang chạy hay đã fail
- **Gợi ý:** Thêm st.spinner() cho tất cả async operations

**5.4. Toast Messages**
- **Vấn đề:** Toast messages có thể quá nhanh, khó đọc
- **Impact:** Missed feedback
- **Gợi ý:** Tăng duration, hoặc thêm persistent success/error messages

**5.5. Responsive Design**
- **Vấn đề:** Chưa test trên mobile/tablet
- **Impact:** Có thể không responsive
- **Gợi ý:** Test responsive, adjust column widths

---

## 📊 PRIORITY RANKING

### 🔴 HIGH PRIORITY (Ảnh hưởng chức năng):

1. **Error handling** - Video player, query results (Nếu fail thì user không dùng được)
2. **Loading states** - Trigger DAG, export data (Không biết action đã chạy chưa)
3. **Status update** - DAG status không tự động update (Phải refresh thủ công)

### 🟡 MEDIUM PRIORITY (Cải thiện UX):

4. **Confirmation dialogs** - Clear queued runs (Có thể xóa nhầm)
5. **Filters/Search** - Content audit page (Khó tìm video)
6. **Visual feedback** - Disabled buttons, tooltips (Không rõ tại sao disabled)

### 🟢 LOW PRIORITY (Nice to have):

7. **SQL syntax highlighting** - Database manager
8. **Charts visualization** - Video details, dashboard monitor
9. **Responsive design** - Mobile/tablet support

---

## ✅ RECOMMENDATIONS

### Quick Wins (Dễ fix):

1. ✅ Thêm confirmation dialog cho "Clear Queued"
2. ✅ Thêm loading spinner cho trigger DAG buttons
3. ✅ Auto-refresh status sau action (st.rerun() sau 2-3 giây)
4. ✅ Thêm tooltips cho disabled buttons
5. ✅ Thêm error handling cho video player (try-except)

### Medium Effort:

6. ✅ Thêm search/filter trong Content Audit
7. ✅ Cải thiện log display (st.code() thay vì textarea)
8. ✅ Thêm charts vào video details

### Long-term:

9. ✅ SQL editor với syntax highlighting
10. ✅ Responsive design testing
11. ✅ User preferences (refresh interval, theme)

---

## 📝 TÓM TẮT

### Tổng số issues: **~15 issues**

- 🔴 **High priority:** 3 issues
- 🟡 **Medium priority:** 3 issues  
- 🟢 **Low priority:** 9 issues

### Dashboard overall: ✅ **GOOD** (7/10)

- ✅ Navigation OK
- ✅ Basic functionality works
- ✅ Buttons responsive
- ⚠️ Cần cải thiện error handling, loading states, filters

---

**Bạn có thể review và confirm các issues này, sau đó tôi sẽ fix theo priority.**
