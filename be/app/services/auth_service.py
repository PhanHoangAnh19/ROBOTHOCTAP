# Tầng service: đăng nhập JWT, xoay refresh token và thu hồi phiên quản trị.
import secrets
from datetime import timedelta

import jwt

from app.common.exceptions import BusinessError
from app.common.timeutil import utc_now
from app.config import get_settings
from app.platform.crypto import hash_password, token_hash, verify_password
from app.repositories import admin_user_repository as repository


def _secret():
    secret = get_settings().jwt_secret.get_secret_value()
    if len(secret) < 32:
        raise BusinessError("unavailable", "Cần JWT_SECRET có ít nhất 32 ký tự")
    return secret


def _tokens(account_id, session_id, refresh_id, expires_at):
    now = utc_now()
    common = {"sub": str(account_id), "sid": session_id, "iat": now}
    return {
        "access_token": jwt.encode({**common, "type": "access", "exp": now + timedelta(
            minutes=get_settings().access_token_minutes)}, _secret(), algorithm="HS256"),
        "refresh_token": jwt.encode({**common, "type": "refresh", "jti": refresh_id,
                                     "exp": expires_at}, _secret(), algorithm="HS256"),
        "token_type": "bearer",
    }


def seed_admin(connection, username, password):
    if repository.find_by_username(connection, username):
        raise BusinessError("conflict", "Tài khoản đã tồn tại")
    if not username or len(password) < 8:
        raise BusinessError("invalid", "Tên không được trống, mật khẩu phải có ít nhất 8 ký tự")
    return repository.insert(connection, username, hash_password(password))


def login(connection, username, password):
    _secret()
    admin = repository.find_by_username(connection, username)
    if not admin or not admin["is_active"] or not verify_password(password, admin["hashed_password"]):
        raise BusinessError("unauthorized", "Thông tin đăng nhập không hợp lệ")
    refresh_id = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(days=get_settings().refresh_token_days)
    session_id = repository.create_session(connection, admin["account_id"], token_hash(refresh_id), expires_at)
    return _tokens(admin["account_id"], session_id, refresh_id, expires_at)


def authenticate(connection, token, token_type="access"):
    try:
        claims = jwt.decode(token, _secret(), algorithms=["HS256"],
                            options={"require": ["exp", "iat", "sub", "sid", "type"]})
        if claims["type"] != token_type:
            raise ValueError()
        session = repository.session(connection, int(claims["sid"]))
        if (not session or session["is_revoked"] or not session["is_active"]
                or session["expires_at"] <= utc_now() or str(session["account_id"]) != claims["sub"]):
            raise ValueError()
        if token_type == "refresh" and token_hash(claims["jti"]) != session["refresh_token_digest"]:
            raise ValueError()
        return session, claims
    except (jwt.PyJWTError, ValueError, KeyError, TypeError, OverflowError):
        raise BusinessError("unauthorized", "Token không hợp lệ hoặc đã hết hạn") from None


def refresh(connection, token):
    session, claims = authenticate(connection, token, "refresh")
    refresh_id = secrets.token_urlsafe(32)
    rotated = repository.rotate(connection, session["session_id"], token_hash(claims["jti"]), token_hash(refresh_id))
    if not rotated:
        raise BusinessError("unauthorized", "Refresh token đã được sử dụng")
    return _tokens(session["account_id"], session["session_id"], refresh_id, session["expires_at"])


def logout(connection, session_id):
    repository.revoke(connection, session_id)
    return {"status": "ok"}
