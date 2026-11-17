# Tầng kiểm thử: chạy trên PostgreSQL thật, rollback mọi dữ liệu của từng test.
from pathlib import Path
import secrets
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.dependencies import get_connection
from app.db.pool import get_pool
from app.main import app
from app.services.auth_service import seed_admin


@pytest.fixture(scope="session")
def running_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db(running_client):
    with get_pool().connection() as connection:
        with connection.transaction(force_rollback=True):
            yield connection


@pytest.fixture
def client(running_client, db):
    def connection_override():
        yield db

    app.dependency_overrides[get_connection] = connection_override
    try:
        yield running_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def admin(client, db):
    username = "test_" + secrets.token_hex(8)
    password = secrets.token_urlsafe(24)
    seed_admin(db, username, password)
    result = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert result.status_code == 200, result.text
    tokens = result.json()
    return {"Authorization": "Bearer " + tokens["access_token"]}, tokens
