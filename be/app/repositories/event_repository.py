# Tầng repository: ghi sự kiện văn bản và đọc lịch sử, kiểm tra kết nối DB.
def insert(connection, event_type, category_name, detail, duration=0):
    return connection.execute(
        "INSERT INTO learning_events (occurred_at, event_kind, category_label, event_detail, duration_minutes) "
        "VALUES (clock_timestamp(), %s, %s, %s, %s) RETURNING event_id",
        (event_type, category_name, detail, duration),
    ).fetchone()["event_id"]


def latest(connection):
    return connection.execute(
        "SELECT event_id AS id, occurred_at AS timestamp, event_kind AS event_type, "
        "category_label AS category_name, event_detail AS detail, duration_minutes "
        "FROM learning_events ORDER BY event_id DESC LIMIT 50"
    ).fetchall()


def ping(connection):
    return connection.execute("SELECT 1 AS alive").fetchone()["alive"] == 1
