import pytest

from src.config import load_settings


@pytest.mark.parametrize(
    ("provider", "base_url"),
    [
        ("proxyapi", "https://openai.api.proxyapi.ru/v1"),
        ("routerai", "https://routerai.ru/api/v1"),
        ("kodikrouter", "https://api.kodikrouter.ru/v1"),
        ("custom", ""),
    ],
)
def test_provider_default_base_url(monkeypatch, provider, base_url):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    settings = load_settings()
    assert settings.llm_base_url == base_url
    assert settings.is_llm_configured == bool(base_url)


def test_crawler_limits_are_capped(monkeypatch):
    monkeypatch.setenv("MAX_PAGES", "99")
    monkeypatch.setenv("MAX_INTERNAL_PAGES", "99")
    monkeypatch.setenv("MAX_PAGE_CHARS", "999999")
    monkeypatch.setenv("MAX_TOTAL_CHARS", "999999")
    settings = load_settings()
    assert settings.max_pages == 5
    assert settings.max_internal_pages == 4
    assert settings.max_page_chars == 10000
    assert settings.max_total_chars == 40000
