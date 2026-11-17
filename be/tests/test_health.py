# Tầng kiểm thử: kiểm tra PostgreSQL, hợp đồng API cũ và việc từ chối dữ liệu ảnh.
from contextlib import nullcontext
import json
import re
import secrets
from types import SimpleNamespace

import pytest

from app.platform import ai_client


@pytest.mark.parametrize("body", [[], None, {"choices": [], "usage": None}])
def test_malformed_llm_response_is_handled(body, monkeypatch):
    result = SimpleNamespace(read=lambda: json.dumps(body).encode())
    monkeypatch.setattr(ai_client.urllib.request, "urlopen", lambda *args, **kwargs: nullcontext(result))
    monkeypatch.setattr(ai_client.time, "sleep", lambda seconds: None)
    with pytest.raises(ai_client.LLMError):
        ai_client.openai_completion("http://127.0.0.1/v1", secrets.token_urlsafe(32), "test", "Tutor", "Hello")


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    assert client.get("/api/v1/health").status_code == 200


@pytest.mark.parametrize("field", ["image", "base64", "file", "video", "unknown"])
@pytest.mark.parametrize("endpoint,payload", [
    ("/sensor-event", {"event_type": "TU_THE_CO", "detail": "Kiểm thử"}),
    ("/ask-ai", {"question": "1 + 1?"}),
])
def test_reject_unknown_fields(client, db, field, endpoint, payload):
    before = db.execute("SELECT COUNT(*) AS n FROM learning_events").fetchone()["n"]
    result = client.post(endpoint, json={**payload, field: "rejected"})
    assert result.status_code == 422
    assert any(error["type"] == "extra_forbidden" for error in result.json()["detail"])
    assert db.execute("SELECT COUNT(*) AS n FROM learning_events").fetchone()["n"] == before


def test_reject_non_text_and_multipart(client):
    assert client.post("/sensor-event", json={"event_type": "TU_THE_CO", "detail": {"image": "x"}}).status_code == 422
    assert client.post("/sensor-event", files={"file": ("test.txt", b"test")}).status_code == 422


def test_legacy_contract_and_summary(client, db, monkeypatch):
    def offline(*args, **kwargs):
        raise ai_client.LLMError("offline")

    monkeypatch.setattr("app.services.provider_service.answer", offline)
    for event_type in ("TU_THE_CO", "TU_THE_VAI", "KHOANG_CACH_MAT", "MAT_TAP_TRUNG", "CUSTOM"):
        result = client.post("/sensor-event", json={"event_type": event_type, "detail": "Kiểm thử ' SQL"})
        assert result.status_code == 200
        assert result.json() == {"status": "ok"}
    for mode in ("GIAI_TOAN", "DAY_HOC", "THAC_MAC", "CUSTOM_MODE"):
        result = client.post("/ask-ai", json={"question": "1 + 1?", "mode": mode})
        assert result.status_code == 200
        assert result.json() == {"answer": "[Chế độ Offline] Đã nhận câu hỏi '1 + 1?'. (Kiểm tra lại API Key để AI trả lời thực tế)."}
    client.post("/ask-ai", json={"question": "Mặc định"})
    result = client.get("/events")
    assert result.status_code == 200
    body = result.json()
    assert set(body) == {"summary", "events"}
    rows = body["events"]
    assert len(rows) <= 50
    assert [row["id"] for row in rows] == sorted([row["id"] for row in rows], reverse=True)
    for row in rows:
        assert set(row) == {"id", "timestamp", "event_type", "category_name", "detail", "duration_minutes"}
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", row["timestamp"])
    assert rows[0]["event_type"] == "GIAI_TOAN"
    assert rows[1]["event_type"] == "CUSTOM_MODE"
    assert rows[1]["category_name"] == "Giải Đáp Kiến Thức"
    assert rows[5]["category_name"] == "Cảnh báo Hệ Thống"
    assert body["summary"] == {
        "total_study_minutes": sum(row["duration_minutes"] for row in rows),
        "posture_warnings": sum(row["event_type"] in ("TU_THE_CO", "TU_THE_VAI", "KHOANG_CACH_MAT") for row in rows),
        "attention_warnings": sum(row["event_type"] == "MAT_TAP_TRUNG" for row in rows),
        "ai_interactions": sum(row["event_type"] in ("GIAI_TOAN", "DAY_HOC", "THAC_MAC") for row in rows),
    }


def test_fifty_event_window(client, db):
    for i in range(51):
        client.post("/sensor-event", json={"event_type": "MAT_TAP_TRUNG", "detail": str(i)})
    body = client.get("/events").json()
    assert len(body["events"]) == 50
    assert body["events"][0]["detail"] == "50"
    assert body["events"][-1]["detail"] == "1"
    assert body["summary"] == {"total_study_minutes": 0, "posture_warnings": 0,
                               "attention_warnings": 50, "ai_interactions": 0}


def test_admin_and_device_token_lifecycle(client, db, admin):
    headers, tokens = admin
    assert client.get("/api/v1/devices").status_code == 401
    created = client.post("/api/v1/devices", headers=headers, json={"name": "Robot thử"})
    assert created.status_code == 200
    device_id = created.json()["id"]
    assert client.get(f"/api/v1/devices/{device_id}", headers=headers).status_code == 200
    assert client.put(f"/api/v1/devices/{device_id}", headers=headers, json={"name": "Đã đổi"}).json()["name"] == "Đã đổi"
    token = client.post(f"/api/v1/devices/{device_id}/token", headers=headers).json()["token"]
    stored = db.execute(
        "SELECT access_token_digest FROM robots WHERE robot_id = %s", (device_id,),
    ).fetchone()["access_token_digest"]
    assert stored != token
    payload = {"event_type": "TU_THE_CO", "detail": "Kiểm thử robot"}
    assert client.post("/api/v1/sensor-event", json=payload).status_code == 401
    device_headers = {"Authorization": "Bearer " + token}
    assert client.post("/api/v1/sensor-event", headers=device_headers, json=payload).status_code == 200
    assert client.post("/api/v1/sensor-event", headers=device_headers, json={**payload, "image": "x"}).status_code == 422
    assert client.delete(f"/api/v1/devices/{device_id}/token", headers=headers).status_code == 200
    assert client.post("/api/v1/sensor-event", headers=device_headers, json=payload).status_code == 401
    assert client.delete(f"/api/v1/devices/{device_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/devices/{device_id}", headers=headers).status_code == 404
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert rotated.status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    new_headers = {"Authorization": "Bearer " + rotated.json()["access_token"]}
    assert client.get("/api/v1/stats", headers=new_headers).status_code == 200
    assert client.get("/api/v1/events", headers=new_headers).json() == client.get("/events").json()
    assert client.post("/api/v1/auth/logout", headers=new_headers).status_code == 200
    assert client.get("/api/v1/stats", headers=new_headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}).status_code == 401


def test_provider_and_prompt_crud(client, db, admin, monkeypatch):
    headers, _ = admin
    data = {"name": "Local", "base_url": "http://127.0.0.1:9999/v1", "model": "test",
            "api_key": secrets.token_urlsafe(32), "config": {"timeout": 10}}
    created = client.post("/api/v1/providers", headers=headers, json=data)
    assert created.status_code == 200
    provider_id = created.json()["id"]
    assert set(created.json()) == {"id", "name", "base_url", "model", "is_active", "config"}
    stored = db.execute(
        "SELECT encrypted_api_key FROM ai_service_configs WHERE service_id = %s", (provider_id,),
    ).fetchone()
    assert stored["encrypted_api_key"] != data["api_key"]
    assert client.get("/api/v1/providers", headers=headers).status_code == 200
    assert client.get(f"/api/v1/providers/{provider_id}", headers=headers).status_code == 200
    assert client.put(f"/api/v1/providers/{provider_id}", headers=headers, json={**data, "is_active": True}).status_code == 200
    monkeypatch.setattr(ai_client, "openai_completion", lambda *args: "Đáp án thử")
    assert client.post(f"/api/v1/providers/{provider_id}/test", headers=headers).json() == {"status": "ok"}
    prompt = {"mode": "TEST_MODE", "category_name": "Thử", "system_prompt": "Gợi ý"}
    prompt_created = client.post("/api/v1/prompts", headers=headers, json=prompt)
    assert prompt_created.status_code == 200
    prompt_id = prompt_created.json()["id"]
    assert client.get("/api/v1/prompts", headers=headers).status_code == 200
    assert client.get(f"/api/v1/prompts/{prompt_id}", headers=headers).status_code == 200
    assert client.put(f"/api/v1/prompts/{prompt_id}", headers=headers, json={**prompt, "category_name": "Đổi"}).status_code == 200
    assert client.post("/ask-ai", json={"question": "Thử", "mode": "TEST_MODE"}).json() == {"answer": "Đáp án thử"}
    assert client.get("/events").json()["events"][0]["category_name"] == "Đổi"
    assert client.delete(f"/api/v1/prompts/{prompt_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/providers/{provider_id}", headers=headers).status_code == 200
