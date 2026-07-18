from src.chat_service import build_chat_messages
from src.models import AuditResult, PageContent
from tests.test_llm_client import sample_json


def test_chat_context_limited_and_contains_audit():
    audit = AuditResult.model_validate(sample_json())
    messages = build_chat_messages(audit, [PageContent(url="u", title="t", text="x"*50000)], [{"role":"user","content":"old"}]*12, "Что внедрять?")
    assert messages[0]["role"] == "system"
    assert len([m for m in messages if m.get("content") == "old"]) == 8
    assert messages[-1]["content"] == "Что внедрять?"
