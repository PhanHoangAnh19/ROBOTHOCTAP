# Tầng middleware: giữ cấu hình CORS cũ để dashboard tiếp tục gọi backend.
from fastapi.middleware.cors import CORSMiddleware


def install(app):
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
