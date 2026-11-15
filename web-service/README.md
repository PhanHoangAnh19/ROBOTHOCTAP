# web-service/ — Nhóm Web & Service

**Thành viên:** Phan Quang Hoàng Anh · Nguyễn Thị Cẩm Nguyên
**Nhánh:** `web-service`

## Nhiệm vụ chính (theo timeline 8 tuần)
- Dashboard phụ huynh: sự kiện tư thế/tập trung realtime, status indicators
- Biểu đồ: thời lượng học, tần suất nhắc, lịch sử bài; trang chi tiết phiên học
- Hiển thị log phản hồi LLM & chi phí token
- Form đăng nhập/đăng ký, route guard theo role (phụ huynh/giáo viên)
- Responsive mobile/tablet, cross-browser; user guide & slide demo

## Chạy
1. Chạy backend trước (xem [be/README.md](../be/README.md)) — mặc định ở `http://127.0.0.1:8000`.
2. Mở `dashboard.html` bằng Chrome/Edge (nhấp đúp file).

Đổi địa chỉ backend: sửa `API_BASE_URL` trong `dashboard.html`.

## File
| File | Mô tả |
|---|---|
| `dashboard.html` | Dashboard: bảng sự kiện, thống kê, hỏi AI theo 3 chế độ |
| `axios.min.js` | Bản axios tối giản (dựa trên `fetch`) dùng cho dashboard |
