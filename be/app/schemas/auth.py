# Tầng schema: dữ liệu đăng nhập, refresh và phản hồi token quản trị.
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1)
    password: SecretStr


class RefreshPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
