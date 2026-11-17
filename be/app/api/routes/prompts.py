# Tầng route: CRUD prompt giảng giải, yêu cầu JWT quản trị.
from fastapi import APIRouter, Depends

from app.api.dependencies import Connection, Page, get_current_admin
from app.common.response import response
from app.schemas.prompts import PromptPayload, PromptResponse
from app.services import prompt_service

router = APIRouter(prefix="/prompts", tags=["prompts"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=list[PromptResponse])
def list_prompts(connection: Connection, page: Page):
    return response(prompt_service.list_prompts(connection, page))


@router.post("", response_model=PromptResponse)
def create(payload: PromptPayload, connection: Connection):
    return response(prompt_service.create(connection, payload.model_dump()))


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, connection: Connection):
    return response(prompt_service.get_prompt(connection, prompt_id))


@router.put("/{prompt_id}", response_model=PromptResponse)
def update(prompt_id: int, payload: PromptPayload, connection: Connection):
    return response(prompt_service.update(connection, prompt_id, payload.model_dump()))


@router.delete("/{prompt_id}")
def delete(prompt_id: int, connection: Connection):
    return response(prompt_service.delete(connection, prompt_id))
