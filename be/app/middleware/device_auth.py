# Tầng middleware: kiểm tra bearer token robot cho API sự kiện có phiên bản.
from app.common.exceptions import BusinessError
from app.services import device_service


def verify_device(connection, credentials):
    if credentials is None:
        raise BusinessError("unauthorized", "Thiếu token robot")
    return device_service.authenticate(connection, credentials.credentials)
