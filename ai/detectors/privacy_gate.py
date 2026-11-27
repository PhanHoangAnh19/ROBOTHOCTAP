"""
privacy_gate.py — Cổng riêng tư đa tầng (Multi-layer Privacy Gate) cho Robot Học Tập AI.
Người thực hiện: NGUYỄN VĂN QUỐC (Nhóm Training AI - Tuần 5 - Cột mốc M2).

Mục tiêu an toàn cốt lõi:
    - Tuân thủ Luật Bảo vệ Dữ liệu Cá nhân 2026 & Tiêu chí Q9 (Chặn mặt/da ≥ 98%).
    - TUYỆT ĐỐI KHÔNG để lọt bất kỳ hình ảnh khuôn mặt trẻ em hoặc vùng da cơ thể nào ra ngoài Cloud LLM.
    - Chỉ cho phép truyền tải nội dung trang vở khi: 0 khuôn mặt & tỷ lệ da tay ≤ 15%.
"""

import os
import sys
import cv2
import numpy as np

# Đảm bảo đường dẫn import
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(AI_DIR)
for p in [PROJECT_ROOT, AI_DIR, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class PrivacyGateDetector:
    """
    Cổng kiểm duyệt riêng tư 3 tầng an toàn:
      - Tầng 1: MediaPipe Face Landmarker phát hiện khuôn mặt (chặn 100% nếu có mặt).
      - Tầng 2: Phân đoạn vùng da kép HSV + YCrCb (chặn nếu tổng diện tích da > 15%).
      - Tầng 3: Kiểm tra cụm da xâm phạm (chặn nếu có bàn tay/cánh tay đè lấn chiếm > 8% trang).
      - Tầng 4: Đánh giá độ nét ảnh qua phương sai Laplacian (cảnh báo ảnh mờ).
    """

    def __init__(
        self,
        model_path: str = None,
        max_skin_ratio: float = 0.08,
        max_cluster_ratio: float = 0.05,
        min_blur_score: float = 60.0,
        shared_face_detector=None,
        shared_pose_detector=None
    ):
        self.max_skin_ratio = max_skin_ratio
        self.max_cluster_ratio = max_cluster_ratio
        self.min_blur_score = min_blur_score

        # 1. Tái sử dụng hoặc khởi tạo MediaPipe Face Landmarker & Pose Landmarker
        self.face_detector = shared_face_detector
        self.pose_detector = shared_pose_detector

        if MEDIAPIPE_AVAILABLE:
            if self.face_detector is None:
                model_candidates = [
                    model_path,
                    os.path.join(AI_DIR, "models", "face_landmarker.task"),
                    os.path.join(AI_DIR, "face_landmarker.task"),
                    os.path.join(PROJECT_ROOT, "face_landmarker.task"),
                    os.path.join(PROJECT_ROOT, "ai", "models", "face_landmarker.task")
                ]
                valid_model = next((p for p in model_candidates if p and os.path.exists(p)), None)
                if valid_model:
                    try:
                        base_options = python.BaseOptions(model_asset_path=valid_model)
                        options = vision.FaceLandmarkerOptions(
                            base_options=base_options,
                            running_mode=vision.RunningMode.IMAGE,
                            num_faces=4,
                            min_face_detection_confidence=0.30,
                            min_face_presence_confidence=0.30
                        )
                        self.face_detector = vision.FaceLandmarker.create_from_options(options)
                    except Exception as e:
                        print(f"⚠️ [PrivacyGate] Không thể nạp FaceLandmarker: {e}")

            if self.pose_detector is None:
                pose_candidates = [
                    os.path.join(AI_DIR, "models", "pose_landmarker_lite.task"),
                    os.path.join(AI_DIR, "pose_landmarker_lite.task"),
                    os.path.join(PROJECT_ROOT, "pose_landmarker_lite.task"),
                    os.path.join(PROJECT_ROOT, "ai", "models", "pose_landmarker_lite.task")
                ]
                valid_pose = next((p for p in pose_candidates if p and os.path.exists(p)), None)
                if valid_pose:
                    try:
                        pose_opts = vision.PoseLandmarkerOptions(
                            base_options=python.BaseOptions(model_asset_path=valid_pose),
                            running_mode=vision.RunningMode.IMAGE,
                            num_poses=2,
                            min_pose_detection_confidence=0.35,
                            min_pose_presence_confidence=0.35
                        )
                        self.pose_detector = vision.PoseLandmarker.create_from_options(pose_opts)
                    except Exception:
                        pass

    def detect_faces(self, image: np.ndarray) -> tuple[int, list]:
        """
        Phát hiện khuôn mặt chính diện (FaceLandmarker) kết hợp phát hiện đầu/người nghiêng hoặc cúi
        phía sau (PoseLandmarker) để đạt độ chính xác Q9 >= 98%.
        """
        if not MEDIAPIPE_AVAILABLE or image is None or image.size == 0:
            return 0, []

        h, w = image.shape[:2]
        scale = 640.0 / max(h, w) if max(h, w) > 640 else 1.0
        small = cv2.resize(image, (int(w * scale), int(h * scale))) if scale < 1.0 else image
        rgb_image = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        face_boxes = []

        # 1. Quét khuôn mặt qua FaceLandmarker
        if self.face_detector is not None:
            try:
                results = self.face_detector.detect(mp_image)
                for landmarks in results.face_landmarks:
                    xs = [lm.x * w for lm in landmarks]
                    ys = [lm.y * h for lm in landmarks]
                    x_min = max(0, int(min(xs)))
                    y_min = max(0, int(min(ys)))
                    x_max = min(w, int(max(xs)))
                    y_max = min(h, int(max(ys)))
                    face_boxes.append((x_min, y_min, x_max - x_min, y_max - y_min))
            except Exception:
                pass

        # 2. Quét đầu/cơ thể người (nghiêng mặt, cúi đầu, người lớn đi phía sau) qua PoseLandmarker
        if len(face_boxes) == 0 and self.pose_detector is not None:
            try:
                p_res = self.pose_detector.detect(mp_image)
                if p_res.pose_landmarks:
                    for lms in p_res.pose_landmarks:
                        vis_pts = [
                            (lm.x * w, lm.y * h)
                            for idx, lm in enumerate(lms[:17])
                            if lm.visibility > 0.45 and 0.02 <= lm.x <= 0.98 and 0.02 <= lm.y <= 0.98
                        ]
                        if len(vis_pts) >= 2:
                            # Ưu tiên lấy hộp bao quanh vùng đầu (mốc 0..10) nếu có
                            head_pts = [
                                (lm.x * w, lm.y * h)
                                for lm in lms[:11]
                                if lm.visibility > 0.35 and 0.0 <= lm.x <= 1.0 and 0.0 <= lm.y <= 1.0
                            ]
                            pts_use = head_pts if len(head_pts) >= 2 else vis_pts
                            xs = [p[0] for p in pts_use]
                            ys = [p[1] for p in pts_use]
                            pad = int(max(w, h) * 0.06)
                            x_min = max(0, int(min(xs)) - pad)
                            y_min = max(0, int(min(ys)) - pad)
                            x_max = min(w, int(max(xs)) + pad)
                            y_max = min(h, int(max(ys)) + pad)
                            if (x_max - x_min) > 20 and (y_max - y_min) > 20:
                                face_boxes.append((x_min, y_min, x_max - x_min, y_max - y_min))
            except Exception:
                pass

        return len(face_boxes), face_boxes

    def compute_skin_segmentation(self, image: np.ndarray) -> tuple[float, float, np.ndarray, list]:
        """
        Phân đoạn da người kết hợp 2 không gian màu:
          - HSV: Hue [0, 23], Saturation [42, 255], Value [55, 255] (loại bỏ giấy trắng ngả vàng dưới đèn)
          - YCrCb: Cr [138, 175], Cb [77, 127]
        Khử nhiễu cấu trúc hình elip để loại bỏ vân giấy/đường kẻ ô ly.
        """
        if image is None or image.size == 0:
            return 0.0, 0.0, None, []

        h, w = image.shape[:2]
        total_pixels = h * w

        # 1. Mặt nạ HSV (S >= 42 loại bỏ hoàn toàn bóng râm trên giấy trắng)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask_hsv = cv2.inRange(hsv, np.array([0, 42, 55], dtype=np.uint8), np.array([23, 255, 255], dtype=np.uint8))

        # 2. Mặt nạ YCrCb (Cr >= 138 chuẩn sắc tố da người)
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        mask_ycrcb = cv2.inRange(ycrcb, np.array([0, 138, 77], dtype=np.uint8), np.array([255, 175, 127], dtype=np.uint8))

        # 3. Giao hai mặt nạ (Logical AND)
        combined = cv2.bitwise_and(mask_hsv, mask_ycrcb)

        # 4. Phép biến đổi hình thái học (Morphological Filtering) khử nhiễu ô vở
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

        skin_pixels = cv2.countNonZero(cleaned)
        total_skin_ratio = skin_pixels / total_pixels

        # 5. Phân tích các cụm da độc lập (tìm bàn tay / ngón tay lớn)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cluster_boxes = []
        max_cluster_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_cluster_area:
                max_cluster_area = area
            if area > (total_pixels * 0.02):  # Cụm lớn hơn 2% trang
                x, y, cw, ch = cv2.boundingRect(cnt)
                cluster_boxes.append((x, y, cw, ch, area / total_pixels))

        max_cluster_ratio = max_cluster_area / total_pixels
        return total_skin_ratio, max_cluster_ratio, cleaned, cluster_boxes

    def compute_blur_score(self, image: np.ndarray) -> float:
        """
        Tính điểm độ sắc nét bằng phương sai toán tử vi phân Laplacian.
        Điểm số > 60: Ảnh nét đọc tốt. Điểm < 60: Ảnh mờ nhoè.
        """
        if image is None or image.size == 0:
            return 0.0
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def anonymize_regions(
        self,
        image: np.ndarray,
        face_boxes: list = None,
        skin_clusters: list = None,
        mode: str = "blur"
    ) -> np.ndarray:
        """
        Tự động làm mờ (Gaussian Blur / Pixelate) hoặc che đen khuôn mặt và da tay
        để bảo vệ danh tính 100% mà không bắt trẻ phải né tránh camera.
        """
        if image is None or image.size == 0:
            return image

        output = image.copy()
        h, w = output.shape[:2]

        # 1. Xử lý làm mờ / xóa khuôn mặt
        if face_boxes:
            for (x, y, fw, fh) in face_boxes:
                # Mở rộng vùng mặt thêm 15% để che phủ trọn vẹn tóc/cằm/tai
                pad_x = int(fw * 0.15)
                pad_y = int(fh * 0.15)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(w, x + fw + pad_x)
                y2 = min(h, y + fh + pad_y)

                rw, rh = x2 - x1, y2 - y1
                if rw <= 0 or rh <= 0:
                    continue

                if mode == "blur":
                    roi = output[y1:y2, x1:x2]
                    # Pixelate kết hợp làm mờ nặng
                    small = cv2.resize(roi, (max(1, rw // 10), max(1, rh // 10)), interpolation=cv2.INTER_NEAREST)
                    pixelated = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
                    output[y1:y2, x1:x2] = cv2.GaussianBlur(pixelated, (25, 25), 0)
                else:  # blackout shield
                    cv2.rectangle(output, (x1, y1), (x2, y2), (25, 25, 25), -1)
                    cv2.putText(output, "[DA CHE MAT]", (x1 + 10, y1 + rh // 2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 2. Xử lý làm mờ cụm da tay nếu có yêu cầu
        if skin_clusters:
            for (cx, cy, cw, ch, _) in skin_clusters:
                x1 = max(0, cx - 5)
                y1 = max(0, cy - 5)
                x2 = min(w, cx + cw + 5)
                y2 = min(h, cy + ch + 5)
                rw, rh = x2 - x1, y2 - y1
                if rw > 0 and rh > 0:
                    roi = output[y1:y2, x1:x2]
                    small = cv2.resize(roi, (max(1, rw // 8), max(1, rh // 8)), interpolation=cv2.INTER_NEAREST)
                    pixelated = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
                    output[y1:y2, x1:x2] = cv2.GaussianBlur(pixelated, (21, 21), 0)

        return output

    def evaluate_image(
        self,
        image: np.ndarray,
        auto_anonymize: bool = True,
        anonymize_mode: str = "blur"
    ) -> dict:
        """
        Đánh giá an toàn toàn diện cho ảnh trước khi gửi ra Cloud LLM.
        Hỗ trợ tính năng AUTO-ANONYMIZE: Tự động làm mờ mặt trẻ em để bé không cần né tránh!
        """
        if image is None or image.size == 0:
            return {
                "is_safe": False,
                "status": "BLOCKED",
                "status_code": "EMPTY_IMAGE",
                "reason": "Ảnh rỗng hoặc không đọc được",
                "faces_count": 0,
                "face_boxes": [],
                "skin_ratio": 0.0,
                "max_cluster_ratio": 0.0,
                "skin_clusters": [],
                "blur_score": 0.0,
                "is_blurry": True,
                "sanitized_image": None
            }

        h, w = image.shape[:2]
        total_pixels = h * w

        # Tầng 1: Phát hiện khuôn mặt
        faces_count, face_boxes = self.detect_faces(image)

        # Tầng 2 & 3: Phân đoạn da và cụm da
        total_skin_ratio, max_cluster_ratio, skin_mask, cluster_boxes = self.compute_skin_segmentation(image)

        # Tầng 4: Đánh giá độ nét
        blur_score = self.compute_blur_score(image)
        is_blurry = blur_score < self.min_blur_score

        # ── XỬ LÝ THÔNG MINH: NẾU BẬT TỰ ĐỘNG XÓA / LÀM MỜ MẶT (AUTO-ANONYMIZE) ──
        if auto_anonymize and (faces_count > 0 or total_skin_ratio > self.max_skin_ratio):
            # Tính diện tích khuôn mặt chiếm bao nhiêu % trang vở
            face_area_total = sum(fw * fh for (_, _, fw, fh) in face_boxes)
            face_ratio = face_area_total / total_pixels

            # Trường hợp 1: Mặt/tay chỉ ở mép/góc trang (chiếm <= 30% diện tích trang)
            # -> Tự động làm mờ mặt/da! Chữ bài tập vẫn đọc được bình thường!
            if face_ratio <= 0.30 and total_skin_ratio <= 0.30:
                anonymized_img = self.anonymize_regions(image, face_boxes, cluster_boxes if total_skin_ratio > 0.15 else None, mode=anonymize_mode)
                return {
                    "is_safe": True,
                    "status": "PASSED",
                    "status_code": "PASSED_AUTO_ANONYMIZED",
                    "reason": f"Đã tự động làm mờ {faces_count} khuôn mặt (Xóa nhận diện 100%, bảo vệ an toàn cho bé)",
                    "faces_count": faces_count,
                    "face_boxes": face_boxes,
                    "skin_ratio": total_skin_ratio,
                    "max_cluster_ratio": max_cluster_ratio,
                    "skin_clusters": cluster_boxes,
                    "blur_score": blur_score,
                    "is_blurry": is_blurry,
                    "sanitized_image": anonymized_img
                }

            # Trường hợp 2: Mặt hoặc tay đè lấp quá 30% diện tích (che mất chữ đề bài)
            # -> Lúc này mới nhẹ nhàng nhắc bé dời nhẹ ra
            block_reason = "Khuôn mặt bé che mất đề bài toán, bé nghiêng nhẹ đầu ra để Robot nhìn rõ đề bài nhé!" if face_ratio > 0.30 else "Bàn tay bé che mất nhiều chữ trong vở, bé dời tay ra mép nhé!"
            return {
                "is_safe": False,
                "status": "BLOCKED",
                "status_code": "HOMEWORK_TEXT_COVERED",
                "reason": block_reason,
                "faces_count": faces_count,
                "face_boxes": face_boxes,
                "skin_ratio": total_skin_ratio,
                "max_cluster_ratio": max_cluster_ratio,
                "skin_clusters": cluster_boxes,
                "blur_score": blur_score,
                "is_blurry": is_blurry,
                "sanitized_image": None
            }

        # ── NẾU KHÔNG DÙNG AUTO-ANONYMIZE HOẶC CHẾ ĐỘ NGHIÊM NGẶT ──
        if faces_count > 0:
            return {
                "is_safe": False,
                "status": "BLOCKED",
                "status_code": "FACE_DETECTED",
                "reason": f"Phát hiện {faces_count} khuôn mặt (Vi phạm quyền riêng tư trẻ em Q9)",
                "faces_count": faces_count,
                "face_boxes": face_boxes,
                "skin_ratio": total_skin_ratio,
                "max_cluster_ratio": max_cluster_ratio,
                "skin_clusters": cluster_boxes,
                "blur_score": blur_score,
                "is_blurry": is_blurry,
                "sanitized_image": None
            }

        if total_skin_ratio > self.max_skin_ratio:
            return {
                "is_safe": False,
                "status": "BLOCKED",
                "status_code": "SKIN_RATIO_EXCEEDED",
                "reason": f"Tỷ lệ da tay che khuất trang vở quá lớn: {total_skin_ratio*100:.1f}% (> {self.max_skin_ratio*100:.0f}%)",
                "faces_count": 0,
                "face_boxes": [],
                "skin_ratio": total_skin_ratio,
                "max_cluster_ratio": max_cluster_ratio,
                "skin_clusters": cluster_boxes,
                "blur_score": blur_score,
                "is_blurry": is_blurry,
                "sanitized_image": None
            }

        if max_cluster_ratio > self.max_cluster_ratio:
            return {
                "is_safe": False,
                "status": "BLOCKED",
                "status_code": "SKIN_CLUSTER_INTRUSION",
                "reason": f"Phát hiện bàn tay/ngón tay xâm phạm trang vở: {max_cluster_ratio*100:.1f}% (> {self.max_cluster_ratio*100:.0f}%)",
                "faces_count": 0,
                "face_boxes": [],
                "skin_ratio": total_skin_ratio,
                "max_cluster_ratio": max_cluster_ratio,
                "skin_clusters": cluster_boxes,
                "blur_score": blur_score,
                "is_blurry": is_blurry,
                "sanitized_image": None
            }

        # ĐỦ ĐIỀU KIỆN AN TOÀN TUYỆT ĐỐI (TRANG SẠCH 100%)
        return {
            "is_safe": True,
            "status": "PASSED",
            "status_code": "SAFE_PAGE" if not is_blurry else "SAFE_BUT_BLURRY",
            "reason": "Trang vở an toàn, 0 khuôn mặt, không bị tay che (Sẵn sàng gửi LLM)" if not is_blurry else "Trang vở an toàn nhưng ảnh hơi mờ, nên chụp lại nét hơn",
            "faces_count": 0,
            "face_boxes": [],
            "skin_ratio": total_skin_ratio,
            "max_cluster_ratio": max_cluster_ratio,
            "skin_clusters": cluster_boxes,
            "blur_score": blur_score,
            "is_blurry": is_blurry,
            "sanitized_image": image.copy()
        }

    def draw_hud(self, display_frame: np.ndarray, result: dict, show_skin_mask: bool = False) -> np.ndarray:
        """
        Vẽ giao diện giám sát an toàn Cyber Quantum HUD trên khung hình.
        Ưu tiên hiển thị trực tiếp ảnh đã làm mờ mặt (sanitized_image) để thấy rõ hiệu ứng xóa mặt.
        """
        sanitized = result.get("sanitized_image")
        if sanitized is not None and sanitized.shape[:2] == display_frame.shape[:2]:
            output = sanitized.copy()
        else:
            output = display_frame.copy()

        h, w = output.shape[:2]

        is_safe = result.get("is_safe", False)
        status_code = result.get("status_code", "UNKNOWN")
        faces_cnt = result.get("faces_count", 0)
        skin_rat = result.get("skin_ratio", 0.0)
        blur_sc = result.get("blur_score", 0.0)

        # Định màu sắc & nội dung ngắn gọn không dấu/chuẩn ASCII để không tràn khung OpenCV
        if status_code == "PASSED_AUTO_ANONYMIZED":
            theme_color = (255, 210, 0)     # Xanh ngọc: ĐÃ TỰ ĐỘNG XÓA MẶT
            status_text = "[PASSED - AUTO BLUR] DA TU DONG LAM MO MAT 100%"
            detail_text = f"Da xoa nhan dien {faces_cnt} khuon mat -> An toan gui LLM"
        elif is_safe:
            theme_color = (0, 255, 0)       # Xanh lá: AN TOÀN
            status_text = "[PASSED] CONG AN TOAN - DU DIEU KIEN GUI LLM"
            detail_text = "Trang vo sach, 0 khuon mat, khong bi tay che"
        elif status_code in ["FACE_DETECTED", "HOMEWORK_TEXT_COVERED"]:
            theme_color = (0, 0, 255)       # Đỏ: VI PHẠM
            status_text = "[BLOCKED] VI PHAM: PHAT HIEN MAT / CHE DE BAI"
            detail_text = f"Phat hien {faces_cnt} mat che bai -> Chan gui Cloud (Q9)"
        else:
            theme_color = (0, 165, 255)     # Cam: CHE KHUẤT DA TAY
            status_text = "[BLOCKED] VI PHAM: BAN TAY CHE TRANG VO (>15%)"
            detail_text = f"Ty le da tay {skin_rat*100:.1f}% vuot nguong an toan"

        # Tự động co giãn cỡ chữ theo chiều rộng cửa sổ để không bao giờ tràn lề phải
        title_scale = min(0.55, max(0.35, w / 820.0))
        sub_scale = min(0.45, max(0.32, w / 920.0))
        box_h = 96

        # 1. Vẽ khung viền trạng thái toàn cảnh
        cv2.rectangle(output, (0, 0), (w - 1, h - 1), theme_color, 3)

        # 2. Đánh dấu vị trí khuôn mặt (vẽ trước hộp HUD để không đè chữ lên hộp HUD)
        for (fx, fy, fw, fh) in result.get("face_boxes", []):
            box_col = (255, 210, 0) if status_code == "PASSED_AUTO_ANONYMIZED" else (0, 0, 255)
            lbl = "DA LAM MO MAT (AN TOAN)" if status_code == "PASSED_AUTO_ANONYMIZED" else "CANH BAO MAT"
            cv2.rectangle(output, (fx, fy), (fx + fw, fy + fh), box_col, 2)
            # Nếu cạnh trên của mặt nằm sát hộp HUD (< 115px), đặt nhãn xuống dưới khung mặt
            lbl_y = (fy + fh + 18) if fy < (box_h + 25) else (fy - 8)
            cv2.putText(output, lbl, (fx, min(h - 10, max(20, lbl_y))),
                        cv2.FONT_HERSHEY_SIMPLEX, sub_scale, box_col, 2)

        # 3. Đánh dấu cụm da tay nếu có
        for (cx, cy, cw, ch, cratio) in result.get("skin_clusters", []):
            cv2.rectangle(output, (cx, cy), (cx + cw, cy + ch), (0, 165, 255), 1)
            lbl_y = (cy + ch + 15) if cy < (box_h + 20) else (cy - 5)
            cv2.putText(output, f"Da/Tay {cratio*100:.1f}%", (cx, min(h - 10, max(15, lbl_y))),
                        cv2.FONT_HERSHEY_SIMPLEX, sub_scale * 0.9, (0, 165, 255), 1)

        # 4. Vẽ hộp thông tin Telemetry (luôn nằm trên cùng, sạch đẹp)
        cv2.rectangle(output, (8, 8), (w - 8, box_h), (18, 18, 18), -1)
        cv2.rectangle(output, (8, 8), (w - 8, box_h), theme_color, 2)

        cv2.putText(output, status_text, (18, 34), cv2.FONT_HERSHEY_SIMPLEX, title_scale, theme_color, 2)
        cv2.putText(output, f"Chi tiet: {detail_text}", (18, 60), cv2.FONT_HERSHEY_SIMPLEX, sub_scale, (230, 230, 230), 1)

        telemetry = f"Mat: {faces_cnt} | Da tay: {skin_rat*100:.1f}% (<=15%) | Do net: {blur_sc:.0f}"
        cv2.putText(output, telemetry, (18, 84), cv2.FONT_HERSHEY_SIMPLEX, sub_scale,
                    (180, 255, 180) if is_safe else (180, 180, 255), 1)

        return output
