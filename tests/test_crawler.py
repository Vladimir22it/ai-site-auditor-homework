import socket
import httpx
import pytest
from src.config import Settings
from src.crawler import _candidate_links, crawl_site


def public_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("93.184.216.34", 0))])


def test_candidate_links_priority_and_exclusions():
    html = open("tests/fixtures/sample.html", encoding="utf-8").read()
    links = _candidate_links(html, "https://example.com/", limit=4)
    assert links == ["https://example.com/about"]


def test_crawl_static_html_and_redirect_check(monkeypatch):
    public_dns(monkeypatch)
    html = open("tests/fixtures/sample.html", encoding="utf-8").read()
    def handler(request):
        if request.url.path == "/about":
            return httpx.Response(200, headers={"content-type": "text/html"}, text="<main>О компании Acme</main>")
        return httpx.Response(200, headers={"content-type": "text/html"}, text=html)
    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(transport=transport, **{k: v for k, v in kwargs.items() if k != "transport"}))
    result = crawl_site("https://example.com", Settings())
    assert len(result.pages) == 2
    assert result.pages[1].url.endswith("/about")


def test_redirect_to_forbidden_address_is_blocked(monkeypatch):
    public_dns(monkeypatch)
    def handler(request):
        if request.url.host == "example.com":
            return httpx.Response(302, headers={"location": "http://127.0.0.1/"})
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<main>x</main>")
    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(transport=transport, **{k: v for k, v in kwargs.items() if k != "transport"}))
    with pytest.raises(ValueError):
        crawl_site("https://example.com", Settings())


def test_browser_fallback_used_for_short_main_text(monkeypatch):
    public_dns(monkeypatch)
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<main>x</main>")
    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(transport=transport, **{k: v for k, v in kwargs.items() if k != "transport"}))
    monkeypatch.setattr("src.crawler._fetch_with_browser", lambda url, timeout: "<main>" + "д" * 600 + "</main>")
    result = crawl_site("https://example.com", Settings(enable_browser_fetch=True))
    assert len(result.pages[0].text) >= 500
    assert "Playwright fallback" in result.warnings[0]


def test_browser_fallback_unavailable_does_not_crash(monkeypatch):
    public_dns(monkeypatch)
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<main>x</main>")
    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(transport=transport, **{k: v for k, v in kwargs.items() if k != "transport"}))
    def fail_browser(url, timeout):
        raise RuntimeError("not installed")
    monkeypatch.setattr("src.crawler._fetch_with_browser", fail_browser)
    result = crawl_site("https://example.com", Settings(enable_browser_fetch=True))
    assert result.pages[0].text == "x"
    assert "недоступен" in result.warnings[0]
