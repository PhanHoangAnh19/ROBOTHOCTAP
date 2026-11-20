# Tầng dùng chung: chuyển schema thành JSON và bảo toàn cấu trúc API cũ.
from fastapi.encoders import jsonable_encoder


def response(data):
    return jsonable_encoder(data)
