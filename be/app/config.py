# Tầng cấu hình: đọc biến môi trường và .env, không chứa bí mật mặc định.
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8", extra="ignore",
    )
    database_url: SecretStr
    port: int = Field(default=8000, ge=1, le=65535)
    timezone: str = "Asia/Bangkok"
    pool_min_size: int = Field(default=1, ge=1)
    pool_max_size: int = Field(default=10, ge=1)
    db_timeout: float = Field(default=10, gt=0)
    jwt_secret: SecretStr = SecretStr("")
    access_token_minutes: int = Field(default=30, ge=1)
    refresh_token_days: int = Field(default=7, ge=1)
    provider_encryption_key: SecretStr = SecretStr("")
    llm_base_url: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = ""
    llm_timeout: float = Field(default=10, gt=0)
    llm_retries: int = Field(default=1, ge=0, le=5)
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    return Settings()
