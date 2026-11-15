# ai/ — Nhóm Training AI

**Thành viên:** Phan Hà Minh Phúc · Nguyễn Văn Quốc
**Nhánh:** `ai`

## Nhiệm vụ chính (theo timeline 8 tuần)
- MediaPipe Pose / FaceMesh: góc gập cổ, nghiêng vai, khoảng cách đầu–bàn
- Phát hiện tư thế xấu kéo dài (mặc định 10 giây), EAR nhắm mắt, yaw/pitch quay đầu
- Pipeline cắt trang sách/vở (deskew), phát hiện trang ổn định
- **Privacy Gate**: chặn ảnh có mặt/da ≥ 98% trước khi gửi LLM
- Viết & test Prompt cho bài tập tiểu học (giọng gợi mở, Socratic)

## Chạy
```
cd ai
python -m venv .venv
.venv\Scripts\python -m pip install opencv-python numpy requests
.venv\Scripts\python test_cam_laptop.py
```
- Cần chạy **backend** trước (xem [be/README.md](../be/README.md)) để cảnh báo được gửi lên Dashboard.
- Bấm vào cửa sổ camera rồi nhấn **Q** để tắt.
- `requirements.txt` là môi trường đầy đủ của nhóm (có torch, khá nặng) — chỉ cài khi cần train/thử model.

## File
| File | Mô tả |
|---|---|
| `test_cam_laptop.py` | Thử phát hiện tư thế bằng webcam laptop (so khác biệt khung hình), gửi cảnh báo tới `POST /sensor-event` |
| `test_opencv.py` | Kiểm tra OpenCV cài đặt đúng |
