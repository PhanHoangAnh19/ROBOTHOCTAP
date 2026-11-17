# Tầng middleware: chuyển lỗi nghiệp vụ và DB thành JSON, không trả thông tin bí mật.
from fastapi.responses import JSONResponse
from psycopg import Error, IntegrityError, OperationalError
from psycopg_pool import PoolTimeout

from app.common.exceptions import BusinessError
from app.common.response import response

STATUS = {"not_found": 404, "unauthorized": 401, "conflict": 409,
          "invalid": 400, "unavailable": 503, "upstream": 502}


async def business_error(request, exc):
    return JSONResponse(status_code=STATUS.get(exc.code, 400),
                        content=response({"detail": exc.message, "code": exc.code}))


async def database_error(request, exc):
    if isinstance(exc, IntegrityError):
        status, message = 409, "Dữ liệu trùng hoặc vi phạm ràng buộc"
    elif isinstance(exc, (OperationalError, PoolTimeout)):
        status, message = 503, "PostgreSQL chưa sẵn sàng"
    else:
        status, message = 500, "Không thực hiện được thao tác dữ liệu"
    return JSONResponse(status_code=status, content=response({"detail": message}))


def install(app):
    app.add_exception_handler(BusinessError, business_error)
    app.add_exception_handler(Error, database_error)
    app.add_exception_handler(PoolTimeout, database_error)
