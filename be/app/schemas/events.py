# Tầng schema: sự kiện và câu hỏi chỉ nhận văn bản, cấm mọi trường ngoài khai báo.
from pydantic import BaseModel, ConfigDict


class EventSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AskPayload(EventSchema):
    question: str
    mode: str = "GIAI_TOAN"


class SensorEventPayload(EventSchema):
    event_type: str
    detail: str


class AskResponse(EventSchema):
    answer: str


class SensorEventResponse(EventSchema):
    status: str


class EventResponse(EventSchema):
    id: int
    timestamp: str
    event_type: str
    category_name: str
    detail: str
    duration_minutes: int
