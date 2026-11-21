"""
image_optimizer.py — Tối ưu ảnh trang vở trước khi gửi lên LLM Vision API.

Vị trí trong luồng dữ liệu:
    page_deskew.py (Quốc) → [numpy array] → image_optimizer.py (Phúc) → [bytes] → backend_client.py

Mục tiêu:
    - Giảm ≥ 70% dung lượng ảnh so với ảnh thô từ camera
    - Giữ chữ viết tay/bút chì đủ nét để LLM Vision đọc được
    - Giữ ước tính token dưới 500 tokens/lần gọi API
"""

import base64
import cv2
import numpy as np


# ──────────────────────────────────────────────
# CÁC HẰNG SỐ MẶC ĐỊNH
# ──────────────────────────────────────────────

DEFAULT_MAX_WIDTH   = 800    # px — chiều rộng tối đa sau downscale
DEFAULT_JPEG_QUALITY = 82    # 0–100, 82 là điểm cân bằng chất lượng/kích thước tốt
CLAHE_CLIP_LIMIT    = 2.5    # Giới hạn khuếch đại CLAHE (cao hơn = tương phản mạnh hơn)
CLAHE_TILE_GRID     = (8, 8) # Kích thước ô lưới CLAHE


# ──────────────────────────────────────────────
# CÁC HÀM ĐƠN LẺ
# ──────────────────────────────────────────────

def downscale(image: np.ndarray, max_width: int = DEFAULT_MAX_WIDTH) -> np.ndarray:
    """
    Thu nhỏ ảnh về chiều rộng tối đa, giữ nguyên tỉ lệ khung hình.
    Nếu ảnh đã nhỏ hơn max_width thì trả về nguyên bản.

    Args:
        image:     Ảnh numpy array (BGR hoặc Grayscale).
        max_width: Chiều rộng tối đa cho phép (px).

    Returns:
        Ảnh đã thu nhỏ (hoặc nguyên bản nếu không cần thu).
    """
    h, w = image.shape[:2]
    if w <= max_width:
        return image

    scale = max_width / w
    new_w = max_width
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Tăng tương phản chữ bằng CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Phù hợp với chữ bút chì nhạt hoặc ánh sáng không đều trên trang vở.

    Luồng xử lý:
        BGR → LAB (tách kênh sáng) → CLAHE trên kênh L → ghép lại → BGR

    Args:
        image: Ảnh numpy array BGR.

    Returns:
        Ảnh BGR với chữ sắc nét hơn, nền đồng đều hơn.
    """
    # Chuyển sang không gian màu LAB để chỉ xử lý kênh độ sáng (L)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
    l_enhanced = clahe.apply(l_channel)

    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


def encode_jpeg(image: np.ndarray, quality: int = DEFAULT_JPEG_QUALITY) -> bytes:
    """
    Nén ảnh thành JPEG bytes trong bộ nhớ (không ghi file).

    Args:
        image:   Ảnh numpy array BGR.
        quality: Chất lượng JPEG (0–100).

    Returns:
        JPEG bytes.

    Raises:
        RuntimeError: Nếu encode thất bại.
    """
    success, buffer = cv2.imencode(
        ".jpg", image,
        [cv2.IMWRITE_JPEG_QUALITY, quality]
    )
    if not success:
        raise RuntimeError("encode_jpeg: cv2.imencode thất bại.")
    return buffer.tobytes()


def estimate_tokens_from_image(image_bytes: bytes) -> int:
    """
    Ước tính số token tiêu thụ khi gửi ảnh lên LLM Vision API dưới dạng base64.

    Cách tính: Claude/GPT Vision tính token dựa trên kích thước ảnh.
    Công thức xấp xỉ thực nghiệm: 1 token ≈ 750 bytes base64.

    Args:
        image_bytes: Ảnh dạng bytes (đã nén JPEG).

    Returns:
        Số token ước tính (int).
    """
    b64_len = len(base64.b64encode(image_bytes))
    return max(1, int(b64_len / 750))


# ──────────────────────────────────────────────
# HÀM TỔNG HỢP — DÙNG TRONG PRODUCTION
# ──────────────────────────────────────────────

def optimize_for_llm(
    image: np.ndarray,
    max_width: int = DEFAULT_MAX_WIDTH,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> dict:
    """
    Pipeline tổng hợp: nhận ảnh thô từ page_deskew.py, trả ra dict sẵn sàng gửi API.

    Thứ tự xử lý:
        1. Downscale về max_width
        2. Tăng tương phản CLAHE
        3. Nén JPEG
        4. Ước tính token

    Args:
        image:        Ảnh numpy array BGR (đầu ra từ page_deskew.py của Quốc).
        max_width:    Chiều rộng tối đa (px).
        jpeg_quality: Chất lượng nén JPEG (0–100).

    Returns:
        dict với các key:
            "image_bytes"     : bytes  — JPEG bytes sẵn sàng encode base64 gửi API
            "estimated_tokens": int    — ước tính token tiêu thụ
            "original_size_kb": float  — kích thước ảnh gốc (KB)
            "optimized_size_kb": float — kích thước ảnh sau tối ưu (KB)
            "reduction_pct"   : float  — phần trăm giảm kích thước
            "final_resolution": tuple  — (width, height) sau xử lý
    """
    # Kích thước ảnh gốc (ước tính từ numpy array raw)
    original_size_kb = image.nbytes / 1024.0

    # Bước 1: Thu nhỏ
    img = downscale(image, max_width)

    # Bước 2: Tăng tương phản
    img = enhance_contrast(img)

    # Bước 3: Nén JPEG
    image_bytes = encode_jpeg(img, jpeg_quality)

    # Bước 4: Thống kê
    optimized_size_kb = len(image_bytes) / 1024.0
    reduction_pct = (1.0 - optimized_size_kb / original_size_kb) * 100.0
    h, w = img.shape[:2]

    return {
        "image_bytes":      image_bytes,
        "estimated_tokens": estimate_tokens_from_image(image_bytes),
        "original_size_kb": round(original_size_kb, 1),
        "optimized_size_kb": round(optimized_size_kb, 1),
        "reduction_pct":    round(reduction_pct, 1),
        "final_resolution": (w, h),
    }
