from __future__ import annotations

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel
from .config import Settings
from .content_extractor import clean_html
from .models import PageContent
from .url_security import URLSecurityError, normalize_url, same_domain, validate_public_url

PRIORITY = ("about", "company", "o-kompanii", "services", "uslugi", "products", "catalog", "faq", "contacts", "contact", "pricing", "prices", "team")
EXCLUDED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".zip", ".rar", ".7z", ".mp4", ".avi", ".mov")
EXCLUDED_PATH = ("login", "signin", "account", "cabinet", "cart", "checkout", "wp-admin")
UA = "AI-Site-Auditor/1.0 (+https://streamlit.app)"


class CrawlResult(BaseModel):
    pages: list[PageContent]
    warnings: list[str] = []


def _check_response(response: httpx.Response) -> None:
    validate_public_url(str(response.url))
    response.raise_for_status()
    ctype = response.headers.get("content-type", "").lower()
    if "text/html" not in ctype and "application/xhtml" not in ctype:
        raise ValueError("Страница не является HTML")


def _candidate_links(html: str, base_url: str, limit: int = 4) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        url = normalize_url(urljoin(base_url, a["href"]))
        path = urlparse(url).path.lower()
        if not same_domain(url, base_url) or path.endswith(EXCLUDED_EXT) or any(x in path for x in EXCLUDED_PATH):
            continue
        if url not in links:
            links.append(url)
    return sorted(links, key=lambda u: (0 if any(p in u.lower() for p in PRIORITY) else 1, len(u)))[:limit]


def _fetch_with_browser(url: str, timeout_seconds: float) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright не установлен. HTTP-режим продолжает работу без browser fallback.") from exc
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA)
        try:
            response = page.goto(url, wait_until="networkidle", timeout=int(timeout_seconds * 1000))
            if response is not None:
                validate_public_url(response.url)
            return page.content()
        finally:
            browser.close()


def _extract_page(html: str, url: str, max_page_chars: int) -> PageContent:
    title, text = clean_html(html, url=url, max_chars=max_page_chars)
    return PageContent(url=url, title=title, text=text)


def crawl_site(url: str, settings: Settings) -> CrawlResult:
    start = validate_public_url(url)
    warnings: list[str] = []
    pages: list[PageContent] = []
    with httpx.Client(follow_redirects=True, timeout=settings.http_timeout_seconds, headers={"User-Agent": UA}) as client:
        try:
            main = client.get(start)
            _check_response(main)
        except Exception as exc:
            raise ValueError(f"Не удалось загрузить сайт: {exc}") from exc
        main_url = str(main.url)
        page = _extract_page(main.text, main_url, settings.max_page_chars)
        if settings.enable_browser_fetch and len(page.text) < settings.min_text_chars_for_browser_fallback:
            try:
                browser_html = _fetch_with_browser(main_url, settings.http_timeout_seconds)
                page = _extract_page(browser_html, main_url, settings.max_page_chars)
                warnings.append("Для главной страницы использован Playwright fallback из-за малого объёма текста после HTTP-загрузки.")
            except Exception as exc:
                warnings.append(f"Playwright fallback недоступен, используется HTTP-текст: {exc}")
        pages.append(page)
        for link in _candidate_links(main.text, main_url, settings.max_internal_pages):
            if len(pages) >= settings.max_pages:
                break
            try:
                resp = client.get(link)
                _check_response(resp)
                extracted = _extract_page(resp.text, str(resp.url), settings.max_page_chars)
                if extracted.text:
                    pages.append(extracted)
            except (httpx.HTTPError, URLSecurityError, ValueError) as exc:
                warnings.append(f"Пропущена страница {link}: {exc}")
    total = 0
    limited: list[PageContent] = []
    for page in pages:
        room = settings.max_total_chars - total
        if room <= 0:
            break
        page.text = page.text[:room]
        total += len(page.text)
        limited.append(page)
    return CrawlResult(pages=limited, warnings=warnings)
