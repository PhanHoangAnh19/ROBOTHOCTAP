# Tầng service: CRUD thiết bị, cấp và thu hồi token, xác thực robot.
import secrets

from app.common.exceptions import BusinessError, require_found
from app.platform.crypto import token_hash
from app.repositories import device_repository as repository


def list_devices(connection, page):
    return repository.list_all(connection, page.limit, page.offset)


def get_device(connection, device_id):
    return require_found(repository.get(connection, device_id))


def create(connection, data):
    return get_device(connection, repository.insert(connection, **data))


def update(connection, device_id, data):
    get_device(connection, device_id)
    repository.update(connection, device_id, **data)
    return get_device(connection, device_id)


def delete(connection, device_id):
    get_device(connection, device_id)
    repository.delete(connection, device_id)
    return {"status": "ok"}


def issue_token(connection, device_id):
    get_device(connection, device_id)
    token = secrets.token_urlsafe(32)
    repository.set_token(connection, device_id, token_hash(token))
    return {"device_id": device_id, "token": token}


def revoke_token(connection, device_id):
    get_device(connection, device_id)
    repository.set_token(connection, device_id, None)
    return {"status": "ok"}


def authenticate(connection, token):
    device = repository.find_by_token(connection, token_hash(token))
    if not device:
        raise BusinessError("unauthorized", "Token robot không hợp lệ")
    return device
