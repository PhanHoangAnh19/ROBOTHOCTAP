# web-service/ — Nhóm Web & Service

**Thành viên:** Phan Quang Hoàng Anh · Nguyễn Thị Cẩm Nguyên
**Nhánh:** `web-service`

Dashboard giáo viên / phụ huynh: **Vue 3 + Vite + TypeScript + Tailwind CSS 4 + Chart.js**.

## Chạy

Cần **Node.js 20+**.

```powershell
# 1. Chạy backend trước (xem ../be/README.md) — mặc định http://127.0.0.1:8000
# 2. Chạy web
cd web-service
npm install        # lần đầu
npm run dev
```

Mở **http://localhost:5173**. Vite tự chuyển `/events`, `/sensor-event`, `/ask-ai` sang backend
(đổi địa chỉ backend: `$env:VITE_API_URL="http://..."` trước khi `npm run dev`).

Không chạy backend vẫn xem được giao diện — web tự chuyển sang **dữ liệu mẫu** (góc dưới menu ghi "Chưa kết nối backend").

| Lệnh | Tác dụng |
|---|---|
| `npm run dev` | Chạy web để phát triển (tự tải lại khi sửa code) |
| `npm run typecheck` | Kiểm tra lỗi TypeScript |
| `npm run build` | Build bản production vào `dist/` |

## Các trang

| Đường dẫn | Trang | Nội dung |
|---|---|---|
| `/` | Tổng quan lớp | 4 thẻ thống kê, bảng học sinh, **biểu đồ cột thời lượng học + biểu đồ đường tần suất nhắc** 7 ngày, nạp bài học, câu hỏi hay gặp |
| `/hoc-sinh` | Học sinh | Danh sách, tìm kiếm |
| `/hoc-sinh/:id` | Chi tiết học sinh | Thống kê **theo ngày / theo tuần**, danh sách **phiên học**, **timeline sự kiện** từng phiên |
| `/bai-hoc` | Nội dung bài học | Danh sách bài đã nạp |
| `/bai-tap` | Bài tập | Tình trạng làm bài |

Nút **Nạp bài học** mở hộp thoại gửi bài (môn, tóm tắt, ý chính, câu hỏi ôn) cho cả lớp.

## Dữ liệu thật và dữ liệu mẫu

| Dữ liệu | Nguồn hiện tại | Cần API từ nhóm BE |
|---|---|---|
| Sự kiện tư thế / tập trung / hỏi AI | **Thật** — `GET /events` (tự làm mới 5 giây), gắn cho học sinh **Ben** | Thêm `student_id` / `device_id` vào sự kiện |
| Thống kê ngày / tuần, phiên học | Web tự tính từ sự kiện (phiên mới khi 2 sự kiện cách nhau > 30 phút) | API thống kê & phiên học (backend hiện chỉ trả 50 sự kiện gần nhất) |
| Học sinh, lớp, nhóm, tâm trạng, bài tập | Mẫu — `src/data/mock.ts` | API học sinh / lớp / bài tập |
| Bài học đã nạp | Lưu trên trình duyệt (localStorage) | API bài học |

Khi BE có API: chỉ cần thay hàm trong `src/data/mock.ts`, `src/utils/stats.ts`, `src/stores/robot.ts` — giao diện giữ nguyên.

**Riêng tư:** web không đọc, không lưu nội dung ảnh/slide — kéo thả file chỉ lấy **tên file**.

## Cấu trúc

```
src/
├── api/events.ts          # Gọi backend, kiểu dữ liệu sự kiện
├── data/mock.ts           # Dữ liệu mẫu (học sinh, lớp, nhóm...)
├── stores/                # robot.ts (sự kiện + bài học), ui.ts (hộp thoại, menu)
├── utils/stats.ts         # Gom thống kê ngày/tuần, chia phiên học
├── layouts/AppLayout.vue  # Menu bên + khung trang
├── components/            # Bảng học sinh, thẻ thống kê, hộp thoại nạp bài, timeline, biểu đồ
└── views/                 # Các trang
```
