import pytest
from src.config import Settings
from src.llm_client import LLMClient, LLMConfigurationError, LLMResponseError, parse_audit_json


def test_missing_config():
    with pytest.raises(LLMConfigurationError):
        LLMClient(Settings())


def sample_json(n=5):
    agents = []
    for i in range(n):
        agents.append({"name": f"Agent {i}", "department": "Продажи", "problem": "p", "function": "f", "example_scenario": "s", "benefit": "b", "required_data": ["d"], "integrations": ["crm"], "kpis": ["k"], "implementation_complexity": "низкая", "estimated_mvp_time": "2 недели", "priority_score": 10-i, "risks": ["r"]})
    return {"company_name": "Acme", "industry": "IT", "business_description": "desc", "products_services": ["crm"], "target_audiences": ["b2b"], "business_processes": ["sales"], "assumed_problems": ["lead"], "growth_points": ["auto"], "confidence": 0.8, "factual_basis": ["text"], "agents": agents, "top_3_agents": ["Agent 0", "Agent 1", "Agent 2"], "top_3_rationale": "best"}


def test_json_parser_with_fence():
    import json
    result = parse_audit_json("```json\n" + json.dumps(sample_json(), ensure_ascii=False) + "\n```")
    assert result.company_name == "Acme"


def test_json_parser_extracts_object_from_extra_text():
    import json
    result = parse_audit_json("Пояснение до JSON " + json.dumps(sample_json(), ensure_ascii=False) + " текст после")
    assert result.industry == "IT"


def test_pydantic_validation_fewer_agents():
    import json
    with pytest.raises(LLMResponseError):
        parse_audit_json(json.dumps(sample_json(4), ensure_ascii=False))
