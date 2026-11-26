"""
main_monitor.py — Màn hình giám sát tổng hợp cho Robot Học Tập.

Chạy:
    python main_monitor.py              # mặc định: chạy cả Pose + Attention
    python main_monitor.py --pose       # chỉ giám sát tư thế ngồi
    python main_monitor.py --attention  # chỉ giám sát buồn ngủ + quay đầu
    python main_monitor.py --all        # tường minh chạy cả 2 (giống mặc định)
"""

import os
import sys
import cv2
import time
import argparse
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
    from ai.detectors.posture_math import calculate_shoulder_tilt, calculate_neck_tilt, calculate_head_desk_proxy
    from ai.detectors.face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch
    from ai.analyzers.posture_tracker import PostureDebounceTracker
    from ai.clients.backend_client import BackendEventPublisher
except ImportError:
    try:
        from detectors.posture_math import calculate_shoulder_tilt, calculate_neck_tilt, calculate_head_desk_proxy
        from detectors.face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch
        from analyzers.posture_tracker import PostureDebounceTracker
        from clients.backend_client import BackendEventPublisher
    except ImportError:
        from posture_math import calculate_shoulder_tilt, calculate_neck_tilt, calculate_head_desk_proxy
        from face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch
        from posture_tracker import PostureDebounceTracker
        from backend_client import BackendEventPublisher


# ──────────────────────────────────────────────
# KHỞI TẠO MODEL
# ──────────────────────────────────────────────

def _find_model(filename: str) -> str | None:
    candidates = [
        os.path.join(CURRENT_DIR, "models", filename),
        os.path.join(CURRENT_DIR, filename),
        os.path.join(PROJECT_ROOT, filename),
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


def _load_pose_detector():
    model_path = _find_model("pose_landmarker_lite.task")
    if not model_path:
        print("❌ Không tìm thấy pose_landmarker_lite.task!")
        return None
    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.IMAGE,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        num_poses=1,
    )
    return vision.PoseLandmarker.create_from_options(options)


def _load_face_detector():
    model_path = _find_model("face_landmarker.task")
    if not model_path:
        print("❌ Không tìm thấy face_landmarker.task!")
        return None
    options = vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(options)


# ──────────────────────────────────────────────
# XỬ LÝ TỪNG FRAME
# ──────────────────────────────────────────────

LEFT_EYE_INDICES  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]


def _process_pose(frame, h, w, detector, tracker, publisher):
    """Phát hiện tư thế ngồi, vẽ HUD, gửi alert nếu cần. Trả về (neck_angle, shoulder_angle, track_info)."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    is_bad, reasons, neck_angle, shoulder_angle = False, [], 0.0, 0.0

    if result.pose_landmarks:
        lm = result.pose_landmarks[0]
        nose           = (int(lm[0].x * w),  int(lm[0].y * h))
        left_ear       = (int(lm[7].x * w),  int(lm[7].y * h))
        right_ear      = (int(lm[8].x * w),  int(lm[8].y * h))
        left_shoulder  = (int(lm[11].x * w), int(lm[11].y * h))
        right_shoulder = (int(lm[12].x * w), int(lm[12].y * h))

        chosen_ear      = left_ear      if lm[7].visibility >= lm[8].visibility else right_ear
        chosen_shoulder = left_shoulder if lm[7].visibility >= lm[8].visibility else right_shoulder

        neck_angle     = calculate_neck_tilt(chosen_ear, chosen_shoulder)
        shoulder_angle = calculate_shoulder_tilt(left_shoulder, right_shoulder)
        too_close, _   = calculate_head_desk_proxy(nose, left_shoulder, right_shoulder, h, w)

        if neck_angle > 25.0:
            is_bad = True
            reasons.append(f"Gap co ({neck_angle:.1f}°>25°)")
        if shoulder_angle > 10.0:
            is_bad = True
            reasons.append(f"Lech vai ({shoulder_angle:.1f}°>10°)")
        if too_close:
            is_bad = True
            reasons.append("Cui sat ban")

        cv2.line(frame, left_shoulder, right_shoulder, (255, 200, 0), 2)
        cv2.line(frame, chosen_ear, chosen_shoulder, (0, 255, 255), 2)
        cv2.circle(frame, chosen_ear, 5, (0, 0, 255), -1)
        cv2.circle(frame, chosen_shoulder, 5, (0, 255, 0), -1)

    track_info = tracker.update(is_bad, reasons)

    if track_info.get("alert"):
        publisher.send_posture_alert(reasons, track_info["bad_duration"],
                                     {"neck": neck_angle, "shoulder": shoulder_angle})
        cv2.putText(frame, "CANH BAO: NGOI THANG LUNG!", (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

    state_color = (0, 255, 0) if track_info["state"] == "GOOD" else \
                  (0, 0, 255) if track_info["state"] == "ALERT_TRIGGERED" else (0, 165, 255)
    cv2.putText(frame, f"[POSE] Neck:{neck_angle:.1f}  Shoulder:{shoulder_angle:.1f}",
                (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 255, 200), 2)
    cv2.putText(frame, f"[POSE] State:{track_info['state']} Bad:{track_info['bad_duration']:.1f}s",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, state_color, 2)

    return neck_angle, shoulder_angle, track_info


def _process_attention(frame, h, w, detector, publisher,
                       drowsy_start_ref: list, distracted_start_ref: list):
    """Phát hiện nhắm mắt + quay đầu, vẽ HUD, gửi alert nếu cần."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    status_ear = "Mo mat"
    status_yaw = "Nhin thang"
    now = time.time()

    if result.face_landmarks:
        lm     = result.face_landmarks[0]
        pts_2d = [(int(l.x * w), int(l.y * h)) for l in lm]

        ear_left  = calculate_ear_single_eye([pts_2d[i] for i in LEFT_EYE_INDICES])
        ear_right = calculate_ear_single_eye([pts_2d[i] for i in RIGHT_EYE_INDICES])
        avg_ear   = (ear_left + ear_right) / 2.0

        yaw_ratio, looking_away = estimate_head_pose_yaw_pitch(pts_2d)

        # Nhắm mắt
        if avg_ear < 0.20:
            if drowsy_start_ref[0] is None:
                drowsy_start_ref[0] = now
            dur = now - drowsy_start_ref[0]
            status_ear = f"NHAM MAT ({dur:.1f}s)"
            if dur > 3.0:
                cv2.putText(frame, "CANH BAO: BUON NGU!", (50, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
                publisher.send_attention_alert("DROWSY", f"Nham mat {dur:.1f}s")
        else:
            drowsy_start_ref[0] = None
            status_ear = f"Mo mat (EAR:{avg_ear:.2f})"

        # Quay đầu
        if looking_away:
            if distracted_start_ref[0] is None:
                distracted_start_ref[0] = now
            dur = now - distracted_start_ref[0]
            status_yaw = f"QUAY DAU ({dur:.1f}s)"
            if dur > 5.0:
                cv2.putText(frame, "CANH BAO: MAT TAP TRUNG!", (50, 255),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 3)
                publisher.send_attention_alert("DISTRACTED", f"Quay dau {dur:.1f}s")
        else:
            distracted_start_ref[0] = None
            status_yaw = f"Nhin thang (Yaw:{yaw_ratio:.2f})"

    cv2.putText(frame, f"[ATTN] Eye: {status_ear}",
                (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    cv2.putText(frame, f"[ATTN] Head: {status_yaw}",
                (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 0), 2)


# ──────────────────────────────────────────────
# VÒNG LẶP CHÍNH
# ──────────────────────────────────────────────

def run_monitor(enable_pose: bool, enable_attention: bool):
    mode_label = []
    if enable_pose:      mode_label.append("POSE")
    if enable_attention: mode_label.append("ATTENTION")

    print("=" * 60)
    print(f"🚀 ROBOT HỌC TẬP — MONITOR v2.0  [{' + '.join(mode_label)}]")
    print("=" * 60)

    # Khởi tạo model cần thiết
    pose_detector = _load_pose_detector() if enable_pose else None
    face_detector = _load_face_detector() if enable_attention else None

    if enable_pose and pose_detector is None:
        return
    if enable_attention and face_detector is None:
        return

    tracker   = PostureDebounceTracker(bad_duration_threshold=10.0, cooldown_seconds=120.0)
    publisher = BackendEventPublisher()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Không mở được webcam!")
        return

    prev_time      = time.time()
    smoothed_fps   = 0.0
    drowsy_start   = [None]      # dùng list để truyền tham chiếu vào hàm con
    distract_start = [None]

    print(f"✅ Camera sẵn sàng. Nhấn 'q' để dừng.")

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        h, w = frame.shape[:2]
        now  = time.time()
        dt   = now - prev_time
        prev_time = now

        if dt > 0:
            fps = 1.0 / dt
            smoothed_fps = fps if smoothed_fps == 0.0 else (0.85 * smoothed_fps + 0.15 * fps)

        if enable_pose:
            _process_pose(frame, h, w, pose_detector, tracker, publisher)

        if enable_attention:
            _process_attention(frame, h, w, face_detector, publisher,
                               drowsy_start, distract_start)

        cv2.putText(frame, f"FPS: {smoothed_fps:.1f}  Mode: {'+'.join(mode_label)}",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.imshow("Robot Hoc Tap - Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if pose_detector:
        pose_detector.close()
    if face_detector:
        face_detector.close()


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robot Học Tập — Monitor tổng hợp")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pose",      action="store_true", help="Chỉ giám sát tư thế ngồi")
    group.add_argument("--attention", action="store_true", help="Chỉ giám sát buồn ngủ + quay đầu")
    group.add_argument("--all",       action="store_true", help="Chạy cả Pose + Attention (mặc định)")
    args = parser.parse_args()

    # Mặc định (không truyền gì) = chạy cả 2
    if args.pose:
        run_monitor(enable_pose=True,  enable_attention=False)
    elif args.attention:
        run_monitor(enable_pose=False, enable_attention=True)
    else:
        run_monitor(enable_pose=True,  enable_attention=True)
