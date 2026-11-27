import os
import time
import requests


class BackendEventPublisher:
    """
    Client bắn tín hiệu sự kiện & đồng bộ ngưỡng cấu hình từ AI Edge sang Backend FastAPI.
    - Endpoint sự kiện: POST http://127.0.0.1:8000/sensor-event
    - Endpoint cấu hình: GET  http://127.0.0.1:8000/api/v1/settings
    Tuân thủ Luật bảo vệ dữ liệu trẻ em 2026 (Q11): 0 byte ảnh gửi qua sensor-event.
    """

    def __init__(
        self,
        backend_url: str = "http://127.0.0.1:8000/sensor-event",
        settings_url: str = "http://127.0.0.1:8000/api/v1/settings",
        send_cooldown: float = 3.0,
    ):
        self.backend_url = backend_url
        self.settings_url = settings_url
        self.send_cooldown = send_cooldown
        # Tách bộ đếm thời gian gửi theo từng khóa sự kiện riêng để Tư thế & Tập trung không chặn nhau
        self.last_sent_by_key: dict[str, float] = {}

    def fetch_settings(
        self,
        default_bad_threshold: float = 10.0,
        default_cooldown: float = 120.0,
        default_debounce: float = 3.0,
    ) -> dict:
        """
        Đọc ngưỡng cảnh báo động từ API /api/v1/settings của nhóm BE (Long).
        Nếu Backend đang offline hoặc chưa cấp token thì dùng giá trị mặc định an toàn.
        """
        defaults = {
            "posture_bad_threshold_seconds": float(default_bad_threshold),
            "reminder_cooldown_seconds": float(default_cooldown),
            "debounce_seconds": float(default_debounce),
            "source": "default_fallback",
        }
        headers = {}
        token = os.environ.get("BACKEND_ACCESS_TOKEN") or os.environ.get("ROBOT_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            res = requests.get(self.settings_url, headers=headers, timeout=0.8)
            if res.status_code == 200:
                body = res.json()
                data = body.get("data", body) if isinstance(body, dict) else {}
                return {
                    "posture_bad_threshold_seconds": float(
                        data.get("posture_bad_threshold_seconds", default_bad_threshold)
                    ),
                    "reminder_cooldown_seconds": float(
                        data.get("reminder_cooldown_seconds", default_cooldown)
                    ),
                    "debounce_seconds": float(
                        data.get("debounce_seconds", default_debounce)
                    ),
                    "source": "backend_api",
                }
        except Exception:
            pass

        return defaults

    def _post_event(self, event_type: str, detail_msg: str, cooldown_key: str = None) -> bool:
        """Gửi 1 sự kiện đơn lẻ sang Backend với bộ chống lặp riêng theo từng loại lỗi."""
        key = cooldown_key or event_type
        now = time.time()
        last_t = self.last_sent_by_key.get(key, 0.0)
        if now - last_t < self.send_cooldown:
            return False

        payload = {
            "event_type": event_type,
            "detail": detail_msg,
        }
        try:
            res = requests.post(self.backend_url, json=payload, timeout=0.5)
            if res.status_code == 200:
                self.last_sent_by_key[key] = now
                return True
        except Exception:
            pass
        return False

    def send_posture_alert(self, reasons: list, bad_duration: float, angles: dict) -> bool:
        """
        Gửi riêng từng loại lỗi tư thế phát hiện được trong lần cảnh báo đó:
          - TU_THE_CO       : Gập cổ > 25°
          - TU_THE_VAI      : Lệch vai > 10°
          - KHOANG_CACH_MAT : Cúi sát bàn < 25cm
        Giúp Dashboard đếm đầy đủ từng lỗi thay vì chỉ ghi đè 1 lỗi.
        """
        neck_angle = angles.get("neck", 0.0)
        shoulder_angle = angles.get("shoulder", 0.0)

        events_to_send = []
        for r in reasons:
            r_lower = r.lower()
            if "gap co" in r_lower or "gập cổ" in r_lower:
                events_to_send.append((
                    "TU_THE_CO",
                    f"[MediaPipe AI] {r} liên tục {bad_duration:.1f}s (Cổ: {neck_angle:.1f}°, Vai: {shoulder_angle:.1f}°)"
                ))
            elif "lech vai" in r_lower or "lệch vai" in r_lower:
                events_to_send.append((
                    "TU_THE_VAI",
                    f"[MediaPipe AI] {r} liên tục {bad_duration:.1f}s (Vai: {shoulder_angle:.1f}°, Cổ: {neck_angle:.1f}°)"
                ))
            elif "cui" in r_lower or "cúi" in r_lower or "sat ban" in r_lower:
                events_to_send.append((
                    "KHOANG_CACH_MAT",
                    f"[MediaPipe AI] {r} liên tục {bad_duration:.1f}s (Khoảng cách mắt - bàn < 25cm)"
                ))

        # Fallback nếu danh sách lý do tùy chỉnh không khớp từ khóa trên
        if not events_to_send and reasons:
            events_to_send.append((
                "TU_THE_CO",
                f"[MediaPipe AI] {', '.join(reasons)} liên tục {bad_duration:.1f}s (Cổ: {neck_angle:.1f}°, Vai: {shoulder_angle:.1f}°)"
            ))

        any_sent = False
        for ev_type, detail_msg in events_to_send:
            if self._post_event(ev_type, detail_msg, cooldown_key=f"POSTURE:{ev_type}"):
                any_sent = True
        return any_sent

    def send_attention_alert(self, state: str, detail_msg: str) -> bool:
        """
        Gửi cảnh báo mất tập trung (DROWSY / DISTRACTED) với khóa cooldown riêng biệt,
        không bị xung đột với cảnh báo tư thế ngồi.
        """
        return self._post_event(
            event_type="MAT_TAP_TRUNG",
            detail_msg=f"[MediaPipe AI] [{state}] {detail_msg}",
            cooldown_key=f"ATTENTION:{state}",
        )
