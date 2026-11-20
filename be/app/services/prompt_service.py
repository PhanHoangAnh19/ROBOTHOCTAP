# Tầng service: CRUD prompt và giữ nguyên ánh xạ chế độ, prompt mặc định của bản cũ.
from app.common.exceptions import require_found
from app.repositories import prompt_repository as repository

DEFAULT_PROMPTS = {
    "GIAI_TOAN": ("Giải Toán", "Bạn là gia sư toán. Hãy giải chi tiết từng bước thật dễ hiểu dưới 60 từ:"),
    "DAY_HOC": ("Dạy Học Gợi Mở", "Bạn là gia sư Socratic. Đừng giải hộ ngay mà hãy gợi ý phương pháp tư duy dưới 60 từ:"),
    "THAC_MAC": ("Giải Đáp Kiến Thức", "Bạn là bách khoa toàn thư thông minh. Trả lời thú vị, ngắn gọn dưới 60 từ:"),
}


def resolve(connection, mode):
    row = repository.by_mode(connection, mode)
    if row:
        return row["category_name"], row["system_prompt"]
    return DEFAULT_PROMPTS.get(mode, DEFAULT_PROMPTS["THAC_MAC"])


def list_prompts(connection, page):
    return repository.list_all(connection, page.limit, page.offset)


def get_prompt(connection, prompt_id):
    return require_found(repository.get(connection, prompt_id))


def create(connection, data):
    return get_prompt(connection, repository.insert(connection, **data))


def update(connection, prompt_id, data):
    get_prompt(connection, prompt_id)
    repository.update(connection, prompt_id, **data)
    return get_prompt(connection, prompt_id)


def delete(connection, prompt_id):
    get_prompt(connection, prompt_id)
    repository.delete(connection, prompt_id)
    return {"status": "ok"}
