import cv2
import numpy as np

def order_points(pts):
    """
    Sắp xếp 4 tọa độ góc theo thứ tự chuẩn:
    [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
    """
    rect = np.zeros((4, 2), dtype="float32")
    pts = np.array(pts, dtype="float32")

    # Điểm Top-Left có tổng (x + y) nhỏ nhất, Bottom-Right có tổng (x + y) lớn nhất
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Điểm Top-Right có hiệu (x - y) lớn nhất, Bottom-Left có hiệu (x - y) nhỏ nhất
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def four_point_transform(image, pts):
    """
    Thực hiện phép biến đổi phối cảnh Perspective Transform để duỗi thẳng trang giấy
    dựa trên 4 điểm góc đã sắp xếp.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Tính chiều rộng lớn nhất của trang vở
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = max(int(width_a), int(width_b))

    # Tính chiều cao lớn nhất của trang vở
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = max(int(height_a), int(height_b))

    # Giới hạn kích thước tối thiểu để tránh lỗi crash
    max_w = max(max_w, 100)
    max_h = max(max_h, 100)

    # Tọa độ 4 góc đích sau khi duỗi phẳng (Top-Left=(0,0), Top-Right=(W,0), ...)
    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")

    # Tính ma trận chuyển đổi và warp
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_w, max_h))
    return warped, (max_w, max_h)

def _is_valid_page_quad(pts: np.ndarray, h: int, w: int, gray: np.ndarray) -> bool:
    """
    Kiểm tra hình học & độ sáng nghiêm ngặt để phân biệt trang sách/vở thật
    với tường nhà, trần nhà hoặc bóng đèn tuýp:
      1. Không chạm sát toàn bộ viền khung hình camera (loại bỏ nền tường).
      2. Tỷ lệ khung hình (Aspect Ratio) nằm trong khoảng trang sách [0.45, 2.2] (loại bỏ bóng đèn dài).
      3. Các góc trong của tứ giác gần 90 độ (55° – 125°).
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # 1. Đếm số đỉnh chạm sát mép camera (< 8px)
    margin = 8
    border_touches = 0
    for (px, py) in rect:
        if px <= margin or py <= margin or px >= (w - margin) or py >= (h - margin):
            border_touches += 1
    if border_touches >= 2:
        return False

    # 2. Kiểm tra kích thước và tỷ lệ dài/rộng (Aspect Ratio)
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)

    max_w = max(width_a, width_b)
    min_w = min(width_a, width_b)
    max_h = max(height_a, height_b)
    min_h = min(height_a, height_b)

    if min_w < 60 or min_h < 60:
        return False

    # Các cạnh đối diện không được chênh lệch quá 2.2 lần (loại bỏ hình thang méo dị dạng)
    if (max_w / max(1.0, min_w)) > 2.2 or (max_h / max(1.0, min_h)) > 2.2:
        return False

    aspect_ratio = max_w / max(1.0, max_h)
    if not (0.45 <= aspect_ratio <= 2.2):
        return False

    # 3. Kiểm tra góc giữa các cạnh kề (gần vuông góc: |cos(theta)| < 0.5)
    for i in range(4):
        p0 = rect[i]
        p1 = rect[(i + 1) % 4]
        p2 = rect[(i + 2) % 4]
        v1 = p0 - p1
        v2 = p2 - p1
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        if norm < 1e-5:
            return False
        cos_angle = abs(np.dot(v1, v2) / norm)
        if cos_angle > 0.50:
            return False

    return True


def detect_page_contour(image):
    """
    Phát hiện trang sách/vở trong khung hình và trích xuất 4 góc:
    1. Grayscale + GaussianBlur khử nhiễu
    2. Canny đa ngưỡng tìm cạnh sắc nét của trang giấy
    3. Tìm Contours khép kín (chiếm 8% -> 75% khung hình)
    4. approxPolyDP xấp xỉ tứ giác 4 đỉnh + kiểm tra hình học chống bắt nhầm tường/đèn
    """
    if image is None or image.size == 0:
        return None, None

    h, w = image.shape[:2]
    frame_area = h * w
    min_area = frame_area * 0.08
    max_area = frame_area * 0.75

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    candidate_contours = []

    # Dùng Canny tìm viền cạnh thực của trang sách/vở
    for low, high in [(35, 110), (50, 150)]:
        edged = cv2.Canny(blurred, low, high)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel, iterations=2)
        cnts, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if min_area <= area <= max_area:
                candidate_contours.append(c)

    if not candidate_contours:
        return None, None

    # Lọc lấy các contour lớn nhất
    candidate_contours = sorted(candidate_contours, key=cv2.contourArea, reverse=True)[:10]

    page_corners = None
    for c in candidate_contours:
        peri = cv2.arcLength(c, True)
        for eps in [0.02, 0.03, 0.04, 0.05]:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                pts = approx.reshape(4, 2).astype("float32")
                if _is_valid_page_quad(pts, h, w, gray):
                    page_corners = pts
                    break
        if page_corners is not None:
            break

    if page_corners is not None:
        warped, size = four_point_transform(image, page_corners)
        return page_corners, warped

    return None, None
