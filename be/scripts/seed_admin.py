# Tầng công cụ: tạo admin đầu tiên qua service, nhập mật khẩu ẩn từ bàn phím.
import argparse
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.common.exceptions import BusinessError
from app.db.pool import close_pool, open_pool
from app.services.auth_service import seed_admin


def main():
    parser = argparse.ArgumentParser(description="Tạo tài khoản quản trị")
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    password = getpass("Mật khẩu (ít nhất 8 ký tự): ")
    if password != getpass("Nhập lại mật khẩu: "):
        parser.error("Mật khẩu xác nhận không trùng")
    try:
        pool = open_pool()
        with pool.connection() as connection:
            account_id = seed_admin(connection, args.username, password)
        print(f"Đã tạo admin id={account_id}")
    except BusinessError as exc:
        parser.exit(1, exc.message + "\n")
    finally:
        close_pool()


if __name__ == "__main__":
    main()
