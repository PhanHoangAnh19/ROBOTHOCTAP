# Tầng route: CRUD provider và kiểm tra kết nối, chỉ dành cho quản trị viên.
from fastapi import APIRouter, Depends

from app.api.dependencies import Connection, Page, get_current_admin
from app.common.response import response
from app.schemas.providers import ProviderPayload, ProviderResponse
from app.services import provider_service

router = APIRouter(prefix="/providers", tags=["providers"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=list[ProviderResponse])
def list_providers(connection: Connection, page: Page):
    return response(provider_service.list_providers(connection, page))


@router.post("", response_model=ProviderResponse)
def create(payload: ProviderPayload, connection: Connection):
    return response(provider_service.create(connection, payload.model_dump()))


@router.get("/{provider_id}", response_model=ProviderResponse)
def get_provider(provider_id: int, connection: Connection):
    return response(provider_service.get_provider(connection, provider_id))


@router.put("/{provider_id}", response_model=ProviderResponse)
def update(provider_id: int, payload: ProviderPayload, connection: Connection):
    return response(provider_service.update(connection, provider_id, payload.model_dump()))


@router.delete("/{provider_id}")
def delete(provider_id: int, connection: Connection):
    return response(provider_service.delete(connection, provider_id))


@router.post("/{provider_id}/test")
def test_connection(provider_id: int, connection: Connection):
    return response(provider_service.test_connection(connection, provider_id))
