from __future__ import annotations

from .llm_client import LLMClient
from .models import AuditResult, PageContent
from .prompts import CHAT_SYSTEM_PROMPT


def build_chat_messages(audit: AuditResult, pages: list[PageContent], history: list[dict[str, str]], question: str) -> list[dict[str, str]]:
    context = audit.model_dump_json(ensure_ascii=False)[:18000]
    site_text = "\n".join(p.text for p in pages)[:12000]
    recent = history[-8:]
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}, {"role": "user", "content": f"Контекст аудита JSON:\n{context}\n\nТекст сайта:\n{site_text}"}]
    messages.extend(recent)
    messages.append({"role": "user", "content": question})
    return messages


def answer_chat(llm: LLMClient, audit: AuditResult, pages: list[PageContent], history: list[dict[str, str]], question: str) -> str:
    return llm.complete(build_chat_messages(audit, pages, history, question), temperature=0.3)
