import math
import numpy as np

def calculate_angle_2d(p1, p2, p3):
    """
    Tính góc tạo bởi 3 điểm p1 - p2 - p3 (đỉnh tại p2) trên mặt phẳng 2D.
    p = (x, y). Trả về góc (độ) từ 0 đến 180.
    """
    a = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    b = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    cosine_angle = np.dot(a, b) / (norm_a * norm_b)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine_angle)))

def calculate_shoulder_tilt(left_shoulder, right_shoulder):
    """
    Tính độ nghiêng trục vai (so với phương ngang).
    Nếu lệch > 10 độ -> Cột sống có xu hướng bị vẹo.
    """
    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]
    if dx == 0:
        return 90.0
    angle_rad = math.atan2(abs(dy), abs(dx))
    return float(math.degrees(angle_rad))

def calculate_neck_tilt(ear, shoulder):
    """
    Tính góc gập cổ so với phương thẳng đứng.
    ear: Tọa độ tai phía quan sát rõ hơn
    shoulder: Tọa độ mỏm vai tương ứng
    Nếu góc gập > 25 độ -> Bé đang cúi gục đầu quá sát bàn học.
    """
    dx = ear[0] - shoulder[0]
    dy = ear[1] - shoulder[1]
    return float(math.degrees(math.atan2(abs(dx), abs(dy))))

def calculate_head_desk_proxy(nose, left_shoulder, right_shoulder, frame_h, frame_w):
    """
    Chỉ số Proxy khoảng cách Đầu - Mặt bàn (Task 4 Tuần 2):
    - Khi trẻ cúi sát mặt bàn (< 25cm): 
      + Tọa độ Y của mũi tụt thấp xuống quá 60% chiều cao khung hình (nose_y / frame_h > 0.6)
      + Độ rộng vai chiếm tỷ lệ lớn bất thường do cơ thể áp sát camera.
    Trả về:
    - is_too_close (bool): True nếu cúi quá gần mặt bàn (<25cm)
    - head_drop_ratio (float): Tỷ lệ hạ đầu
    """
    nose_y = nose[1]
    head_drop_ratio = nose_y / float(frame_h) if frame_h > 0 else 0.0
    
    # Khoảng cách 2 vai
    shoulder_w = abs(right_shoulder[0] - left_shoulder[0])
    shoulder_ratio = shoulder_w / float(frame_w) if frame_w > 0 else 0.0
    
    # Cúi quá sát mặt bàn khi đầu chúi xuống quá 60% màn hình hoặc người quá sát
    is_too_close = head_drop_ratio > 0.60 or shoulder_ratio > 0.55
    return is_too_close, float(head_drop_ratio)
