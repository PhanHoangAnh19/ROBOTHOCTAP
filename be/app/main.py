# Tầng ứng dụng: tạo FastAPI, gắn router/middleware và quản lý pool trong lifespan.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from app.api.router import legacy_router, router
from app.api.routes.health import router as health_router
from app.db.pool import close_pool, open_pool
from app.middleware import cors, error_handler
from app.middleware.logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(open_pool)
    try:
        yield
    finally:
        await run_in_threadpool(close_pool)


app = FastAPI(lifespan=lifespan)
error_handler.install(app)
app.add_middleware(RequestLoggingMiddleware)
cors.install(app)
app.include_router(health_router)
app.include_router(legacy_router)
app.include_router(router)
