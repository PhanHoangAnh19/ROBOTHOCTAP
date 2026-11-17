# Tầng route: kiểm tra server và PostgreSQL thông qua service sự kiện.
from fastapi import APIRouter

from app.api.dependencies import Connection
from app.common.response import response
from app.services import event_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health(connection: Connection):
    return response(event_service.health(connection))
