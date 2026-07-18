from src.audit_service import normalize_agents, pages_to_context
from src.models import AuditResult, PageContent
from tests.test_llm_client import sample_json


def make_result(n=12):
    data = sample_json(n)
    data["agents"][1]["name"] = "Agent 0"
    data["top_3_agents"] = ["Agent 0", "Agent 2", "Agent 3"]
    
    for idx, agent in enumerate(data["agents"]):
        agent["priority_score"] = max(1, 10 - idx)
    return AuditResult.model_validate(data)


def test_limits_agents_removes_duplicates_and_top3():
    result = normalize_agents(make_result())
    assert len(result.agents) == 10
    assert len({a.name for a in result.agents}) == 10
    assert len(result.top_3_agents) == 3


def test_pages_to_context():
    ctx = pages_to_context([PageContent(url="https://e.test", title="T", text="ABC")])
    assert "ABC" in ctx and "https://e.test" in ctx
