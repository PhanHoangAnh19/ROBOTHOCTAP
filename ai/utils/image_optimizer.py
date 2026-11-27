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

DEFAULT_MAX_WIDTH    = 520    # px — thu nhỏ cả ảnh Pi Camera/điện thoại (1280px) lẫn webcam (640px)
DEFAULT_JPEG_QUALITY = 70     # 0–100, tối ưu dung lượng giảm >= 70% so với JPEG gốc Q95
CLAHE_CLIP_LIMIT     = 2.0    # Giới hạn khuếch đại CLAHE giữ chữ nét mà không tăng nhiễu hạt JPEG
CLAHE_TILE_GRID      = (8, 8) # Kích thước ô lưới CLAHE


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


def estimate_tokens_from_image(image_bytes: bytes, width: int = None, height: int = None) -> int:
    """
    Ước tính số token tiêu thụ khi gửi ảnh lên LLM Vision API (Claude / Gemini / GPT Vision).

    Cách tính chuẩn theo tài liệu Vision API:
        Token ảnh được tính theo diện tích điểm ảnh (pixel):
            tokens ≈ (width × height) / 750
        Ví dụ: Ảnh 640×480 ≈ 410 tokens; ảnh sau thu nhỏ 520×390 ≈ 270 tokens.

    Args:
        image_bytes: Ảnh dạng bytes (đã nén JPEG).
        width:       Chiều rộng ảnh (tự giải mã từ image_bytes nếu không truyền).
        height:      Chiều cao ảnh (tự giải mã từ image_bytes nếu không truyền).

    Returns:
        Số token ước tính theo diện tích pixel (int).
    """
    if width is None or height is None:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if decoded is not None:
            height, width = decoded.shape[:2]
        else:
            b64_len = len(base64.b64encode(image_bytes))
            return max(1, int(b64_len / 750))

    return max(1, int((width * height) / 750))


# ──────────────────────────────────────────────
# HÀM TỔNG HỢP — DÙNG TRONG PRODUCTION
# ──────────────────────────────────────────────

def optimize_for_llm(
    image: np.ndarray,
    max_width: int = DEFAULT_MAX_WIDTH,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> dict:
    """
    Pipeline tổng hợp: nhận ảnh từ page_deskew.py, trả ra dict sẵn sàng gửi API.

    Thứ tự xử lý:
        1. Đo kích thước JPEG gốc chuẩn (Q=95) trước khi xử lý để so sánh công bằng
        2. Downscale về max_width (mặc định 520px — thu nhỏ cả ảnh 1280px lẫn 640px)
        3. Tăng tương phản CLAHE
        4. Nén JPEG ở mức jpeg_quality
        5. Ước tính token theo diện tích pixel (width × height) / 750
    """
    # Kích thước JPEG gốc (Q=95) trước khi tối ưu để so sánh công bằng JPEG vs JPEG
    orig_jpeg_bytes = encode_jpeg(image, quality=95)
    original_size_kb = len(orig_jpeg_bytes) / 1024.0
    orig_h, orig_w = image.shape[:2]
    original_tokens = estimate_tokens_from_image(orig_jpeg_bytes, width=orig_w, height=orig_h)

    # Bước 1: Thu nhỏ
    img = downscale(image, max_width)

    # Bước 2: Tăng tương phản
    img = enhance_contrast(img)

    # Bước 3: Nén JPEG
    image_bytes = encode_jpeg(img, jpeg_quality)

    # Bước 4: Thống kê công bằng (JPEG gốc Q95 vs JPEG đã tối ưu)
    optimized_size_kb = len(image_bytes) / 1024.0
    reduction_pct = (1.0 - optimized_size_kb / max(0.1, original_size_kb)) * 100.0
    h, w = img.shape[:2]
    estimated_tokens = estimate_tokens_from_image(image_bytes, width=w, height=h)

    return {
        "image_bytes":       image_bytes,
        "estimated_tokens":  estimated_tokens,
        "original_tokens":   original_tokens,
        "original_size_kb":  round(original_size_kb, 1),
        "optimized_size_kb": round(optimized_size_kb, 1),
        "reduction_pct":     round(reduction_pct, 1),
        "final_resolution":  (w, h),
    }
