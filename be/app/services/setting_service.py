# Tầng service: đọc và cập nhật cấu hình app_settings, validate khóa hợp lệ.
from app.repositories import setting_repository as repository

ALLOWED_KEYS = frozenset(["posture_bad_threshold_seconds", "reminder_cooldown_seconds", "debounce_seconds"])


def get_all(connection):
    return repository.get_all(connection)


def update(connection, settings: dict):
    for key, value in settings.items():
        repository.put(connection, key, value)
    return repository.get_all(connection)

