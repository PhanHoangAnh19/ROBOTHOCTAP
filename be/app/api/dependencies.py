# Tầng API: cấp connection theo request, phân trang và danh tính đã xác thực.
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.pagination import Pagination
from app.db.pool import get_pool
from app.middleware.admin_auth import verify_admin
from app.middleware.device_auth import verify_device

bearer = HTTPBearer(auto_error=False)


def get_connection():
    with get_pool().connection() as connection:
        yield connection


# Hoàn tất commit/rollback trước khi gửi phản hồi thành công cho client.
Connection = Annotated[object, Depends(get_connection, scope="function")]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def get_current_admin(connection: Connection, credentials: Credentials):
    return verify_admin(connection, credentials)


def get_current_device(connection: Connection, credentials: Credentials):
    return verify_device(connection, credentials)


def get_pagination(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    return Pagination(limit, offset)


Admin = Annotated[dict, Depends(get_current_admin)]
Page = Annotated[Pagination, Depends(get_pagination)]
