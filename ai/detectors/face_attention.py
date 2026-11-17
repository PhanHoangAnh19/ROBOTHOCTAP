import numpy as np

def calculate_ear_single_eye(eye_points):
    """
    Tính Eye Aspect Ratio (EAR) cho 1 bên mắt:
    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    eye_points: danh sách 6 điểm (x, y) viền mắt
    """
    p1, p2, p3, p4, p5, p6 = [np.array(pt) for pt in eye_points]
    vert_1 = np.linalg.norm(p2 - p6)
    vert_2 = np.linalg.norm(p3 - p5)
    horiz = np.linalg.norm(p1 - p4)
    if horiz == 0:
        return 0.0
    return float((vert_1 + vert_2) / (2.0 * horiz))

def estimate_head_pose_yaw_pitch(face_landmarks_2d):
    """
    Ước lượng góc quay đầu (Yaw/Pitch) dựa vào độ lệch sống mũi và 2 bên má.
    Mốc cơ bản: Mũi (1), Mép má trái (234), Mép má phải (454)
    """
    nose = face_landmarks_2d[1]
    left_cheek = face_landmarks_2d[234]
    right_cheek = face_landmarks_2d[454]
    
    dist_left = abs(nose[0] - left_cheek[0])
    dist_right = abs(right_cheek[0] - nose[0])
    total_w = dist_left + dist_right
    if total_w == 0:
        return 0.5, False
        
    yaw_ratio = dist_left / total_w
    # Nếu lệch xa mốc 0.5 (nhìn chính diện) -> Bé đang quay mặt ra hướng khác
    is_looking_away = yaw_ratio < 0.28 or yaw_ratio > 0.72
    return float(yaw_ratio), is_looking_away
