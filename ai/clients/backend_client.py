import requests
import time

class BackendEventPublisher:
    """
    Client bắn tín hiệu sự kiện từ AI Edge sang Backend FastAPI của nhóm BE.
    Backend URL: http://127.0.0.1:8000/sensor-event
    Tuân thủ Luật bảo vệ dữ liệu trẻ em 2026: 0 byte ảnh gửi đi (chỉ gửi JSON thông số).
    """
    def __init__(self, backend_url="http://127.0.0.1:8000/sensor-event"):
        self.backend_url = backend_url
        self.last_sent_time = 0
        self.send_cooldown = 3.0

    def send_posture_alert(self, reasons: list, bad_duration: float, angles: dict):
        now = time.time()
        if now - self.last_sent_time < self.send_cooldown:
            return False

        neck_angle = angles.get("neck", 0.0)
        shoulder_angle = angles.get("shoulder", 0.0)
        
        event_type = "TU_THE_CO"
        if "Lệch vai" in " ".join(reasons):
            event_type = "TU_THE_VAI"

        detail_msg = f"[MediaPipe AI] {', '.join(reasons)} liên tục {bad_duration:.1f}s (Cổ: {neck_angle:.1f}°, Vai: {shoulder_angle:.1f}°)"

        payload = {
            "event_type": event_type,
            "detail": detail_msg
        }

        try:
            res = requests.post(self.backend_url, json=payload, timeout=0.5)
            self.last_sent_time = now
            return res.status_code == 200
        except Exception:
            return False

    def send_attention_alert(self, state: str, detail_msg: str):
        now = time.time()
        if now - self.last_sent_time < self.send_cooldown:
            return False

        payload = {
            "event_type": "MAT_TAP_TRUNG",
            "detail": f"[MediaPipe AI] {detail_msg}"
        }

        try:
            res = requests.post(self.backend_url, json=payload, timeout=0.5)
            self.last_sent_time = now
            return res.status_code == 200
        except Exception:
            return False
