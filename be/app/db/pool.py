# Tầng dữ liệu: tạo một pool cho mỗi tiến trình và chạy DDL lúc khởi động.
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool = None


def open_pool():
    global _pool
    if _pool is not None:
        return _pool
    settings = get_settings()
    candidate = ConnectionPool(
        settings.database_url.get_secret_value(), open=False,
        min_size=settings.pool_min_size, max_size=settings.pool_max_size,
        timeout=settings.db_timeout,
        kwargs={"row_factory": dict_row, "connect_timeout": int(settings.db_timeout)},
    )
    try:
        # libpq áp dụng connect_timeout cho từng địa chỉ IPv6/IPv4 của localhost.
        candidate.open(wait=True, timeout=settings.db_timeout * 3)
        with candidate.connection() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    except Exception:
        candidate.close()
        raise
    _pool = candidate
    return _pool


def get_pool():
    if _pool is None:
        raise RuntimeError("Pool chưa được khởi tạo")
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
