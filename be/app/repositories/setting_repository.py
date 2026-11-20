# Tầng repository: đọc và ghi cấu hình mở rộng dạng JSONB.
from psycopg.types.json import Jsonb


def get(connection, key):
    return connection.execute("SELECT setting_value AS value FROM app_settings WHERE setting_key = %s", (key,)).fetchone()


def put(connection, key, value):
    return connection.execute(
        "INSERT INTO app_settings (setting_key, setting_value) VALUES (%s, %s) "
        "ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value RETURNING app_setting_id",
        (key, Jsonb(value)),
    ).fetchone()["app_setting_id"]
