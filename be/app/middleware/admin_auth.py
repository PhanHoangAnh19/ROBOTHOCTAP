# Tầng middleware: kiểm tra bearer JWT qua service, dùng dependency cho route quản trị.
from app.common.exceptions import BusinessError
from app.services import auth_service


def verify_admin(connection, credentials):
    if credentials is None:
        raise BusinessError("unauthorized", "Thiếu JWT quản trị")
    session, _ = auth_service.authenticate(connection, credentials.credentials)
    return session
