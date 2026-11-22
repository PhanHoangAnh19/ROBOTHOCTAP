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

def detect_page_contour(image):
    """
    Phát hiện trang sách/vở trong khung hình và trích xuất 4 góc:
    1. Grayscale + GaussianBlur khử nhiễu
    2. Canny đa ngưỡng + Morphological Closing & Otsu threshold
    3. Tìm Contours và lọc diện tích lớn nhất (chiếm > 6% khung hình)
    4. approxPolyDP xấp xỉ đa giác 4 đỉnh (với fallback minAreaRect an toàn)
    """
    h, w = image.shape[:2]
    min_area = (h * w) * 0.06  # Ngưỡng diện tích linh hoạt để bắt nhạy khi đặt xa

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    candidate_contours = []

    # Chiến lược 1: Canny đa ngưỡng kết hợp nối liền viền
    for low, high in [(30, 90), (50, 150)]:
        edged = cv2.Canny(blurred, low, high)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edged, kernel, iterations=2)
        cnts, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            if cv2.contourArea(c) >= min_area:
                candidate_contours.append(c)

    # Chiến lược 2: Otsu thresholding cho giấy trắng trên nền bàn/áo tương phản
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel_o = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed_o = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel_o, iterations=2)
    cnts_o, _ = cv2.findContours(closed_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts_o:
        area = cv2.contourArea(c)
        if min_area <= area < (h * w * 0.95):
            candidate_contours.append(c)

    if not candidate_contours:
        return None, None

    # Lọc lấy các contour lớn nhất
    candidate_contours = sorted(candidate_contours, key=cv2.contourArea, reverse=True)[:8]

    page_corners = None
    for c in candidate_contours:
        peri = cv2.arcLength(c, True)
        for eps in [0.02, 0.03, 0.04, 0.05]:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                page_corners = approx.reshape(4, 2)
                break
        if page_corners is not None:
            break

    # Fallback nếu mép hơi cong hoặc bị tay đè: Dùng minAreaRect
    if page_corners is None and len(candidate_contours) > 0:
        rect = cv2.minAreaRect(candidate_contours[0])
        box = cv2.boxPoints(rect)
        page_corners = np.asarray(box, dtype=np.float32)

    if page_corners is not None:
        warped, size = four_point_transform(image, page_corners)
        return page_corners, warped

    return None, None
