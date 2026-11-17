# Tầng schema: khuôn dữ liệu robot và token, không trả bản băm bí mật.
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DevicePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    description: str = ""
    is_active: bool = True


class DeviceResponse(DevicePayload):
    id: int
    created_at: datetime


class DeviceTokenResponse(BaseModel):
    device_id: int
    token: str
