# Tầng service: quản lý provider, mã hóa khóa và kiểm tra kết nối LLM văn bản.
from app.common.exceptions import BusinessError, require_found
from app.config import get_settings
from app.platform import ai_client
from app.platform.crypto import decrypt_api_key, encrypt_api_key
from app.repositories import provider_repository as repository


def _public(row):
    return {key: value for key, value in row.items() if key != "encrypted_api_key"}


def list_providers(connection, page):
    return repository.list_all(connection, page.limit, page.offset)


def get_provider(connection, provider_id):
    return _public(require_found(repository.get(connection, provider_id)))


def _data(data):
    values = dict(data)
    values["base_url"] = str(values["base_url"])
    values["encrypted"] = encrypt_api_key(values.pop("api_key").get_secret_value())
    return values


def create(connection, data):
    return get_provider(connection, repository.insert(connection, **_data(data)))


def update(connection, provider_id, data):
    get_provider(connection, provider_id)
    repository.update(connection, provider_id, **_data(data))
    return get_provider(connection, provider_id)


def delete(connection, provider_id):
    get_provider(connection, provider_id)
    repository.delete(connection, provider_id)
    return {"status": "ok"}


def test_connection(connection, provider_id):
    provider = require_found(repository.get(connection, provider_id))
    try:
        ai_client.openai_completion(provider["base_url"], decrypt_api_key(provider["encrypted_api_key"]),
                                    provider["model"], "Reply briefly.", "Hello")
    except ai_client.LLMError:
        raise BusinessError("upstream", "Không kết nối được provider") from None
    return {"status": "ok"}


def answer(connection, system_prompt, question):
    provider = repository.active(connection)
    if provider:
        return ai_client.openai_completion(provider["base_url"], decrypt_api_key(provider["encrypted_api_key"]),
                                           provider["model"], system_prompt, question)
    settings = get_settings()
    if settings.llm_base_url:
        return ai_client.openai_completion(settings.llm_base_url, settings.llm_api_key.get_secret_value(),
                                           settings.llm_model, system_prompt, question)
    return ai_client.gemini_completion(system_prompt, question)
