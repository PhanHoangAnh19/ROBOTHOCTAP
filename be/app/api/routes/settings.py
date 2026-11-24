# Tầng route: đọc và cập nhật cấu hình ngưỡng cảnh báo qua app_settings.
from fastapi import APIRouter, Depends

from app.api.dependencies import Connection, get_current_admin
from app.common.response import response
from app.schemas.settings import SettingsPayload, SettingsResponse
from app.services import setting_service

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=SettingsResponse)
def get_settings(connection: Connection):
    return response(setting_service.get_all(connection))


@router.put("", response_model=SettingsResponse)
def put_settings(payload: SettingsPayload, connection: Connection):
    updates = payload.model_dump(exclude_none=True)
    return response(setting_service.update(connection, updates))
