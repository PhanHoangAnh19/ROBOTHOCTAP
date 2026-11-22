import cv2
import time
import numpy as np

class PageStabilityDetector:
    """
    Thuật toán phát hiện trang sách/vở đã ổn định (Task 3 - Tuần 4):
    1. Ổn định vị trí: 4 góc không bị xê dịch rung lắc (jitter < threshold).
    2. Không bị che: Không có bàn tay bé che đè lên nội dung trang vở (> 12% diện tích da).
    3. Thời gian ổn định: Duy trì cả 2 điều kiện trên liên tục >= 1.0 giây.
    """
    def __init__(self, required_duration=1.0, movement_threshold=8.0, max_hand_coverage=0.12):
        self.required_duration = required_duration
        self.movement_threshold = movement_threshold
        self.max_hand_coverage = max_hand_coverage

        self.last_corners = None
        self.stable_start_time = None
        self.is_stable = False

    def detect_skin_coverage(self, warped_page):
        """
        Phát hiện tỷ lệ vùng da tay trên bề mặt trang vở đã cắt (Deskewed).
        Sử dụng không gian màu HSV chuẩn cho da người Châu Á / Việt Nam.
        """
        if warped_page is None or warped_page.size == 0:
            return 0.0

        hsv = cv2.cvtColor(warped_page, cv2.COLOR_BGR2HSV)
        # Dải màu da: H: 0-25, S: 30-180, V: 60-255
        lower_skin = np.array([0, 30, 60], dtype=np.uint8)
        upper_skin = np.array([25, 180, 255], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_pixels = cv2.countNonZero(mask)
        total_pixels = warped_page.shape[0] * warped_page.shape[1]

        if total_pixels == 0:
            return 0.0

        return float(skin_pixels / total_pixels)

    def check_stability(self, current_corners, warped_page):
        """
        Kiểm tra độ ổn định theo từng khung hình.
        Trả về dict trạng thái:
        - is_stable (bool): True khi sẵn sàng kích hoạt chụp gửi LLM
        - progress (float): Tiến trình giữ yên (0.0 -> 1.0)
        - movement (float): Độ dịch chuyển của 4 góc
        - skin_coverage (float): Tỷ lệ tay che trang vở
        - status_msg (str): Mô tả trực quan hiển thị lên màn hình
        """
        now = time.time()

        if current_corners is None or warped_page is None:
            self.stable_start_time = None
            self.last_corners = None
            self.is_stable = False
            return {
                "is_stable": False,
                "progress": 0.0,
                "movement": 99.0,
                "skin_coverage": 0.0,
                "status_msg": "Chua phat hien trang sach/vo"
            }

        # 1. Đo độ dịch chuyển so với frame trước
        movement = 0.0
        if self.last_corners is not None:
            # Khoảng cách Euclidean trung bình của 4 đỉnh
            diff = np.linalg.norm(current_corners - self.last_corners, axis=1)
            movement = float(np.mean(diff))

        self.last_corners = current_corners.copy()

        # 2. Kiểm tra tay che
        skin_coverage = self.detect_skin_coverage(warped_page)
        hand_occluded = skin_coverage > self.max_hand_coverage

        # 3. Đánh giá tính ổn định
        is_moving = movement > self.movement_threshold

        if is_moving or hand_occluded:
            # Nếu đang rung lắc hoặc tay còn đang giữ vở -> reset thời gian
            self.stable_start_time = None
            self.is_stable = False
            reason = "Dang di chuyen / rung tay" if is_moving else f"Tay che trang vo ({skin_coverage*100:.1f}%)"
            return {
                "is_stable": False,
                "progress": 0.0,
                "movement": movement,
                "skin_coverage": skin_coverage,
                "status_msg": f"Cho on dinh: {reason}"
            }

        # Nếu vị trí đứng yên và không bị tay che
        if self.stable_start_time is None:
            self.stable_start_time = now

        elapsed = now - self.stable_start_time
        progress = min(1.0, elapsed / self.required_duration)

        if elapsed >= self.required_duration:
            self.is_stable = True
            msg = "TRANG ON DINH - SAN SANG CHUP!"
        else:
            self.is_stable = False
            msg = f"Dang giu yen... ({int(progress * 100)}%)"

        return {
            "is_stable": self.is_stable,
            "progress": progress,
            "movement": movement,
            "skin_coverage": skin_coverage,
            "status_msg": msg
        }
