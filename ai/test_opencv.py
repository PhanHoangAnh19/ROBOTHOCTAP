
import cv2
import numpy as np

# Tạo một ảnh màu kích thước 640 x 480
image = np.zeros((480, 640, 3), dtype=np.uint8)

# Vẽ hình chữ nhật màu xanh lá
cv2.rectangle(
    image,
    (100, 100),
    (300, 300),
    (0, 255, 0),
    3
)

# Ghi chữ lên ảnh
cv2.putText(
    image,
    "Camera AI Test",
    (100, 80),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (255, 255, 255),
    2
)

# Lưu ảnh kết quả
cv2.imwrite("data/test_result.jpg", image)

print("OpenCV hoat dong thanh cong!")
print("Kich thuoc anh:", image.shape)
