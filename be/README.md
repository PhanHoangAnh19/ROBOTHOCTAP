# be/ — Nhóm BE (Backend)

**Thành viên:** Phạm Trần Khánh Linh · Dương Thành Long · Trần Đặng Như Quỳnh
**Nhánh:** `be`

## Nhiệm vụ chính (theo timeline 8 tuần)
- Backend FastAPI + SQLite: lưu sự kiện, timestamp, loại sự kiện
- LLM client: gọi Vision API, timeout/retry, log token & latency
- Bộ máy sự kiện: state machine, debounce, cooldown nhắc nhở ≥ 2 phút
- API phiên học & thống kê; server **reject payload ảnh → HTTP 422**
- Auth JWT, phân quyền phụ huynh/giáo viên; Docker + health check
- Đảm bảo **0 byte ảnh ghi xuống đĩa**

## Chạy
```
cd be
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:GEMINI_API_KEY="key_cua_ban"      # bỏ qua nếu chỉ test offline
.venv\Scripts\python -m uvicorn backend_api:app --port 8000
```
Tài liệu API tự sinh: http://127.0.0.1:8000/docs

## API hiện có
| Method | Đường dẫn | Mô tả |
|---|---|---|
| POST | `/ask-ai` | Hỏi AI: `{"question": "...", "mode": "GIAI_TOAN" \| "DAY_HOC" \| "THAC_MAC"}` |
| POST | `/sensor-event` | Ghi cảnh báo: `{"event_type": "TU_THE_CO" \| "TU_THE_VAI" \| "KHOANG_CACH_MAT" \| "MAT_TAP_TRUNG", "detail": "..."}` |
| GET | `/events` | 50 sự kiện mới nhất + thống kê tổng hợp cho Dashboard |
