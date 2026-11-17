# Tầng schema: giữ nguyên bốn chỉ số thống kê và danh sách sự kiện của dashboard.
from app.schemas.events import EventResponse, EventSchema


class Summary(EventSchema):
    total_study_minutes: int
    posture_warnings: int
    attention_warnings: int
    ai_interactions: int


class EventsResponse(EventSchema):
    summary: Summary
    events: list[EventResponse]
