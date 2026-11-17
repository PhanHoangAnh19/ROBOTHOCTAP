import os
import sys
import cv2
import time
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

try:
    from ai.detectors.face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch
except ImportError:
    from detectors.face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch

def run_attention_test():
    print("=" * 60)
    print("👁️ TEST ĐO NHẮM MẮT (EAR) & QUAY ĐẦU (YAW/PITCH) - TUẦN 3")
    print("Mục tiêu: Đánh giá tính khả thi của tính năng chống buồn ngủ/mất tập trung")
    print("=" * 60)

    model_candidates = [
        os.path.join(CURRENT_DIR, "models", "face_landmarker.task"),
        os.path.join(CURRENT_DIR, "face_landmarker.task"),
        os.path.join(PROJECT_ROOT, "face_landmarker.task")
    ]
    model_path = next((p for p in model_candidates if os.path.exists(p)), None)
    if not model_path:
        print(f"❌ Không tìm thấy model face_landmarker.task!")
        return

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Không mở được webcam!")
        return

    # Chỉ số các điểm mắt theo chuẩn MediaPipe 468 mốc
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

    drowsy_start = None
    distracted_start = None

    print("✅ Đã kết nối camera. Nhấn 'q' để dừng.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = detector.detect(mp_image)

        status_ear = "Mo mat"
        status_yaw = "Nhin thang"
        now = time.time()

        if result.face_landmarks and len(result.face_landmarks) > 0:
            landmarks = result.face_landmarks[0]
            pts_2d = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

            # 1. Tính EAR mắt trái và mắt phải
            left_eye_pts = [pts_2d[i] for i in LEFT_EYE_INDICES]
            right_eye_pts = [pts_2d[i] for i in RIGHT_EYE_INDICES]

            ear_left = calculate_ear_single_eye(left_eye_pts)
            ear_right = calculate_ear_single_eye(right_eye_pts)
            avg_ear = (ear_left + ear_right) / 2.0

            # 2. Tính góc quay đầu
            yaw_ratio, looking_away = estimate_head_pose_yaw_pitch(pts_2d)

            # Đánh giá nhắm mắt (EAR < 0.20 là nhắm mắt)
            if avg_ear < 0.20:
                if drowsy_start is None:
                    drowsy_start = now
                drowsy_duration = now - drowsy_start
                status_ear = f"NHAM MAT ({drowsy_duration:.1f}s)"
                if drowsy_duration > 3.0:
                    cv2.putText(frame, "CANH BAO: BUON NGU!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
            else:
                drowsy_start = None
                status_ear = f"Mo mat (EAR: {avg_ear:.2f})"

            # Đánh giá quay đầu
            if looking_away:
                if distracted_start is None:
                    distracted_start = now
                distract_dur = now - distracted_start
                status_yaw = f"QUAY DAU ({distract_dur:.1f}s)"
                if distract_dur > 5.0:
                    cv2.putText(frame, "CANH BAO: MAT TAP TRUNG!", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 3)
            else:
                distracted_start = None
                status_yaw = f"Nhin thang (Yaw: {yaw_ratio:.2f})"

        cv2.putText(frame, f"Eye Status: {status_ear}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        cv2.putText(frame, f"Head Pose: {status_yaw}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 200, 0), 2)

        cv2.imshow("Test Attention (EAR + Yaw/Pitch)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()

if __name__ == "__main__":
    run_attention_test()
