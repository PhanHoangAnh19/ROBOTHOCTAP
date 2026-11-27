# ai/ — Nhóm Training AI

**Thành viên:** Phan Hà Minh Phúc · **Nguyễn Văn Quốc**  
**Nhánh Git:** `ai`

---

## 🏗️ Cấu trúc thư mục module AI

```
ai/
├── models/                     # Chứa các file trọng số mô hình nhẹ cho AI biên
│   ├── pose_landmarker_lite.task   # Google Tasks Pose Model (khung xương tư thế)
│   └── face_landmarker.task        # Google Tasks Face Mesh Model (mắt, miệng, đầu)
│
├── detectors/                  # Module trích xuất đặc trưng & thị giác máy tính
│   ├── posture_math.py         # Tính góc gập cổ (Neck tilt), nghiêng vai và khoảng cách đầu-bàn
│   ├── face_attention.py       # Tính EAR (nhắm mắt ngủ gật) và Yaw/Pitch (quay đầu)
│   ├── page_deskew.py          # Tìm 4 góc và duỗi phẳng (Deskew) trang sách/vở (Quốc)
│   └── page_stability.py       # Kiểm tra trang vở đứng yên, không rung, không tay che (Quốc)
│
├── analyzers/                  # Logic phân tích hành vi & lọc nhiễu thời gian
│   └── posture_tracker.py      # State Machine: Debounce 10s + Cooldown 2 phút chuẩn Q2
│
├── utils/                      # Tiện ích tiền xử lý ảnh & nén dữ liệu
│   └── image_optimizer.py      # Tối ưu kích thước & độ tương phản giảm chi phí token (Phúc)
│
├── clients/                    # Kết nối ngoại vi và truyền dữ liệu
│   └── backend_client.py       # Bắn sự kiện JSON sang Backend FastAPI (POST /sensor-event)
│
├── prompts/                    # Kỹ nghệ Prompt cho trợ lý học tập AI
│   └── llm_socratic.py         # Prompt Socratic hướng dẫn sư phạm tiểu học & 10 kịch bản test
│
├── main_monitor.py             # Ứng dụng chính: Camera HUD realtime giám sát tư thế (Demo M1)
├── test_page_deskew.py         # Script test cắt & duỗi phẳng trang vở qua webcam (Quốc)
├── test_attention.py           # Script test đo nhắm mắt ngủ gật & quay đầu
├── test_image_optimizer.py     # Script test nén ảnh & so sánh token tiêu thụ (Phúc)
├── create_survey_excel.py      # Script tổng hợp bảng số liệu khảo sát góc ngồi (Phúc)
├── requirements.txt            # Danh sách thư viện cần thiết (mediapipe, opencv-python, requests)
├── test_cam_laptop.py          # Script test camera baseline ban đầu
└── test_opencv.py              # Script kiểm tra cài đặt OpenCV
```

---

## 🚀 Hướng dẫn chạy thử nghiệm

### 1. Kích hoạt môi trường ảo
```bash
source venv/bin/activate
# Hoặc cài đặt thư viện cần thiết:
pip install mediapipe opencv-python numpy requests
```

### 2. Chạy ứng dụng Giám sát tư thế (Demo M1)
```bash
# Chạy từ thư mục gốc:
python3 ai/main_monitor.py

# Hoặc vào thư mục ai:
cd ai && python3 main_monitor.py
```
- **Chỉ số trên màn hình:**
  - `FPS`: Tốc độ xử lý khung hình (đã áp dụng bộ lọc mượt mà EMA).
  - `Neck Tilt`: Góc cúi đầu ($> 25^\circ \rightarrow$ cảnh báo gập cổ).
  - `Shoulder Tilt`: Độ lệch trục vai ($> 10^\circ \rightarrow$ cảnh báo vẹo cột sống).
  - `State`: Đếm thời gian ngồi sai liên tục đủ 10 giây sẽ kích hoạt cảnh báo đỏ `CANH BAO: NGOI THANG LUNG!` và bắn sự kiện sang Dashboard.
- Nhấn phím **`q`** để dừng camera.

### 3. Chạy thử nghiệm Prompt Socratic cho bài học
```bash
python3 ai/prompts/llm_socratic.py
```
