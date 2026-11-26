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

    # Điểm Top-Right có hiệu (y - x) nhỏ nhất, Bottom-Left có hiệu (y - x) lớn nhất
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

    # Tọa độ 4 góc đích sau khi duỗi phẳng
    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_w, max_h))
    return warped, (max_w, max_h)


def detect_page_contour(image):
    """
    Phát hiện trang sách/vở thông minh kết hợp 2 chiến lược:
      - Chiến lược A (Paper + Ink Content Grouping): Tìm nền giấy sáng màu có chứa
        chữ viết/hình vẽ/dòng kẻ (Blackhat morphology), loại trừ da người (mặt/tay) và đèn trần.
        Bắt được sách cực nhạy kể cả khi tay cầm che mất góc hoặc gáy sách hơi cong!
      - Chiến lược B (Canny Quad + Convex Hull): Bắt tờ giấy phẳng 4 góc rõ nét.
    """
    if image is None or image.size == 0:
        return None, None

    h, w = image.shape[:2]
    frame_area = h * w
    min_area = frame_area * 0.05
    max_area = frame_area * 0.82

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 1. Tạo mặt nạ da người (mặt, cổ, tay) để không bao giờ nhận nhầm mặt người là trang sách
    skin_hsv = cv2.inRange(hsv, np.array([0, 25, 50], dtype=np.uint8), np.array([25, 255, 255], dtype=np.uint8))
    skin_ycrcb = cv2.inRange(ycrcb, np.array([0, 133, 77], dtype=np.uint8), np.array([255, 173, 127], dtype=np.uint8))
    skin_mask = cv2.bitwise_and(skin_hsv, skin_ycrcb)
    skin_mask = cv2.dilate(skin_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)), iterations=1)

    # 2. Mặt nạ nền giấy sáng màu (loại bỏ áo tối màu, tóc, da người và bóng đèn chói lóa 255)
    paper_mask = cv2.inRange(hsv, np.array([0, 0, 95], dtype=np.uint8), np.array([180, 72, 246], dtype=np.uint8))
    paper_mask = cv2.bitwise_and(paper_mask, cv2.bitwise_not(skin_mask))

    # 3. Mặt nạ nét chữ / hình vẽ / kẻ ô ly bên trong trang sách (Blackhat morphology)
    kernel_bh = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel_bh)
    _, ink_mask = cv2.threshold(blackhat, 16, 255, cv2.THRESH_BINARY)
    ink_mask = cv2.bitwise_and(ink_mask, cv2.bitwise_not(skin_mask))

    paper_dil = cv2.dilate(paper_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)), iterations=1)
    ink_on_paper = cv2.bitwise_and(ink_mask, paper_dil)

    candidates = []  # list of (hull, is_strict_canny_quad)

    # Chiến lược A: Gom cụm vùng giấy có chứa nét chữ/hình vẽ (bắt nhạy khi cầm sách trên tay)
    ink_grouped = cv2.dilate(ink_on_paper, cv2.getStructuringElement(cv2.MORPH_RECT, (43, 43)), iterations=2)
    page_blob = cv2.bitwise_and(ink_grouped, paper_dil)
    page_blob = cv2.morphologyEx(page_blob, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (23, 23)), iterations=2)
    cnts_b, _ = cv2.findContours(page_blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts_b:
        hull = cv2.convexHull(c)
        area = cv2.contourArea(hull)
        if min_area <= area <= max_area:
            candidates.append((hull, False))

    # Chiến lược B: Canny đa ngưỡng + Convex Hull
    for low, high in [(20, 70), (35, 110)]:
        edged = cv2.Canny(blurred, low, high)
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=2)
        cnts, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            hull = cv2.convexHull(c)
            area = cv2.contourArea(hull)
            if min_area <= area <= max_area:
                candidates.append((hull, True))

    if not candidates:
        return None, None

    # Ưu tiên ứng viên có diện tích lớn nhất (cả trang sách thay vì 1 khung nhỏ)
    candidates = sorted(candidates, key=lambda item: cv2.contourArea(item[0]), reverse=True)[:12]

    best_corners = None
    for hull, is_canny in candidates:
        peri = cv2.arcLength(hull, True)
        pts = None
        exact_quad = False
        for eps in [0.02, 0.03, 0.04, 0.06]:
            approx = cv2.approxPolyDP(hull, eps * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                pts = approx.reshape(4, 2).astype("float32")
                exact_quad = True
                break
        if pts is None:
            rect = cv2.minAreaRect(hull)
            pts = np.asarray(cv2.boxPoints(rect), dtype=np.float32)

        rect_ord = order_points(pts)
        rect_ord[:, 0] = np.clip(rect_ord[:, 0], 0, w - 1)
        rect_ord[:, 1] = np.clip(rect_ord[:, 1], 0, h - 1)

        (tl, tr, br, bl) = rect_ord
        w_a = np.linalg.norm(br - bl)
        w_b = np.linalg.norm(tr - tl)
        h_a = np.linalg.norm(tr - br)
        h_b = np.linalg.norm(tl - bl)
        max_w, min_w = max(w_a, w_b), min(w_a, w_b)
        max_h, min_h = max(h_a, h_b), min(h_a, h_b)

        if min_w < 70 or min_h < 70:
            continue
        aspect = max_w / max(1.0, max_h)
        if not (0.40 <= aspect <= 2.4):
            continue
        if (max_w / max(1.0, min_w)) > 2.3 or (max_h / max(1.0, min_h)) > 2.3:
            continue

        # Không được chạm cả 4 góc khung hình camera (loại bỏ nền tường toàn khung)
        margin = 6
        touches = sum(1 for (px, py) in rect_ord if px <= margin or py <= margin or px >= (w - margin) or py >= (h - margin))
        if touches >= 4:
            continue

        # Kiểm tra mật độ giấy, da người & nét chữ bên trong tứ giác
        quad_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(quad_mask, np.int32(rect_ord), 255)
        quad_pixels = max(1, cv2.countNonZero(quad_mask))

        paper_in_quad = cv2.countNonZero(cv2.bitwise_and(paper_mask, quad_mask)) / quad_pixels
        ink_in_quad = cv2.countNonZero(cv2.bitwise_and(ink_on_paper, quad_mask)) / quad_pixels
        skin_in_quad = cv2.countNonZero(cv2.bitwise_and(skin_mask, quad_mask)) / quad_pixels

        if skin_in_quad >= 0.25:
            continue

        # Điều kiện 1: Trang sách có chữ/hình vẽ/ô ly bên trong (kể cả khi cầm tay che góc)
        if paper_in_quad >= 0.42 and ink_in_quad >= 0.015:
            best_corners = rect_ord
            break

        # Điều kiện 2: Tờ giấy trắng tinh nằm trọn vẹn 4 góc trong khung hình (touches <= 1)
        if exact_quad and is_canny and touches <= 1 and paper_in_quad >= 0.65:
            best_corners = rect_ord
            break

    if best_corners is not None:
        warped, size = four_point_transform(image, best_corners)
        return best_corners, warped

    return None, None
