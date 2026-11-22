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
    2. Canny Edge Detection + Dilate kết nối các nét đứt
    3. Tìm Contours và lọc diện tích lớn nhất (chiếm > 12% khung hình)
    4. approxPolyDP xấp xỉ đa giác 4 đỉnh
    """
    h, w = image.shape[:2]
    min_area = (h * w) * 0.12  # Cuốn vở phải chiếm ít nhất 12% màn hình

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Dùng Canny để tìm các cạnh rõ ràng của trang giấy
    edged = cv2.Canny(blurred, 40, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edged, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None

    # Lấy các contour lớn nhất
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    page_corners = None

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.03 * peri, True)

        # Nếu xấp xỉ được chính xác 4 đỉnh
        if len(approx) == 4:
            page_corners = approx.reshape(4, 2)
            break

    # Nếu không tìm thấy tứ giác hoàn hảo, dùng minAreaRect làm phương án dự phòng (fallback)
    if page_corners is None and len(contours) > 0 and cv2.contourArea(contours[0]) >= min_area:
        rect = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rect)
        page_corners = np.int0(box)

    if page_corners is not None:
        warped, size = four_point_transform(image, page_corners)
        return page_corners, warped

    return None, None
