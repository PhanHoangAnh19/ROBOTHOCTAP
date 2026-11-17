# Tầng nền tảng: mã hóa khóa provider, băm mật khẩu và token bằng thư viện chuẩn.
import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, InvalidToken

from app.common.exceptions import BusinessError
from app.config import get_settings


def token_hash(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def verify_password(password: str, stored: str):
    try:
        raw = base64.b64decode(stored, validate=True)
        digest = hashlib.scrypt(password.encode(), salt=raw[:16], n=16384, r=8, p=1)
        return hmac.compare_digest(digest, raw[16:])
    except (ValueError, TypeError):
        return False


def cipher():
    key = get_settings().provider_encryption_key.get_secret_value()
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError):
        raise BusinessError("unavailable", "Cần cấu hình PROVIDER_ENCRYPTION_KEY hợp lệ") from None


def encrypt_api_key(value: str):
    return cipher().encrypt(value.encode()).decode()


def decrypt_api_key(value: str):
    try:
        return cipher().decrypt(value.encode()).decode()
    except InvalidToken:
        raise BusinessError("unavailable", "Không giải mã được khóa provider") from None
