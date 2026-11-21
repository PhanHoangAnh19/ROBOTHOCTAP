"""
test_image_optimizer.py — Script test module image_optimizer.

Chạy được ngay không cần phần cứng robot, hỗ trợ 2 chế độ:
    1. --file <đường_dẫn>  : Test trên file ảnh có sẵn (ảnh chụp bằng điện thoại)
    2. (mặc định)          : Chụp 1 frame từ webcam laptop rồi test

Kết quả hiển thị:
    - Bảng thống kê: kích thước trước/sau, % giảm, ước tính token
    - Cửa sổ so sánh ảnh gốc | ảnh đã tối ưu (nhấn 'q' để đóng)

Chạy:
    cd ai
    python test_image_optimizer.py
    python test_image_optimizer.py --file anh_vo.jpg
"""

import os
import sys
import argparse
import cv2
import numpy as np

# Cho phép chạy trực tiếp hoặc import từ ngoài thư mục ai/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ai.utils.image_optimizer import optimize_for_llm, downscale, enhance_contrast
except ImportError:
    from utils.image_optimizer import optimize_for_llm, downscale, enhance_contrast


# ──────────────────────────────────────────────
# LẤY ẢNH ĐẦU VÀO
# ──────────────────────────────────────────────

def capture_from_webcam() -> np.ndarray:
    """Chụp 1 frame từ webcam laptop (index 0)."""
    print("📷 Đang mở webcam laptop...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Không mở được webcam (index 0). Thử dùng --file thay thế.")
        sys.exit(1)

    # Warm-up 10 frame để camera ổn định độ sáng
    for _ in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("❌ Không đọc được frame từ webcam.")
        sys.exit(1)

    print(f"✅ Đã chụp frame từ webcam: {frame.shape[1]}×{frame.shape[0]} px")
    return frame


def load_from_file(path: str) -> np.ndarray:
    """Đọc ảnh từ file."""
    image = cv2.imread(path)
    if image is None:
        print(f"❌ Không đọc được file: {path}")
        sys.exit(1)
    print(f"✅ Đã đọc file ảnh: {image.shape[1]}×{image.shape[0]} px  ({path})")
    return image


# ──────────────────────────────────────────────
# HIỂN THỊ KẾT QUẢ
# ──────────────────────────────────────────────

def print_report(result: dict) -> None:
    """In bảng thống kê ra terminal."""
    print("\n" + "=" * 55)
    print("📊 KẾT QUẢ TỐI ƯU ẢNH")
    print("=" * 55)
    print(f"  Kích thước gốc (raw numpy) : {result['original_size_kb']:>8.1f} KB")
    print(f"  Kích thước sau tối ưu      : {result['optimized_size_kb']:>8.1f} KB")
    print(f"  Mức giảm                   : {result['reduction_pct']:>7.1f} %")
    print(f"  Độ phân giải cuối          : {result['final_resolution'][0]}×{result['final_resolution'][1]} px")
    print(f"  Ước tính token API         : ~{result['estimated_tokens']} tokens")
    print("=" * 55)

    # Nhận xét đạt/không đạt mục tiêu
    ok_reduction = result['reduction_pct'] >= 70.0
    ok_tokens    = result['estimated_tokens'] <= 500

    print(f"  {'✅' if ok_reduction else '⚠️ '} Giảm ≥ 70%  : {'ĐẠT' if ok_reduction else 'CHƯA ĐẠT — thử giảm max_width hoặc jpeg_quality'}")
    print(f"  {'✅' if ok_tokens    else '⚠️ '} Token ≤ 500 : {'ĐẠT' if ok_tokens    else 'CHƯA ĐẠT — thử giảm max_width thêm'}")
    print("=" * 55 + "\n")


def show_comparison(original: np.ndarray, result: dict) -> None:
    """Hiển thị ảnh gốc bên trái, ảnh tối ưu bên phải để so sánh trực quan."""
    # Giải mã ảnh tối ưu từ bytes
    nparr = np.frombuffer(result["image_bytes"], np.uint8)
    optimized = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Resize cả 2 về cùng chiều cao để ghép ngang
    target_h = 500
    def resize_to_height(img, h):
        ratio = h / img.shape[0]
        return cv2.resize(img, (int(img.shape[1] * ratio), h), interpolation=cv2.INTER_AREA)

    orig_display = resize_to_height(original, target_h)
    opt_display  = resize_to_height(optimized, target_h)

    # Thêm label
    cv2.putText(orig_display, f"GOC  {original.shape[1]}x{original.shape[0]}px",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 80, 255), 2)
    cv2.putText(opt_display,
                f"DA TOI UU  {result['final_resolution'][0]}x{result['final_resolution'][1]}px  ~{result['estimated_tokens']} tokens",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 0), 2)

    # Đường kẻ phân cách
    divider = np.zeros((target_h, 4, 3), dtype=np.uint8)
    divider[:] = (200, 200, 200)

    combined = np.hstack([orig_display, divider, opt_display])
    cv2.imshow("image_optimizer — Goc | Da toi uu  (nhan 'q' de dong)", combined)

    print("🖼️  Đang hiển thị so sánh ảnh. Nhấn 'q' để đóng...")
    while True:
        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
        # Đóng nếu người dùng bấm nút X cửa sổ
        if cv2.getWindowProperty(
            "image_optimizer — Goc | Da toi uu  (nhan 'q' de dong)",
            cv2.WND_PROP_VISIBLE
        ) < 1:
            break

    cv2.destroyAllWindows()


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Test image_optimizer.py — tối ưu ảnh trang vở trước khi gửi LLM API"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Đường dẫn tới file ảnh. Bỏ trống = chụp từ webcam laptop."
    )
    parser.add_argument(
        "--max-width", "-w",
        type=int,
        default=800,
        help="Chiều rộng tối đa sau downscale (mặc định: 800px)."
    )
    parser.add_argument(
        "--quality", "-q",
        type=int,
        default=82,
        help="Chất lượng JPEG 0–100 (mặc định: 82)."
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Chỉ in bảng số liệu, không hiển thị cửa sổ ảnh."
    )
    args = parser.parse_args()

    print("=" * 55)
    print("🤖 TEST image_optimizer.py — NHÓM TRAINING AI (PHÚC)")
    print("=" * 55)

    # Lấy ảnh đầu vào
    if args.file:
        image = load_from_file(args.file)
    else:
        image = capture_from_webcam()

    # Chạy optimizer
    print(f"\n⚙️  Đang xử lý (max_width={args.max_width}, quality={args.quality})...")
    result = optimize_for_llm(image, max_width=args.max_width, jpeg_quality=args.quality)

    # In báo cáo
    print_report(result)

    # Hiển thị so sánh
    if not args.no_display:
        show_comparison(image, result)

    print("✅ Hoàn thành.")


if __name__ == "__main__":
    main()
