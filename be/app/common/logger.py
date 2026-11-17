# Tầng dùng chung: lấy logger, không ghi nội dung trẻ em hoặc bí mật.
import logging


def get_logger(name: str):
    return logging.getLogger("uvicorn.error." + name)
