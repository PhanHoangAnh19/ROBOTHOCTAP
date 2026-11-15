import cv2
import time
import requests

BACKEND_URL = "http://127.0.0.1:8000/sensor-event"

cap = cv2.VideoCapture(0)
last_alert_time = 0
ALERT_COOLDOWN = 5  # Gửi cảnh báo mỗi 5 giây nếu vẫn sai tư thế

# Lưu khung hình nền để phát hiện chuyển động và vị trí ngồi
ret, first_frame = cap.read()
if ret:
    first_frame = cv2.flip(first_frame, 1)
    first_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    first_gray = cv2.GaussianBlur(first_gray, (21, 21), 0)

def send_alert_to_backend(event_type, detail_msg):
    global last_alert_time
    current_time = time.time()
    if current_time - last_alert_time > ALERT_COOLDOWN:
        try:
            requests.post(BACKEND_URL, json={"event_type": event_type, "detail": detail_msg}, timeout=2)
            print(f"[ĐÃ GỬI DASHBOARD] {detail_msg}")
            last_alert_time = current_time
        except Exception as e:
            print("Lỗi kết nối Backend:", e)

print("Đang mở Webcam Laptop (Chế độ Offline)... Nhấn phím 'Q' trên cửa sổ camera để thoát.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Không mở được Webcam! Hãy kiểm tra quyền truy cập camera trên Windows.")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # So sánh khung hình hiện tại với khung hình nền để tìm vùng cơ thể người ngồi
    diff = cv2.absdiff(first_gray, gray)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Cập nhật khung hình nền từ từ để thích nghi ánh sáng
    first_gray = cv2.addWeighted(first_gray, 0.95, gray, 0.05, 0)

    status_text = "Tu the chuan"
    status_color = (0, 255, 0)  # Xanh lá

    # Lọc các vùng chuyển động đủ lớn (tương ứng cơ thể người)
    large_contours = [c for c in contours if cv2.contourArea(c) > 4000]

    if len(large_contours) > 0:
        largest = max(large_contours, key=cv2.contourArea)
        (x, y, bw, bh) = cv2.boundingRect(largest)
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (255, 200, 0), 2)

        center_x = x + bw // 2
        top_y = y

        # 1. Kiểm tra cúi sát màn hình (Vùng cơ thể chiếm quá 65% chiều rộng màn hình)
        if bw > w * 0.65:
            status_text = "CANH BAO: Cui qua sat man hinh / ban!"
            status_color = (0, 0, 255)
            send_alert_to_backend("KHOANG_CACH_MAT", "[Webcam Laptop] Ngồi quá gần màn hình (Dưới 25cm)")

        # 2. Kiểm tra gập cổ cúi đầu xuống thấp (Đỉnh đầu tụt xuống quá nửa màn hình)
        elif top_y > h * 0.55:
            status_text = "CANH BAO: Gap co / Cui dau qua thap!"
            status_color = (0, 0, 255)
            send_alert_to_backend("TU_THE_CO", "[Webcam Laptop] Phát hiện gập cổ cúi đầu xuống thấp")

        # 3. Kiểm tra nghiêng người / lệch trục vai sang trái hoặc phải
        elif center_x < w * 0.25 or center_x > w * 0.75:
            status_text = "CANH BAO: Ngoi lech / Nghieng vai!"
            status_color = (0, 140, 255)
            send_alert_to_backend("TU_THE_VAI", "[Webcam Laptop] Tư thế ngồi lệch trục sang một bên")

    else:
        # Không có chuyển động/người ngồi trước webcam
        status_text = "CANH BAO: Mat tap trung / Roi khoi ban!"
        status_color = (0, 165, 255)
        send_alert_to_backend("MAT_TAP_TRUNG", "[Webcam Laptop] Người học rời khỏi vùng quan sát")

    cv2.putText(frame, status_text, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2)
    cv2.imshow("Test Camera AI Tu The - Nhan Q de thoat", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()