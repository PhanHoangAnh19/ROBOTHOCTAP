# Tầng route: giữ hai API ghi sự kiện và hỏi AI, không xử lý SQL hoặc ảnh.
from fastapi import APIRouter

from app.api.dependencies import Connection
from app.common.response import response
from app.schemas.events import AskPayload, AskResponse, SensorEventPayload, SensorEventResponse
from app.services import event_service

router = APIRouter(tags=["events"])


@router.post("/ask-ai", response_model=AskResponse)
def ask_ai(payload: AskPayload, connection: Connection):
    return response(event_service.ask(connection, **payload.model_dump()))


@router.post("/sensor-event", response_model=SensorEventResponse)
def sensor_event(payload: SensorEventPayload, connection: Connection):
    return response(event_service.receive(connection, **payload.model_dump()))
