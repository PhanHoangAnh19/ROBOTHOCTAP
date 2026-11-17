# Tầng repository: CRUD provider với khóa đã mã hóa và cấu hình JSONB.
from psycopg.types.json import Jsonb


def list_all(connection, limit, offset):
    return connection.execute(
        "SELECT service_id AS id, service_name AS name, endpoint_url AS base_url, model_name AS model, "
        "is_active, service_config AS config FROM ai_service_configs ORDER BY service_id LIMIT %s OFFSET %s",
        (limit, offset),
    ).fetchall()


def get(connection, provider_id):
    return connection.execute(
        "SELECT service_id AS id, service_name AS name, endpoint_url AS base_url, model_name AS model, "
        "encrypted_api_key, is_active, service_config AS config FROM ai_service_configs WHERE service_id = %s",
        (provider_id,),
    ).fetchone()


def active(connection):
    return connection.execute(
        "SELECT service_id AS id, service_name AS name, endpoint_url AS base_url, model_name AS model, "
        "encrypted_api_key, is_active, service_config AS config FROM ai_service_configs WHERE is_active LIMIT 1"
    ).fetchone()


def insert(connection, name, base_url, model, encrypted, is_active, config):
    return connection.execute(
        "INSERT INTO ai_service_configs (service_name, endpoint_url, model_name, encrypted_api_key, is_active, service_config) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING service_id",
        (name, base_url, model, encrypted, is_active, Jsonb(config)),
    ).fetchone()["service_id"]


def update(connection, provider_id, name, base_url, model, encrypted, is_active, config):
    connection.execute(
        "UPDATE ai_service_configs SET service_name = %s, endpoint_url = %s, model_name = %s, encrypted_api_key = %s, "
        "is_active = %s, service_config = %s WHERE service_id = %s",
        (name, base_url, model, encrypted, is_active, Jsonb(config), provider_id),
    )


def delete(connection, provider_id):
    connection.execute("DELETE FROM ai_service_configs WHERE service_id = %s", (provider_id,))
