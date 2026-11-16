import time

class PostureDebounceTracker:
    """
    Bộ đếm lọc nhiễu thời gian cho tư thế ngồi (Debounce & Cooldown):
    - bad_duration_threshold: Tư thế xấu phải duy trì liên tục >= 10s mới phát cảnh báo (tránh báo ảo khi cúi nhặt bút).
    - cooldown_seconds: Khoảng cách giãn cách giữa 2 lần nhắc (mặc định 120s = 2 phút) để không làm phiền bé.
    """
    def __init__(self, bad_duration_threshold=10.0, cooldown_seconds=120.0):
        self.bad_threshold = bad_duration_threshold
        self.cooldown = cooldown_seconds
        
        self.bad_start_time = None
        self.last_alert_time = 0
        self.current_state = "GOOD"
        
    def update(self, is_bad_posture: bool, bad_reasons: list):
        now = time.time()
        
        # Nếu tư thế tốt -> reset thời gian bắt đầu xấu
        if not is_bad_posture:
            self.bad_start_time = None
            self.current_state = "GOOD"
            return {
                "alert": False,
                "state": self.current_state,
                "bad_duration": 0.0,
                "cooldown_remaining": max(0.0, self.cooldown - (now - self.last_alert_time))
            }
            
        # Nếu bắt đầu sai tư thế
        if self.bad_start_time is None:
            self.bad_start_time = now
            
        bad_duration = now - self.bad_start_time
        can_alert = (now - self.last_alert_time) >= self.cooldown
        
        if bad_duration >= self.bad_threshold:
            if can_alert:
                self.last_alert_time = now
                self.current_state = "ALERT_TRIGGERED"
                return {
                    "alert": True,
                    "state": self.current_state,
                    "bad_duration": bad_duration,
                    "reasons": bad_reasons,
                    "message": "Bé ơi, ngồi thẳng lưng và nâng cằm lên một chút nào!"
                }
            else:
                self.current_state = "COOLDOWN_ACTIVE"
        else:
            self.current_state = "WARNING_PENDING"
            
        return {
            "alert": False,
            "state": self.current_state,
            "bad_duration": bad_duration,
            "cooldown_remaining": max(0.0, self.cooldown - (now - self.last_alert_time))
        }
