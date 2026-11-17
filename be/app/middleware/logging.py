# Tầng middleware: ghi method, đường dẫn và độ trễ; không đọc hoặc lưu body.
import time

from app.common.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = time.monotonic()

        async def log_send(message):
            if message["type"] == "http.response.start":
                logger.info("http method=%s path=%s status=%s latency_ms=%.1f",
                            scope["method"], scope["path"], message["status"],
                            (time.monotonic() - started) * 1000)
            await send(message)

        await self.app(scope, receive, log_send)
