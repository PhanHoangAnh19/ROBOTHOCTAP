# Tầng route: lịch sử và thống kê dashboard giữ nguyên hợp đồng JSON cũ.
from fastapi import APIRouter

from app.api.dependencies import Connection
from app.common.response import response
from app.schemas.stats import EventsResponse, Summary
from app.services import stats_service

legacy_router = APIRouter(tags=["stats"])
router = APIRouter(tags=["stats"])


@legacy_router.get("/events", response_model=EventsResponse)
def get_events(connection: Connection):
    return response(stats_service.dashboard(connection))


@router.get("/stats", response_model=Summary)
def get_stats(connection: Connection):
    return response(stats_service.dashboard(connection)["summary"])
