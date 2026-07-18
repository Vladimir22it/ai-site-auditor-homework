from __future__ import annotations

import re
from bs4 import BeautifulSoup
import trafilatura

DEFAULT_MAX_PAGE_CHARS = 10_000


def clean_html(html: str, url: str = "", max_chars: int = DEFAULT_MAX_PAGE_CHARS) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "svg", "canvas", "nav", "footer", "header", "form"]):
        tag.decompose()
    for selector in ["[role=navigation]", ".menu", ".nav", ".cookie", ".modal", ".sidebar"]:
        for tag in soup.select(selector):
            tag.decompose()
    extracted = trafilatura.extract(str(soup), url=url, include_comments=False, include_tables=False) or soup.get_text(" ")
    text = re.sub(r"\s+", " ", extracted).strip()
    return title, text[:max_chars]
