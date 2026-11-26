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
| `/ai-chi-phi` | AI & Chi phí (tuần 5) | **Phản hồi LLM** (lọc theo chế độ / trạng thái offline, tìm kiếm), **biểu đồ token & chi phí** theo ngày, **độ trễ trung vị so với Q8 ≤ 8s**, đơn giá chỉnh được, lịch sử bài học |

Nút **Nạp bài học** mở hộp thoại gửi bài (môn, tóm tắt, ý chính, câu hỏi ôn) cho cả lớp.

## Dữ liệu thật và dữ liệu mẫu

| Dữ liệu | Nguồn hiện tại | Cần API từ nhóm BE |
|---|---|---|
| Sự kiện tư thế / tập trung / hỏi AI | **Thật** — `GET /events` (tự làm mới 5 giây), gắn cho học sinh **Ben** | Thêm `student_id` / `device_id` vào sự kiện |
| Thống kê ngày / tuần, phiên học | Web tự tính từ sự kiện (phiên mới khi 2 sự kiện cách nhau > 30 phút) | API thống kê & phiên học (backend hiện chỉ trả 50 sự kiện gần nhất) |
| Học sinh, lớp, nhóm, tâm trạng, bài tập | Mẫu — `src/data/mock.ts` | API học sinh / lớp / bài tập |
| Bài học đã nạp | Lưu trên trình duyệt (localStorage) | API bài học |
| Log LLM: câu hỏi / câu trả lời | **Thật** — sự kiện `GIAI_TOAN` / `DAY_HOC` / `THAC_MAC` trong `GET /events` | `GET /llm-logs` (bên dưới) |
| Token, độ trễ, chi phí LLM | Token **ước tính** (1 từ ≈ 1.6 token, giống `ai/prompts/llm_socratic.py`); chưa có độ trễ | `GET /llm-logs` (task 5 tuần 5 của BE) |

Khi BE có API: chỉ cần thay hàm trong `src/data/mock.ts`, `src/utils/stats.ts`, `src/stores/robot.ts` — giao diện giữ nguyên.

### Hợp đồng API đề xuất cho nhóm BE: `GET /llm-logs`

Trang `/ai-chi-phi` tự gọi API này trước; nếu chưa có (404) thì dùng `/events`, backend tắt thì dùng dữ liệu mẫu.
Sau khi có đăng nhập (tuần 6) có thể chuyển sang `/api/v1/llm-logs` + JWT.

```json
{
  "logs": [
    {
      "id": 12,
      "timestamp": "2026-11-26 17:04:10",
      "mode": "GIAI_TOAN",
      "question": "3/4 + 1/2 bằng bao nhiêu?",
      "answer": "Con thử quy đồng mẫu số trước nhé!",
      "status": "ok",
      "provider": "Gemini",
      "model": "gemini-2.0-flash",
      "input_tokens": 135,
      "output_tokens": 42,
      "image_tokens": 0,
      "latency_ms": 2310,
      "cost_usd": null
    }
  ]
}
```

- `status`: `ok` | `offline` | `error`. `latency_ms` = từ lúc nhận câu hỏi tới lúc có câu trả lời (đo Q8).
- Token lấy từ `usage` mà LLM trả về (`ai_client.py` đang log sẵn, chỉ cần lưu vào DB).
- `cost_usd` để `null` thì web tự tính theo đơn giá nhập trên trang. **Không** trả ảnh hay base64.

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
