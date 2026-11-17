# Tầng service: ánh xạ cảnh báo, hỏi đáp và ghi lịch sử với hành vi tương thích bản cũ.
from app.common.exceptions import BusinessError
from app.config import get_settings
from app.common.timeutil import legacy_timestamp
from app.platform.ai_client import LLMError
from app.repositories import event_repository as repository
from app.services import prompt_service, provider_service

CATEGORIES = {
    "TU_THE_CO": "Cảnh báo Gập Cổ",
    "TU_THE_VAI": "Cảnh báo Nghiêng Vai",
    "KHOANG_CACH_MAT": "Khoảng Cách Đầu - Bàn",
    "MAT_TAP_TRUNG": "Cảnh báo Mất Tập Trung",
}


def ask(connection, question, mode):
    category, system_prompt = prompt_service.resolve(connection, mode)
    try:
        answer = provider_service.answer(connection, system_prompt, question)
    except (LLMError, BusinessError):
        answer = (f"[Chế độ Offline] Đã nhận câu hỏi '{question}'. "
                  "(Kiểm tra lại API Key để AI trả lời thực tế).")
    repository.insert(connection, mode, category, f"Hỏi: {question} ➔ Đáp: {answer}", 5)
    return {"answer": answer}


def receive(connection, event_type, detail):
    category = CATEGORIES.get(event_type, "Cảnh báo Hệ Thống")
    repository.insert(connection, event_type, category, detail)
    return {"status": "ok"}


def history(connection):
    rows = repository.latest(connection)
    for row in rows:
        row["timestamp"] = legacy_timestamp(row["timestamp"], get_settings().timezone)
    return rows


def health(connection):
    return {"status": "ok", "database": "ok" if repository.ping(connection) else "error"}
