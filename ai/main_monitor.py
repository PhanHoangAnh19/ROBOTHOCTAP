import os
import sys
import cv2
import time
import numpy as np

# Cho phép chạy file trực tiếp hoặc import từ module cha
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Import linh hoạt theo package mới hoặc thư mục hiện tại
try:
    from ai.detectors.posture_math import calculate_shoulder_tilt, calculate_neck_tilt
    from ai.analyzers.posture_tracker import PostureDebounceTracker
    from ai.clients.backend_client import BackendEventPublisher
except ImportError:
    try:
        from detectors.posture_math import calculate_shoulder_tilt, calculate_neck_tilt
        from analyzers.posture_tracker import PostureDebounceTracker
        from clients.backend_client import BackendEventPublisher
    except ImportError:
        from posture_math import calculate_shoulder_tilt, calculate_neck_tilt
        from posture_tracker import PostureDebounceTracker
        from backend_client import BackendEventPublisher

def run_posture_monitor():
    print("="*60)
    print("🚀 TEAM TRAINING AI (QUỐC & PHÚC) - POSTURE MONITOR v1.0")
    print("Mục tiêu Tuần 1-2-3: MediaPipe Pose + Debounce 10s + Gửi API sang Backend")
    print("="*60)

    # Tìm đường dẫn model trong models/ hoặc thư mục hiện tại
    model_candidates = [
        os.path.join(CURRENT_DIR, "models", "pose_landmarker_lite.task"),
        os.path.join(CURRENT_DIR, "pose_landmarker_lite.task"),
        os.path.join(PROJECT_ROOT, "pose_landmarker_lite.task")
    ]
    model_path = next((p for p in model_candidates if os.path.exists(p)), None)
    if not model_path:
        print(f"❌ Không tìm thấy model pose_landmarker_lite.task trong các thư mục!")
        return

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        num_poses=1
    )
    detector = vision.PoseLandmarker.create_from_options(options)
    tracker = PostureDebounceTracker(bad_duration_threshold=10.0, cooldown_seconds=120.0)
    publisher = BackendEventPublisher()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Không mở được webcam mặc định (0). Vui lòng kiểm tra quyền truy cập camera!")
        return

    prev_time = time.time()
    smoothed_fps = 0.0
    print("✅ Đã kết nối Camera thành công. Nhấn 'q' để dừng.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        h, w, _ = frame.shape
        curr_time = time.time()
        delta_t = curr_time - prev_time
        prev_time = curr_time

        # Bộ lọc làm mượt FPS (EMA) để không bị giật số
        if delta_t > 0:
            instant_fps = 1.0 / delta_t
            smoothed_fps = instant_fps if smoothed_fps == 0.0 else (0.85 * smoothed_fps + 0.15 * instant_fps)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = detector.detect(mp_image)

        is_bad = False
        reasons = []
        neck_angle = 0.0
        shoulder_angle = 0.0

        if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
            landmarks = detection_result.pose_landmarks[0]
            
            # MediaPipe Pose Landmark:
            # 0: Mũi, 7: Tai trái, 8: Tai phải, 11: Vai trái, 12: Vai phải
            nose = (int(landmarks[0].x * w), int(landmarks[0].y * h))
            left_ear = (int(landmarks[7].x * w), int(landmarks[7].y * h))
            right_ear = (int(landmarks[8].x * w), int(landmarks[8].y * h))
            left_shoulder = (int(landmarks[11].x * w), int(landmarks[11].y * h))
            right_shoulder = (int(landmarks[12].x * w), int(landmarks[12].y * h))

            # Chọn bên nhìn rõ hơn (tai có visibility cao hơn)
            chosen_ear = left_ear if landmarks[7].visibility >= landmarks[8].visibility else right_ear
            chosen_shoulder = left_shoulder if landmarks[7].visibility >= landmarks[8].visibility else right_shoulder

            neck_angle = calculate_neck_tilt(chosen_ear, chosen_shoulder)
            shoulder_angle = calculate_shoulder_tilt(left_shoulder, right_shoulder)

            # Đánh giá theo chuẩn: gập cổ > 25 độ, lệch vai > 10 độ
            if neck_angle > 25.0:
                is_bad = True
                reasons.append(f"Gập cổ ({neck_angle:.1f}° > 25°)")
            if shoulder_angle > 10.0:
                is_bad = True
                reasons.append(f"Lệch vai ({shoulder_angle:.1f}° > 10°)")

            # Vẽ landmark trực quan trên frame
            cv2.line(frame, left_shoulder, right_shoulder, (255, 200, 0), 2)
            cv2.line(frame, chosen_ear, chosen_shoulder, (0, 255, 255), 2)
            cv2.circle(frame, chosen_ear, 5, (0, 0, 255), -1)
            cv2.circle(frame, chosen_shoulder, 5, (0, 255, 0), -1)

        # Cập nhật state debounce 10s
        track_info = tracker.update(is_bad, reasons)

        # Nếu kích hoạt cảnh báo, gửi tín hiệu sang Backend
        if track_info.get("alert"):
            angles = {"neck": neck_angle, "shoulder": shoulder_angle}
            publisher.send_posture_alert(reasons, track_info["bad_duration"], angles)

        # Hiển thị HUD thông tin
        status_color = (0, 255, 0) if track_info["state"] == "GOOD" else (0, 165, 255)
        if track_info["state"] == "ALERT_TRIGGERED":
            status_color = (0, 0, 255)
            cv2.putText(frame, "CANH BAO: NGOI THANG LUNG!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

        cv2.putText(frame, f"FPS: {smoothed_fps:.1f}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Neck Tilt: {neck_angle:.1f} deg", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 2)
        cv2.putText(frame, f"Shoulder Tilt: {shoulder_angle:.1f} deg", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 2)
        cv2.putText(frame, f"State: {track_info['state']} (Bad: {track_info['bad_duration']:.1f}s)", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        cv2.imshow("Robot Hoc Tap - Training AI Monitor (Quoc & Phuc)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()

if __name__ == "__main__":
    run_posture_monitor()
