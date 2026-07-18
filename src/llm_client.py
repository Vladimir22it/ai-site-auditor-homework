from __future__ import annotations

import json
import re
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import Settings
from .models import AuditResult


class LLMConfigurationError(RuntimeError):
    """Raised when LLM provider settings are incomplete."""


class LLMResponseError(RuntimeError):
    """Raised when an LLM request or response parsing fails."""


def strip_code_fence(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()


def extract_json_object(text: str) -> str:
    clean = strip_code_fence(text)
    is_clean_json = False
    try:
        json.loads(clean)
        is_clean_json = True
    except json.JSONDecodeError:
        is_clean_json = False
    if is_clean_json:
        return clean
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMResponseError("Ответ LLM не содержит JSON-объект")
    return clean[start:end + 1]


def parse_audit_json(text: str) -> AuditResult:
    try:
        return AuditResult.model_validate_json(extract_json_object(text))
    except Exception as exc:
        raise LLMResponseError(f"Не удалось разобрать структурированный ответ LLM: {exc}") from exc


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.is_llm_configured:
            raise LLMConfigurationError("Настройте LLM_API_KEY, LLM_BASE_URL и LLM_MODEL")
        self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    def complete(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        try:
            response = self.client.chat.completions.create(model=self.settings.llm_model, messages=messages, temperature=temperature)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise LLMResponseError("LLM-запрос не выполнен. Проверьте настройки провайдера.") from exc
