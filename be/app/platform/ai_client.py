# Tầng nền tảng: gọi LLM văn bản, timeout/retry; chỉ log token và độ trễ.
import json
import time
import urllib.error
import urllib.request

from app.common.logger import get_logger
from app.config import get_settings

logger = get_logger(__name__)


class LLMError(Exception):
    pass


def _request(url, data, headers):
    settings = get_settings()
    for attempt in range(settings.llm_retries + 1):
        started = time.monotonic()
        try:
            request = urllib.request.Request(
                url, data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json", **headers},
            )
            with urllib.request.urlopen(request, timeout=settings.llm_timeout) as result:
                body = json.loads(result.read().decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("Phản hồi LLM phải là JSON object")
            usage = body.get("usage", body.get("usageMetadata", {}))
            if not isinstance(usage, dict):
                usage = {}
            token_counts = {
                key: usage[key] for key in (
                    "prompt_tokens", "completion_tokens", "total_tokens",
                    "promptTokenCount", "candidatesTokenCount", "totalTokenCount",
                ) if isinstance(usage.get(key), int)
            }
            logger.info("llm latency_ms=%.1f tokens=%s", (time.monotonic() - started) * 1000, token_counts)
            return body
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            logger.warning("llm attempt=%s latency_ms=%.1f error_type=%s",
                           attempt + 1, (time.monotonic() - started) * 1000, type(exc).__name__)
            retryable = not isinstance(exc, urllib.error.HTTPError) or exc.code == 429 or exc.code >= 500
            if not retryable or attempt == settings.llm_retries:
                raise LLMError("Không gọi được LLM") from None
            time.sleep(min(0.25 * (2 ** attempt), 2))


def openai_completion(base_url, api_key, model, system_prompt, question):
    result = _request(
        base_url.rstrip("/") + "/chat/completions",
        {"model": model, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]}, {"Authorization": f"Bearer {api_key}"},
    )
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        raise LLMError("Phản hồi LLM không hợp lệ") from None


def gemini_completion(system_prompt, question):
    settings = get_settings()
    api_key = settings.gemini_api_key.get_secret_value()
    if not api_key:
        raise LLMError("Chưa cấu hình Gemini")
    result = _request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        {"contents": [{"parts": [{"text": f"{system_prompt} {question}"}]}]},
        {"x-goog-api-key": api_key},
    )
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        raise LLMError("Phản hồi Gemini không hợp lệ") from None
