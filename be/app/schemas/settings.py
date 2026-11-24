# Tầng schema: dữ liệu đọc và ghi cấu hình app_settings.
from pydantic import BaseModel, ConfigDict, Field


class SettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    posture_bad_threshold_seconds: int = Field(default=None, gt=0)
    reminder_cooldown_seconds: int = Field(default=None, gt=0)
    debounce_seconds: int = Field(default=None, gt=0)


class SettingsResponse(BaseModel):
    posture_bad_threshold_seconds: int
    reminder_cooldown_seconds: int
    debounce_seconds: int

