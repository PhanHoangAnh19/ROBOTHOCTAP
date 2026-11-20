# Tầng repository: CRUD robot và lưu bản băm token, không lưu token rõ.
def list_all(connection, limit, offset):
    return connection.execute(
        "SELECT robot_id AS id, robot_name AS name, robot_description AS description, is_active, created_at "
        "FROM robots ORDER BY robot_id LIMIT %s OFFSET %s",
        (limit, offset),
    ).fetchall()


def get(connection, device_id):
    return connection.execute(
        "SELECT robot_id AS id, robot_name AS name, robot_description AS description, is_active, created_at "
        "FROM robots WHERE robot_id = %s", (device_id,),
    ).fetchone()


def insert(connection, name, description, is_active):
    return connection.execute(
        "INSERT INTO robots (robot_name, robot_description, is_active) VALUES (%s, %s, %s) RETURNING robot_id",
        (name, description, is_active),
    ).fetchone()["robot_id"]


def update(connection, device_id, name, description, is_active):
    connection.execute(
        "UPDATE robots SET robot_name = %s, robot_description = %s, is_active = %s WHERE robot_id = %s",
        (name, description, is_active, device_id),
    )


def delete(connection, device_id):
    connection.execute("DELETE FROM robots WHERE robot_id = %s", (device_id,))


def set_token(connection, device_id, access_token_digest):
    connection.execute(
        "UPDATE robots SET access_token_digest = %s WHERE robot_id = %s", (access_token_digest, device_id),
    )


def find_by_token(connection, access_token_digest):
    return connection.execute(
        "SELECT robot_id AS id, robot_name AS name FROM robots WHERE access_token_digest = %s AND is_active",
        (access_token_digest,),
    ).fetchone()
