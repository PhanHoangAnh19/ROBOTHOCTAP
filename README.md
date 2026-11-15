# ROBOT HỌC TẬP — Robot trợ lý học tập AI cho trẻ 6–12 tuổi (POC)

Team 7 thành viên, chia 3 nhóm, phát triển trong 8 tuần (26/10 – 20/12/2026).

## Cấu trúc thư mục

```
ROBOTHOCTAP/
├── be/            # Nhóm BE — FastAPI + SQLite, API sự kiện, LLM client
├── ai/            # Nhóm Training AI — camera, tư thế, tập trung, prompt
└── web-service/   # Nhóm Web & Service — Dashboard phụ huynh
```

| Thư mục | Nhóm | Thành viên | Nhánh làm việc |
|---|---|---|---|
| [`be/`](be/) | BE (Backend) | Phạm Trần Khánh Linh · Dương Thành Long · Trần Đặng Như Quỳnh | `be` |
| [`ai/`](ai/) | Training AI | Phan Hà Minh Phúc · Nguyễn Văn Quốc | `ai` |
| [`web-service/`](web-service/) | Web & Service | Phan Quang Hoàng Anh · Nguyễn Thị Cẩm Nguyên | `web-service` |

## Quy trình làm việc với Git

```
master  ← nhánh chính, chỉ nhận code qua Pull Request
 ├── be
 ├── ai
 └── web-service
```

1. **Lấy code về & chuyển sang nhánh của nhóm mình**
   ```
   git clone https://github.com/PhanHoangAnh19/ROBOTHOCTAP
   cd ROBOTHOCTAP
   git checkout be          # hoặc: ai / web-service
   ```
2. **Trước khi làm, cập nhật code mới nhất từ master**
   ```
   git pull origin master
   ```
3. **Làm việc trong thư mục của nhóm mình**, commit và push lên nhánh nhóm
   ```
   git add .
   git commit -m "feat: mô tả ngắn"
   git push origin be       # đúng tên nhánh nhóm mình
   ```
4. **Khi xong một phần việc** → lên GitHub tạo **Pull Request** từ nhánh nhóm vào `master`, nhờ 1 người nhóm khác review rồi merge.

### Quy ước
- Không push thẳng lên `master`.
- Chỉ sửa file trong thư mục của nhóm mình; cần sửa thư mục nhóm khác thì báo nhóm đó.
- Commit message: `feat:` (tính năng mới), `fix:` (sửa lỗi), `docs:` (tài liệu), `refactor:`, `test:`.
- **Không commit API key, file `.env`, ảnh/video, file `.db`** (đã có trong `.gitignore`). Luật bảo vệ dữ liệu cá nhân: 0 ảnh trẻ em trên git.

## Chạy thử toàn hệ thống trên laptop

| Bước | Lệnh | Xem chi tiết |
|---|---|---|
| 1. Backend | `cd be` → `python -m uvicorn backend_api:app --port 8000` | [be/README.md](be/README.md) |
| 2. Dashboard | Mở `web-service/dashboard.html` bằng Chrome/Edge | [web-service/README.md](web-service/README.md) |
| 3. Camera tư thế | `cd ai` → `python test_cam_laptop.py` | [ai/README.md](ai/README.md) |
