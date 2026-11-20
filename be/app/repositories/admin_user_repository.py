# Tầng repository: lưu tài khoản và phiên đăng nhập quản trị bằng SQL.
def find_by_username(connection, username):
    return connection.execute(
        "SELECT account_id, login_name, hashed_password, is_active FROM admin_accounts WHERE login_name = %s",
        (username,),
    ).fetchone()


def insert(connection, username, hashed_password):
    return connection.execute(
        "INSERT INTO admin_accounts (login_name, hashed_password) VALUES (%s, %s) RETURNING account_id",
        (username, hashed_password),
    ).fetchone()["account_id"]


def create_session(connection, account_id, refresh_token_digest, expires_at):
    return connection.execute(
        "INSERT INTO admin_login_sessions (account_id, refresh_token_digest, expires_at) "
        "VALUES (%s, %s, %s) RETURNING session_id",
        (account_id, refresh_token_digest, expires_at),
    ).fetchone()["session_id"]


def session(connection, session_id):
    return connection.execute(
        "SELECT s.session_id, s.account_id, s.refresh_token_digest, s.expires_at, s.is_revoked, "
        "a.login_name, a.is_active FROM admin_login_sessions s "
        "JOIN admin_accounts a ON a.account_id = s.account_id WHERE s.session_id = %s",
        (session_id,),
    ).fetchone()


def rotate(connection, session_id, old_hash, new_hash):
    return connection.execute(
        "UPDATE admin_login_sessions SET refresh_token_digest = %s WHERE session_id = %s "
        "AND refresh_token_digest = %s AND NOT is_revoked AND expires_at > CURRENT_TIMESTAMP RETURNING session_id",
        (new_hash, session_id, old_hash),
    ).fetchone()


def revoke(connection, session_id):
    connection.execute("UPDATE admin_login_sessions SET is_revoked = TRUE WHERE session_id = %s", (session_id,))
