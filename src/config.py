from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

PROVIDER_BASE_URLS = {
    "proxyapi": "https://api.proxyapi.ru/openai/v1",
    "routerai": "https://api.routerai.ru/v1",
    "kodikrouter": "https://llm.kodikrouter.com/v1",
    "custom": "",
}


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "custom"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    enable_browser_fetch: bool = False
    http_timeout_seconds: float = 12.0
    max_pages: int = 5
    max_internal_pages: int = 4
    max_page_chars: int = 10_000
    max_total_chars: int = 40_000
    min_text_chars_for_browser_fallback: int = 500

    @property
    def is_llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_base_url and self.llm_model)


def _secret_get(name: str) -> str:
    try:
        import streamlit as st

        return str(st.secrets.get(name, ""))
    except Exception:
        return ""


def get_setting(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    value = _secret_get(name)
    if value:
        return value
    load_dotenv(override=False)
    return os.getenv(name, "")


def _get_int(name: str, default: int) -> int:
    raw = get_setting(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = get_setting(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def load_settings() -> Settings:
    provider = (get_setting("LLM_PROVIDER") or "custom").lower()
    base_url = get_setting("LLM_BASE_URL") or PROVIDER_BASE_URLS.get(provider, "")
    max_pages = min(max(_get_int("MAX_PAGES", 5), 1), 5)
    max_internal_pages = min(max(_get_int("MAX_INTERNAL_PAGES", 4), 0), max_pages - 1)
    return Settings(
        llm_provider=provider,
        llm_api_key=get_setting("LLM_API_KEY"),
        llm_base_url=base_url.rstrip("/"),
        llm_model=get_setting("LLM_MODEL"),
        enable_browser_fetch=(get_setting("ENABLE_BROWSER_FETCH").lower() == "true"),
        http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 12.0),
        max_pages=max_pages,
        max_internal_pages=max_internal_pages,
        max_page_chars=min(max(_get_int("MAX_PAGE_CHARS", 10_000), 1_000), 10_000),
        max_total_chars=min(max(_get_int("MAX_TOTAL_CHARS", 40_000), 5_000), 40_000),
        min_text_chars_for_browser_fallback=_get_int("MIN_TEXT_CHARS_FOR_BROWSER_FALLBACK", 500),
    )
