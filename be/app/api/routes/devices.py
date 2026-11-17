# Tầng route: CRUD thiết bị và quản lý token robot dành cho admin.
from fastapi import APIRouter, Depends

from app.api.dependencies import Connection, Page, get_current_admin
from app.common.response import response
from app.schemas.devices import DevicePayload, DeviceResponse, DeviceTokenResponse
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=list[DeviceResponse])
def list_devices(connection: Connection, page: Page):
    return response(device_service.list_devices(connection, page))


@router.post("", response_model=DeviceResponse)
def create(payload: DevicePayload, connection: Connection):
    return response(device_service.create(connection, payload.model_dump()))


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, connection: Connection):
    return response(device_service.get_device(connection, device_id))


@router.put("/{device_id}", response_model=DeviceResponse)
def update(device_id: int, payload: DevicePayload, connection: Connection):
    return response(device_service.update(connection, device_id, payload.model_dump()))


@router.delete("/{device_id}")
def delete(device_id: int, connection: Connection):
    return response(device_service.delete(connection, device_id))


@router.post("/{device_id}/token", response_model=DeviceTokenResponse)
def issue_token(device_id: int, connection: Connection):
    return response(device_service.issue_token(connection, device_id))


@router.delete("/{device_id}/token")
def revoke_token(device_id: int, connection: Connection):
    return response(device_service.revoke_token(connection, device_id))
