# Tầng route: đăng nhập, đăng xuất và đổi refresh token quản trị.
from fastapi import APIRouter

from app.api.dependencies import Admin, Connection
from app.common.response import response
from app.schemas.auth import LoginPayload, RefreshPayload, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginPayload, connection: Connection):
    return response(auth_service.login(connection, payload.username, payload.password.get_secret_value()))


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshPayload, connection: Connection):
    return response(auth_service.refresh(connection, payload.refresh_token))


@router.post("/logout")
def logout(connection: Connection, admin: Admin):
    return response(auth_service.logout(connection, admin["session_id"]))
