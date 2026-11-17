# Tầng dùng chung: biểu diễn lỗi nghiệp vụ độc lập với FastAPI.
class BusinessError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def require_found(value):
    if value is None:
        raise BusinessError("not_found", "Không tìm thấy bản ghi")
    return value
