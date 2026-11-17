# Tầng schema: khuôn dữ liệu prompt giảng giải theo từng chế độ học.
from pydantic import BaseModel, ConfigDict, Field


class PromptPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = Field(min_length=1)
    category_name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)


class PromptResponse(PromptPayload):
    id: int
