"""
main_monitor.py — Màn hình giám sát tổng hợp cho Robot Học Tập (Tuần 1–5 — Cột mốc M2).

Chạy:
    python main_monitor.py              # mặc định: chạy cả Pose + Attention + Privacy Gate
    python main_monitor.py --pose       # chỉ giám sát tư thế ngồi
    python main_monitor.py --attention  # chỉ giám sát buồn ngủ + quay đầu
    python main_monitor.py --gate       # chỉ giám sát cắt trang vở + Cổng riêng tư (Privacy Gate)
    python main_monitor.py --all        # tường minh chạy toàn bộ 3 luồng (giống mặc định)

Phím tắt khi chạy:
    'c' : Chụp & quét kiểm duyệt trang vở/khung hình qua Cổng riêng tư + Tối ưu Token
    'm' : Bật/Tắt chế độ [Tự động xóa/làm mờ mặt] vs [Chặn nghiêm ngặt]
    'b' : Đổi kiểu che mặt giữa [BLUR - Làm mờ Pixelate] và [BLACKOUT - Hộp đen]
    's' : Lưu ảnh mẫu kiểm thử vào ai/data/privacy_passed/ hoặc privacy_blocked/
    'q' : Thoát chương trình
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
    from ai.detectors.page_deskew import detect_page_contour
    from ai.detectors.page_stability import PageStabilityDetector
    from ai.detectors.privacy_gate import PrivacyGateDetector
    from ai.analyzers.posture_tracker import PostureDebounceTracker
    from ai.clients.backend_client import BackendEventPublisher
    from ai.utils.image_optimizer import optimize_for_llm
except ImportError:
    from detectors.posture_math import calculate_shoulder_tilt, calculate_neck_tilt, calculate_head_desk_proxy
    from detectors.face_attention import calculate_ear_single_eye, estimate_head_pose_yaw_pitch
    from detectors.page_deskew import detect_page_contour
    from detectors.page_stability import PageStabilityDetector
    from detectors.privacy_gate import PrivacyGateDetector
    from analyzers.posture_tracker import PostureDebounceTracker
    from clients.backend_client import BackendEventPublisher
    from utils.image_optimizer import optimize_for_llm


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
        num_faces=2,
        min_face_detection_confidence=0.35,
        min_face_presence_confidence=0.35,
    )
    return vision.FaceLandmarker.create_from_options(options)


# ──────────────────────────────────────────────
# XỬ LÝ TỪNG FRAME (CÓ CACHE TỐI ƯU FPS)
# ──────────────────────────────────────────────

LEFT_EYE_INDICES  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]


def _process_pose(frame, h, w, detector, tracker, publisher, run_inference: bool, pose_cache: dict):
    """Phát hiện tư thế ngồi (chạy inference xen kẽ để giữ FPS cao 15-20 FPS)."""
    if run_inference:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pose_cache["result"] = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    result = pose_cache.get("result")
    is_bad, reasons, neck_angle, shoulder_angle = False, [], 0.0, 0.0

    if result and result.pose_landmarks:
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
        cv2.putText(frame, "CANH BAO: NGOI THANG LUNG!", (50, 215),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)

    state_color = (0, 255, 0) if track_info["state"] == "GOOD" else \
                  (0, 0, 255) if track_info["state"] == "ALERT_TRIGGERED" else (0, 165, 255)
    cv2.putText(frame, f"[POSE] Neck:{neck_angle:.1f}  Shoulder:{shoulder_angle:.1f}",
                (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 255, 200), 2)
    cv2.putText(frame, f"[POSE] State:{track_info['state']} Bad:{track_info['bad_duration']:.1f}s",
                (20, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.52, state_color, 2)

    return neck_angle, shoulder_angle, track_info


def _process_attention(frame, h, w, detector, publisher,
                       drowsy_start_ref: list, distracted_start_ref: list,
                       run_inference: bool, face_cache: dict):
    """Phát hiện nhắm mắt + quay đầu (chạy inference xen kẽ để giữ FPS cao)."""
    if run_inference:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_cache["result"] = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    result = face_cache.get("result")
    status_ear = "Mo mat"
    status_yaw = "Nhin thang"
    now = time.time()

    if result and result.face_landmarks:
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
                cv2.putText(frame, "CANH BAO: BUON NGU!", (50, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)
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
                cv2.putText(frame, "CANH BAO: MAT TAP TRUNG!", (50, 285),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 165, 255), 3)
                publisher.send_attention_alert("DISTRACTED", f"Quay dau {dur:.1f}s")
        else:
            distracted_start_ref[0] = None
            status_yaw = f"Nhin thang (Yaw:{yaw_ratio:.2f})"

    cv2.putText(frame, f"[ATTN] Eye: {status_ear}",
                (20, 103), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 0), 2)
    cv2.putText(frame, f"[ATTN] Head: {status_yaw}",
                (20, 126), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 200, 0), 2)


def _process_page_and_gate(frame, raw_frame, h, w, stability_detector, last_gate_result: dict,
                           auto_anonymize: bool, anonymize_mode: str,
                           run_page_detect: bool, page_cache: dict):
    """
    Phát hiện 4 góc trang sách/vở (Deskew), kiểm tra độ ổn định (Stability)
    và hiển thị trạng thái Cổng riêng tư (Privacy Gate).
    """
    if run_page_detect:
        corners, warped = detect_page_contour(raw_frame)
        stability = stability_detector.check_stability(corners, warped)
        page_cache["corners"] = corners
        page_cache["warped"] = warped
        page_cache["stability"] = stability
    else:
        corners = page_cache.get("corners")
        warped = page_cache.get("warped")
        stability = page_cache.get("stability") or stability_detector.check_stability(None, None)

    if corners is not None:
        corners_int = np.int32(corners)
        border_color = (0, 255, 0) if stability["is_stable"] else (0, 165, 255)
        cv2.polylines(frame, [corners_int], True, border_color, 2)
        for i, pt in enumerate(corners_int):
            cv2.circle(frame, tuple(pt), 5, (0, 0, 255), -1)
            cv2.putText(frame, str(i + 1), (pt[0] - 8, pt[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    gate_color = (255, 200, 0) if last_gate_result["status_code"] == "PASSED_AUTO_ANONYMIZED" else \
                 (0, 255, 0) if last_gate_result["is_safe"] else (0, 100, 255)

    page_str = f"Trang vo: {stability['status_msg']} ({int(stability['progress']*100)}%)"
    gate_str = f"[GATE] {last_gate_result['status']} | Auto-Blur:{'ON' if auto_anonymize else 'OFF'} ({anonymize_mode.upper()})"

    cv2.putText(frame, f"[PAGE] {page_str}",
                (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 255), 2)
    cv2.putText(frame, gate_str,
                (20, 173), cv2.FONT_HERSHEY_SIMPLEX, 0.50, gate_color, 2)
    cv2.putText(frame, "Phim 'c': Quet Gate & Xoa Mat | 'm': Auto-Blur | 'b': Blur/Black | 's': Luu",
                (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 255, 255), 1)

    return corners, warped, stability


def _show_gate_subwindow(privacy_gate, source_img, gate_res, subwindow_positioned_ref: list):
    """Hiển thị cửa sổ phụ Cổng riêng tư bên phải màn hình, đảm bảo mặt đã được làm mờ 100%."""
    if source_img is None:
        return
    win_name = "Trang Vo & Cong Rieng Tu (Deskew + Privacy Gate)"
    # draw_hud tự động lấy sanitized_image (đã làm mờ mặt) để hiển thị
    hud_img = privacy_gate.draw_hud(source_img, gate_res)
    wh, ww = hud_img.shape[:2]
    scale = 480.0 / max(wh, ww)
    preview = cv2.resize(hud_img, (int(ww * scale), int(wh * scale)))
    cv2.imshow(win_name, preview)
    if not subwindow_positioned_ref[0]:
        try:
            cv2.moveWindow(win_name, 700, 60)
        except Exception:
            pass
        subwindow_positioned_ref[0] = True


# ──────────────────────────────────────────────
# VÒNG LẶP CHÍNH
# ──────────────────────────────────────────────

def run_monitor(enable_pose: bool, enable_attention: bool, enable_gate: bool = True):
    mode_label = []
    if enable_pose:      mode_label.append("POSE")
    if enable_attention: mode_label.append("ATTENTION")
    if enable_gate:      mode_label.append("PRIVACY_GATE")

    print("=" * 68)
    print(f"🚀 ROBOT HỌC TẬP — MONITOR TỔNG HỢP v3.1 (MỐC M2) [{' + '.join(mode_label)}]")
    print("=" * 68)

    # Khởi tạo model cần thiết (Chia sẻ chung face_detector để không tốn gấp đôi RAM/CPU)
    pose_detector = _load_pose_detector() if enable_pose else None
    face_detector = _load_face_detector() if (enable_attention or enable_gate) else None
    privacy_gate  = PrivacyGateDetector(
        max_skin_ratio=0.15, max_cluster_ratio=0.08, shared_face_detector=face_detector
    ) if enable_gate else None
    stability_det = PageStabilityDetector(required_duration=1.0, movement_threshold=18.0, max_hand_coverage=0.15) if enable_gate else None

    if enable_pose and pose_detector is None:
        return
    if enable_attention and face_detector is None:
        return

    tracker   = PostureDebounceTracker(bad_duration_threshold=10.0, cooldown_seconds=120.0)
    publisher = BackendEventPublisher()

    passed_dir  = os.path.join(CURRENT_DIR, "data", "privacy_passed")
    blocked_dir = os.path.join(CURRENT_DIR, "data", "privacy_blocked")
    if enable_gate:
        os.makedirs(passed_dir, exist_ok=True)
        os.makedirs(blocked_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠️ Không mở được webcam!")
        return

    prev_time      = time.time()
    smoothed_fps   = 0.0
    drowsy_start   = [None]
    distract_start = [None]
    frame_idx      = 0

    pose_cache = {"result": None}
    face_cache = {"result": None}
    page_cache = {"corners": None, "warped": None, "stability": None}

    auto_anonymize = True
    anonymize_mode = "blur"
    saved_count    = 0
    subwin_moved   = [False]
    last_captured_target = None
    last_gate_res  = {
        "is_safe": True,
        "status": "SAN_SANG",
        "status_code": "READY",
        "reason": "Nhan 'c' hoac giu yen vo 1s de quet Cong rieng tu",
        "faces_count": 0,
        "face_boxes": [],
        "skin_ratio": 0.0,
        "max_cluster_ratio": 0.0,
        "skin_clusters": [],
        "blur_score": 0.0,
        "is_blurry": False,
        "sanitized_image": None,
    }
    last_auto_gate_time = 0.0

    print("✅ Camera sẵn sàng.")
    if enable_gate:
        print("👉 Phím tắt Cổng riêng tư (Privacy Gate):")
        print("   - Phím 'c': Chụp & kiểm duyệt qua Privacy Gate (Tự động làm mờ mặt + Tối ưu Token)")
        print("   - Phím 'm': Bật/Tắt chế độ Tự động xóa/làm mờ mặt (Auto-Anonymize)")
        print("   - Phím 'b': Đổi kiểu che mặt BLUR (Làm mờ Pixelate) / BLACKOUT (Hộp đen)")
        print("   - Phím 's': Lưu ảnh mẫu đã kiểm duyệt")
    print("   - Phím 'q': Thoát chương trình.")

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        frame_idx += 1
        raw_frame = frame.copy()
        h, w = frame.shape[:2]
        now  = time.time()
        dt   = now - prev_time
        prev_time = now

        if dt > 0:
            fps = 1.0 / dt
            smoothed_fps = fps if smoothed_fps == 0.0 else (0.85 * smoothed_fps + 0.15 * fps)

        # Chạy xen kẽ Pose (frame chẵn) và Attention (frame lẻ) khi bật cả 2 để FPS tăng gấp đôi (15-22 FPS)
        both_heavy = enable_pose and enable_attention
        run_pose_inf = True if not both_heavy else (frame_idx % 2 == 0)
        run_attn_inf = True if not both_heavy else (frame_idx % 2 == 1)
        run_page_inf = (frame_idx % 2 == 0)

        if enable_pose:
            _process_pose(frame, h, w, pose_detector, tracker, publisher, run_pose_inf, pose_cache)

        if enable_attention:
            _process_attention(frame, h, w, face_detector, publisher,
                               drowsy_start, distract_start, run_attn_inf, face_cache)

        warped = None
        if enable_gate:
            corners, warped, stability = _process_page_and_gate(
                frame, raw_frame, h, w, stability_det, last_gate_res,
                auto_anonymize, anonymize_mode, run_page_inf, page_cache
            )
            # Tự động quét Cổng riêng tư khi trang vở thật đứng yên đủ 1.0s (cooldown 2.0s)
            if stability["is_stable"] and warped is not None and (now - last_auto_gate_time > 2.0):
                last_auto_gate_time = now
                last_captured_target = warped.copy()
                last_gate_res = privacy_gate.evaluate_image(
                    last_captured_target, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode
                )
                _show_gate_subwindow(privacy_gate, last_captured_target, last_gate_res, subwin_moved)

        cv2.putText(frame, f"FPS: {smoothed_fps:.1f}  Mode: {'+'.join(mode_label)}",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)

        cv2.imshow("Robot Hoc Tap - Monitor", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif enable_gate and key == ord('m'):
            auto_anonymize = not auto_anonymize
            print(f"🔄 Chế độ Auto-Anonymize (Tự động xóa mặt): {'BẬT' if auto_anonymize else 'TẮT (Chặn nghiêm ngặt)'}")
            # Cập nhật lại ngay cửa sổ phụ nếu đã có ảnh chụp
            target_img = last_captured_target if last_captured_target is not None else (warped if warped is not None else raw_frame)
            last_captured_target = target_img.copy()
            last_gate_res = privacy_gate.evaluate_image(
                last_captured_target, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode
            )
            _show_gate_subwindow(privacy_gate, last_captured_target, last_gate_res, subwin_moved)
        elif enable_gate and key == ord('b'):
            anonymize_mode = "blackout" if anonymize_mode == "blur" else "blur"
            print(f"🎨 Kiểu che mặt: {anonymize_mode.upper()}")
            target_img = last_captured_target if last_captured_target is not None else (warped if warped is not None else raw_frame)
            last_captured_target = target_img.copy()
            last_gate_res = privacy_gate.evaluate_image(
                last_captured_target, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode
            )
            _show_gate_subwindow(privacy_gate, last_captured_target, last_gate_res, subwin_moved)
        elif enable_gate and key == ord('c'):
            target_img = warped if warped is not None else raw_frame
            last_captured_target = target_img.copy()
            t0 = time.perf_counter()
            last_gate_res = privacy_gate.evaluate_image(
                last_captured_target, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode
            )
            gate_ms = (time.perf_counter() - t0) * 1000
            _show_gate_subwindow(privacy_gate, last_captured_target, last_gate_res, subwin_moved)

            print("\n" + "=" * 60)
            print(f"🛡️  KẾT QUẢ QUÉT CỔNG RIÊNG TƯ (Độ trễ: {gate_ms:.1f} ms)")
            print(f"  Trạng thái : {last_gate_res['status']} ({last_gate_res['status_code']})")
            print(f"  Lý do      : {last_gate_res['reason']}")
            print(f"  Khuôn mặt  : {last_gate_res['faces_count']} | Tỷ lệ da: {last_gate_res['skin_ratio']*100:.1f}%")

            if last_gate_res["is_safe"] and last_gate_res.get("sanitized_image") is not None:
                sanitized = last_gate_res["sanitized_image"]
                opt_res = optimize_for_llm(sanitized)
                print(f"  ✅ Tối ưu Token (Phúc): Giảm {opt_res['reduction_pct']}% | ~{opt_res['estimated_tokens']} tokens")
                print("  🚀 SẴN SÀNG GỬI ẢNH ĐÃ BẢO VỆ DANH TÍNH LÊN LLM!")
            else:
                print("  🚫 CHẶN AN TOÀN: 0 byte ảnh được gửi ra Cloud!")
            print("=" * 60 + "\n")
        elif enable_gate and key == ord('s'):
            target_img = last_captured_target if last_captured_target is not None else (warped if warped is not None else raw_frame)
            last_captured_target = target_img.copy()
            last_gate_res = privacy_gate.evaluate_image(
                last_captured_target, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode
            )
            _show_gate_subwindow(privacy_gate, last_captured_target, last_gate_res, subwin_moved)
            saved_count += 1
            ts = int(time.time())
            save_img = last_gate_res["sanitized_image"] if last_gate_res.get("sanitized_image") is not None else last_captured_target
            if last_gate_res["is_safe"]:
                path = os.path.join(passed_dir, f"passed_{last_gate_res['status_code']}_{ts}_{saved_count:02d}.jpg")
                cv2.imwrite(path, save_img)
                print(f"📸 [PASSED] Đã lưu ảnh an toàn: {path}")
            else:
                path = os.path.join(blocked_dir, f"blocked_{last_gate_res['status_code']}_{ts}_{saved_count:02d}.jpg")
                cv2.imwrite(path, save_img)
                print(f"🚫 [BLOCKED] Đã lưu mẫu bị chặn: {path}")

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
    parser = argparse.ArgumentParser(description="Robot Học Tập — Monitor tổng hợp (Mốc M2)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pose",      action="store_true", help="Chỉ giám sát tư thế ngồi")
    group.add_argument("--attention", action="store_true", help="Chỉ giám sát buồn ngủ + quay đầu")
    group.add_argument("--gate",      action="store_true", help="Chỉ giám sát cắt trang vở + Cổng riêng tư")
    group.add_argument("--all",       action="store_true", help="Chạy cả Pose + Attention + Privacy Gate (mặc định)")
    args = parser.parse_args()

    if args.pose:
        run_monitor(enable_pose=True,  enable_attention=False, enable_gate=False)
    elif args.attention:
        run_monitor(enable_pose=False, enable_attention=True,  enable_gate=False)
    elif args.gate:
        run_monitor(enable_pose=False, enable_attention=False, enable_gate=True)
    else:
        run_monitor(enable_pose=True,  enable_attention=True,  enable_gate=True)
