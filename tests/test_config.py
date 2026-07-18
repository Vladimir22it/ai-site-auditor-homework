from src.config import load_settings


def test_provider_default_base_url(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "proxyapi")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    settings = load_settings()
    assert settings.llm_base_url == "https://api.proxyapi.ru/openai/v1"
    assert settings.is_llm_configured


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
