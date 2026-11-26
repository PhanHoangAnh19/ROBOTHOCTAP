"""
test_privacy_gate.py — Kiểm thử tương tác Cổng riêng tư đa tầng (Task 2 - Tuần 5 - Cột mốc M2).
Người thực hiện: NGUYỄN VĂN QUỐC (Nhóm Training AI).

Chức năng:
    - Mở webcam laptop giám sát trực tiếp.
    - Phát hiện khuôn mặt (MediaPipe FaceLandmarker) & phân đoạn diện tích da tay (HSV + YCrCb).
    - Tự động chặn ảnh vi phạm và chỉ cho phép chụp khi trang vở an toàn 100%.
    - Hỗ trợ phím 's' để chụp lưu mẫu kiểm thử đối kháng (phục vụ tiêu chí Q9 ≥ 98%).
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ai.detectors.privacy_gate import PrivacyGateDetector
    from ai.detectors.page_deskew import detect_page_contour
except ImportError:
    from detectors.privacy_gate import PrivacyGateDetector
    from detectors.page_deskew import detect_page_contour


def run_privacy_gate_demo(file_path: str = None):
    print("=" * 70)
    print("🛡️  KIỂM THỬ CỔNG RIÊNG TƯ ĐA TẦNG — PRIVACY GATE (TASK 2 - TUẦN 5 - M2)")
    print("Người thực hiện: NGUYỄN VĂN QUỐC (Nhóm Training AI)")
    print("Tiêu chuẩn Q9: Chặn mặt trẻ em & da tay che khuất ≥ 98% trước khi gửi LLM")
    print("=" * 70)

    # Thư mục lưu vết kiểm thử
    passed_dir = os.path.join(CURRENT_DIR, "data", "privacy_passed")
    blocked_dir = os.path.join(CURRENT_DIR, "data", "privacy_blocked")
    os.makedirs(passed_dir, exist_ok=True)
    os.makedirs(blocked_dir, exist_ok=True)

    detector = PrivacyGateDetector(max_skin_ratio=0.15, max_cluster_ratio=0.08)

    # Chế độ 1: Kiểm thử trên file ảnh đơn lẻ
    if file_path:
        if not os.path.exists(file_path):
            print(f"❌ Không tìm thấy file: {file_path}")
            return
        image = cv2.imread(file_path)
        if image is None:
            print(f"❌ Không đọc được file: {file_path}")
            return

        res = detector.evaluate_image(image)
        hud_frame = detector.draw_hud(image, res)

        print(f"\n📊 KẾT QUẢ ĐÁNH GIÁ ẢNH: {file_path}")
        print(f"  Trạng thái       : {res['status']} ({res['status_code']})")
        print(f"  An toàn (is_safe): {'✅ TRUE (Được phép gửi)' if res['is_safe'] else '❌ FALSE (Bị chặn)'}")
        print(f"  Lý do            : {res['reason']}")
        print(f"  Số khuôn mặt     : {res['faces_count']}")
        print(f"  Tỷ lệ da tay     : {res['skin_ratio']*100:.1f}%")
        print(f"  Điểm độ nét      : {res['blur_score']:.1f}")

        cv2.imshow("Privacy Gate Test - NGUYEN VAN QUOC", hud_frame)
        print("\n👉 Nhấn phím bất kỳ trên cửa sổ ảnh để đóng.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    # Chế độ 2: Kiểm thử thời gian thực qua webcam laptop
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Không thể kết nối với Webcam. Vui lòng kiểm tra quyền truy cập!")
        return

    print("👉 HƯỚNG DẪN KIỂM THỬ TRỰC TIẾP:")
    print("  1. Nhìn thẳng vào webcam: Hệ thống TỰ ĐỘNG LÀM MỜ / XÓA MẶT để bé không cần né tránh!")
    print("  2. Cầm trang vở để tay đè nhẹ ở mép: Hệ thống tự động làm mờ vùng tay mép vở.")
    print("  3. Nếu mặt hoặc tay che mất quá 30% bài tập: Hệ thống mới báo dời nhẹ ra để nhìn rõ đề.")
    print("👉 Phím tắt điều khiển:")
    print("  - Phím 'm': Bật/Tắt chế độ [Tự động xóa mặt] vs [Chặn nghiêm ngặt].")
    print("  - Phím 'b': Đổi kiểu che mặt giữa [Làm mờ Pixelate] và [Bôi đen Blackout].")
    print("  - Phím 's': Lưu ảnh kiểm thử đã qua cổng kiểm duyệt vào thư mục.")
    print("  - Phím 'q': Thoát chương trình.")

    saved_count = 0
    fps_smooth = 20.0
    prev_time = time.time()
    auto_anonymize = True
    anonymize_mode = "blur"

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        now = time.time()
        fps_instant = 1.0 / max(0.001, (now - prev_time))
        prev_time = now
        fps_smooth = 0.85 * fps_smooth + 0.15 * fps_instant

        # Thử tìm và nắn phẳng trang sách/vở nếu có
        corners, warped = detect_page_contour(frame)

        # Nếu có trang vở, kiểm tra cổng riêng tư trên chính trang vở đã nắn phẳng
        target_img = warped if warped is not None else frame
        res = detector.evaluate_image(target_img, auto_anonymize=auto_anonymize, anonymize_mode=anonymize_mode)

        # Vẽ HUD Cyber Quantum
        display_frame = detector.draw_hud(frame, res)

        # Thông tin chế độ góc dưới
        mode_str = f"Che do: {'TU DONG XOA MAT (ON)' if auto_anonymize else 'CHAN NGHIEM NGAT (OFF)'} | Kieu: {anonymize_mode.upper()} (Phim 'm', 'b')"
        cv2.putText(display_frame, mode_str, (20, display_frame.shape[0] - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1)
        cv2.putText(display_frame, f"FPS: {fps_smooth:.1f} | Ban doc Q9 Privacy Gate (Quoc)", 
                    (20, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 255, 180), 1)

        # Cửa sổ phụ 1: Trang vở sau khi nắn phẳng (nếu có)
        if warped is not None:
            warped_hud = detector.draw_hud(warped, res)
            wh, ww = warped_hud.shape[:2]
            scale = 350.0 / max(wh, ww)
            preview_warped = cv2.resize(warped_hud, (int(ww * scale), int(wh * scale)))
            cv2.imshow("Trang Vo Sau Kiem Duyet Rieng Tu", preview_warped)

        # Cửa sổ phụ 2: Hiển thị ngay ảnh đã được tự động làm mờ / xóa mặt (nếu an toàn)
        if res.get("sanitized_image") is not None and res["status_code"] == "PASSED_AUTO_ANONYMIZED":
            sanitized = res["sanitized_image"]
            sh, sw = sanitized.shape[:2]
            scale_s = 350.0 / max(sh, sw)
            preview_sanitized = cv2.resize(sanitized, (int(sw * scale_s), int(sh * scale_s)))
            cv2.imshow("Anh Da Xoa Mat (Sanitized Payload Cho LLM)", preview_sanitized)

        cv2.imshow("Robot Hoc Tap - Cong Rieng Tu Privacy Gate (Quoc)", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            auto_anonymize = not auto_anonymize
            print(f"🔄 Chuyển chế độ Auto-Anonymize: {'BẬT (Tự động xóa mặt)' if auto_anonymize else 'TẮT (Chặn nghiêm ngặt)'}")
        elif key == ord('b'):
            anonymize_mode = "blackout" if anonymize_mode == "blur" else "blur"
            print(f"🎨 Chuyển kiểu che mặt: {anonymize_mode.upper()}")
        elif key == ord('s'):
            saved_count += 1
            timestamp = int(time.time())
            save_img = res["sanitized_image"] if res.get("sanitized_image") is not None else target_img
            if res["is_safe"]:
                save_path = os.path.join(passed_dir, f"passed_{res['status_code']}_{timestamp}_{saved_count:02d}.jpg")
                cv2.imwrite(save_path, save_img)
                print(f"📸 [PASSED] Đã lưu mẫu an toàn (đã bảo vệ danh tính): {save_path}")
            else:
                save_path = os.path.join(blocked_dir, f"blocked_{res['status_code']}_{timestamp}_{saved_count:02d}.jpg")
                cv2.imwrite(save_path, save_img)
                print(f"🚫 [BLOCKED] Đã lưu mẫu vi phạm: {save_path} ({res['reason']})")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n🎉 Kết thúc phiên test. Tổng cộng đã lưu {saved_count} mẫu kiểm thử.")


def run_q9_benchmark():
    """Quét tự động 4 nhóm ảnh đối kháng trong ai/data/adversarial_tests/ để báo cáo chỉ số Q9."""
    base_dir = os.path.join(CURRENT_DIR, "data", "adversarial_tests")
    groups = [
        ("group1_half_face",        "Nhóm 1: Lọt nửa mặt trẻ em",      True),
        ("group2_hand_on_book",     "Nhóm 2: Bàn tay đè lên sách",     True),
        ("group3_adult_background", "Nhóm 3: Người lớn đi phía sau",   True),
        ("group4_clean_page",       "Nhóm 4: Trang sách sạch đạt chuẩn", False),
    ]
    detector = PrivacyGateDetector(max_skin_ratio=0.15, max_cluster_ratio=0.08)

    print("=" * 72)
    print("📊 BENCHMARK CHỈ SỐ Q9 — CỔNG RIÊNG TƯ ĐA TẦNG (QUỐC & PHÚC)")
    print("=" * 72)

    total_imgs = 0
    total_correct = 0

    for folder, label, should_detect_privacy in groups:
        g_path = os.path.join(base_dir, folder)
        if not os.path.exists(g_path):
            print(f"⚠️ Chưa có thư mục: {g_path}")
            continue
        files = [f for f in os.listdir(g_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not files:
            print(f"📁 {label:<36}: 0 ảnh (Đang chờ nạp ảnh vào {folder}/)")
            continue

        correct = 0
        for fname in files:
            img = cv2.imread(os.path.join(g_path, fname))
            if img is None:
                continue
            # Kiểm tra chế độ strict để đo độ nhạy phát hiện mặt/da (Q9 >= 98%)
            res_strict = detector.evaluate_image(img, auto_anonymize=False)
            detected_violation = not res_strict["is_safe"]
            if detected_violation == should_detect_privacy:
                correct += 1

        total_imgs += len(files)
        total_correct += correct
        acc = (correct / len(files)) * 100.0
        print(f"📁 {label:<36}: {correct}/{len(files)} đúng ({acc:.1f}%)")

    print("-" * 72)
    if total_imgs > 0:
        overall = (total_correct / total_imgs) * 100.0
        print(f"🎯 TỔNG KẾT Q9: {total_correct}/{total_imgs} ảnh chính xác ({overall:.1f}%) — {'✅ ĐẠT (>=98%)' if overall >= 98.0 else '⚠️ CẦN BỔ SUNG'}")
    else:
        print("💡 Hướng dẫn: Bỏ các ảnh test vào 4 thư mục trong ai/data/adversarial_tests/ rồi chạy lại --benchmark.")
    print("=" * 72)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Privacy Gate đa tầng (Quốc)")
    parser.add_argument("--file", "-f", type=str, default=None, help="Đường dẫn file ảnh test đơn lẻ")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Chạy benchmark 4 nhóm ảnh đối kháng Q9")
    args = parser.parse_args()
    if args.benchmark:
        run_q9_benchmark()
    else:
        run_privacy_gate_demo(file_path=args.file)
