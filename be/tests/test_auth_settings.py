# Tầng kiểm thử: auth login/refresh/logout và settings GET/PUT của Long.
import os
import secrets
from unittest.mock import patch

import pytest


def test_login_correct_password(client, db, admin):
    """Login đúng mật khẩu trả access_token và refresh_token."""
    headers, tokens = admin
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    """Login sai mật khẩu trả 401."""
    from app.services.auth_service import seed_admin

    username = "wrong_" + secrets.token_hex(8)
    seed_admin(db, username, secrets.token_urlsafe(24))
    result = client.post("/api/v1/auth/login", json={"username": username, "password": "sai_mat_khau"})
    assert result.status_code == 401


def test_login_nonexistent_user(client, db):
    """Login tài khoản không tồn tại trả 401 với thông báo chung."""
    result = client.post("/api/v1/auth/login", json={"username": "khong_ton_tai_" + secrets.token_hex(8), "password": "abc12345"})
    assert result.status_code == 401


def test_refresh_rotation(client, db, admin):
    """Refresh token xoay vòng: token cũ dùng lại trả 401."""
    _, tokens = admin
    old_refresh = tokens["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_tokens = rotated.json()
    assert new_tokens["refresh_token"] != old_refresh
    # Dùng lại refresh token cũ phải bị từ chối
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401


def test_logout_blocks_access_token(client, db, admin):
    """Logout thu hồi phiên, access token cũ bị chặn."""
    headers, tokens = admin
    # Trước logout: access token hoạt động
    assert client.get("/api/v1/settings", headers=headers).status_code == 200
    # Logout
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    # Sau logout: access token cũ bị chặn
    assert client.get("/api/v1/settings", headers=headers).status_code == 401


def test_get_settings(client, db, admin):
    """GET /api/v1/settings trả 3 khóa mặc định."""
    headers, _ = admin
    result = client.get("/api/v1/settings", headers=headers)
    assert result.status_code == 200
    body = result.json()
    assert body["posture_bad_threshold_seconds"] == 10
    assert body["reminder_cooldown_seconds"] == 120
    assert body["debounce_seconds"] == 2


def test_put_settings_update(client, db, admin):
    """PUT /api/v1/settings đổi giá trị, GET lại thấy giá trị mới."""
    headers, _ = admin
    result = client.put("/api/v1/settings", headers=headers, json={"reminder_cooldown_seconds": 60})
    assert result.status_code == 200
    assert result.json()["reminder_cooldown_seconds"] == 60
    # GET lại xác nhận
    get_result = client.get("/api/v1/settings", headers=headers)
    assert get_result.json()["reminder_cooldown_seconds"] == 60


def test_put_settings_unknown_key_422(client, db, admin):
    """PUT /api/v1/settings với khóa lạ trả 422."""
    headers, _ = admin
    result = client.put("/api/v1/settings", headers=headers, json={"unknown_key": 42})
    assert result.status_code == 422


def test_put_settings_negative_value_422(client, db, admin):
    """PUT /api/v1/settings với giá trị không phải số nguyên dương trả 422."""
    headers, _ = admin
    result = client.put("/api/v1/settings", headers=headers, json={"debounce_seconds": -1})
    assert result.status_code == 422
    result_zero = client.put("/api/v1/settings", headers=headers, json={"debounce_seconds": 0})
    assert result_zero.status_code == 422


def test_settings_requires_auth(client, db):
    """GET/PUT /api/v1/settings thiếu JWT trả 401."""
    assert client.get("/api/v1/settings").status_code == 401
    assert client.put("/api/v1/settings", json={"debounce_seconds": 5}).status_code == 401


def test_jwt_secret_unavailable_returns_503(client, db):
    """Khi JWT_SECRET quá ngắn, auth trả 503."""
    from app.config import Settings

    short_settings = Settings(
        database_url="postgresql://x:x@localhost/x",
        jwt_secret="short",
    )
    with patch("app.services.auth_service.get_settings", return_value=short_settings):
        result = client.post("/api/v1/auth/login", json={"username": "admin", "password": "12345678"})
    assert result.status_code == 503

