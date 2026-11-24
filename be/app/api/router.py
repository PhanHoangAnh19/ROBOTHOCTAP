# Tầng API: gộp router phiên bản mới và giữ riêng các URL tương thích cũ.
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_admin, get_current_device
from app.api.routes import auth, devices, events, health, prompts, providers, settings, stats

legacy_router = APIRouter()
legacy_router.include_router(events.router)
legacy_router.include_router(stats.legacy_router)

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(devices.router)
router.include_router(providers.router)
router.include_router(prompts.router)
router.include_router(settings.router)
router.include_router(events.router, dependencies=[Depends(get_current_device)])
router.include_router(stats.legacy_router, dependencies=[Depends(get_current_admin)])
router.include_router(stats.router, dependencies=[Depends(get_current_admin)])
