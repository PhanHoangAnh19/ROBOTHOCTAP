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

try:
    from ai.detectors.page_deskew import detect_page_contour
    from ai.detectors.page_stability import PageStabilityDetector
except ImportError:
    from detectors.page_deskew import detect_page_contour
    from detectors.page_stability import PageStabilityDetector

def run_page_deskew_demo():
    print("=" * 65)
    print("📖 DEMO PHÁT HIỆN & CẮT PHẲNG TRANG SÁCH/VỞ (TASK 2 & 3 - TUẦN 4)")
    print("Người thực hiện: NGUYỄN VĂN QUỐC (Training AI)")
    print("Mục tiêu: Tìm 4 góc vở -> Duỗi phẳng (Deskew) -> Phát hiện ổn định")
    print("=" * 65)

    # Thư mục lưu 20+ ảnh mẫu nộp báo cáo
    save_dir = os.path.join(CURRENT_DIR, "data", "deskewed_samples")
    os.makedirs(save_dir, exist_ok=True)

    stability_detector = PageStabilityDetector(required_duration=1.0, movement_threshold=10.0, max_hand_coverage=0.15)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Không thể kết nối với Webcam. Vui lòng kiểm tra lại quyền truy cập!")
        return

    sample_count = len([f for f in os.listdir(save_dir) if f.endswith(".jpg")])
    print(f"📁 Thư mục lưu mẫu: {save_dir}")
    print(f"📊 Đã có {sample_count} ảnh mẫu trong thư mục.")
    print("👉 HƯỚNG DẪN: Đặt một cuốn sách/vở trước camera. Giữ yên 1 giây để hệ thống nhận diện.")
    print("👉 Phím tắt: Nhấn 's' để lưu ảnh trang vở, 'q' để thoát.")

    last_auto_save_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        corners, warped = detect_page_contour(frame)

        # Kiểm tra tính ổn định của trang
        status = stability_detector.check_stability(corners, warped)

        # 1. Vẽ khung phát hiện trang vở hoặc khung hướng dẫn
        if corners is not None:
            corners_int = np.int32(corners)
            border_color = (0, 255, 0) if status["is_stable"] else (0, 165, 255)
            cv2.polylines(frame, [corners_int], True, border_color, 3)

            # Đánh dấu 4 đỉnh
            for i, pt in enumerate(corners_int):
                cv2.circle(frame, tuple(pt), 6, (0, 0, 255), -1)
                cv2.putText(frame, str(i + 1), (pt[0] - 10, pt[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        else:
            # Khung gợi ý vị trí đặt sách
            cv2.rectangle(frame, (int(w * 0.15), int(h * 0.22)), (int(w * 0.85), int(h * 0.88)), (200, 200, 0), 1)
            cv2.putText(frame, "Huong dan: De ca 4 goc sach/vo lot vao khung camera (Lui xa ~40cm)", 
                        (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # 2. Hiển thị HUD thông tin
        cv2.rectangle(frame, (10, 10), (450, 110), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (450, 110), (100, 100, 100), 2)

        text_color = (0, 255, 0) if status["is_stable"] else (0, 200, 255)
        cv2.putText(frame, f"Trang thai: {status['status_msg']}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 2)
        cv2.putText(frame, f"Ty le da tay che: {status['skin_coverage']*100:.1f}% (<15%)", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

        # Thanh tiến trình ổn định
        progress_w = int(250 * status["progress"])
        cv2.rectangle(frame, (20, 75), (270, 95), (60, 60, 60), -1)
        cv2.rectangle(frame, (20, 75), (20 + progress_w, 95), (0, 255, 0), -1)
        cv2.putText(frame, f"{int(status['progress']*100)}%", (280, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.putText(frame, f"Da luu: {sample_count} anh | Phim 's': Chup luu", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # 3. Hiển thị cửa sổ phụ trang vở đã cắt phẳng
        if warped is not None:
            # Resize cửa sổ phụ hiển thị vừa vặn
            warped_h, warped_w = warped.shape[:2]
            scale = 350.0 / max(warped_h, warped_w)
            preview_warped = cv2.resize(warped, (int(warped_w * scale), int(warped_h * scale)))
            cv2.imshow("Trang Vo Da Duoi Thang (Deskewed Page)", preview_warped)

        cv2.imshow("Robot Hoc Tap - Giam Sat Trang Sach/Vo (Quoc)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and warped is not None:
            # Lưu thủ công khi nhấn phím 's'
            sample_count += 1
            filename = f"sample_page_{sample_count:02d}.jpg"
            filepath = os.path.join(save_dir, filename)
            cv2.imwrite(filepath, warped)
            print(f"📸 Đã lưu trang vở thành công: {filepath} ({warped.shape[1]}x{warped.shape[0]} px)")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n🎉 Kết thúc phiên test. Tổng cộng có {sample_count} ảnh trong thư mục {save_dir}")

if __name__ == "__main__":
    run_page_deskew_demo()
