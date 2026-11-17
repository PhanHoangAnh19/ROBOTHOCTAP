# Tầng schema: cấu hình provider, nhận khóa bí mật nhưng không trả khóa trong JSON.
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr


class ProviderPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    base_url: HttpUrl
    model: str = Field(min_length=1)
    api_key: SecretStr
    is_active: bool = False
    config: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    id: int
    name: str
    base_url: str
    model: str
    is_active: bool
    config: dict
