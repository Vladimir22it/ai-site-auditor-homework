from __future__ import annotations

import json

import pytest

from src.audit_service import repair_audit_json, run_audit
from src.llm_client import LLMResponseError
from src.models import AuditResult, PageContent
from tests.test_llm_client import sample_json


class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        self.calls.append(messages)
        return self.responses.pop(0)


@pytest.fixture
def proxyapi_like_response() -> dict:
    data = sample_json(5)
    data.update(
        {
            "confidence": "Высокая",
            "products_services": "Онлайн-уроки; Подготовка к экзаменам",
            "target_audiences": "Ученики\nРодители",
            "business_processes": "- Продажи\n- Обучение",
            "assumed_problems": "Ручная обработка заявок",
            "growth_points": "Автоматизация консультаций",
            "factual_basis": "На сайте указаны образовательные услуги",
            "top_3_agents": "Agent 0\nAgent 1\nAgent 2",
        }
    )
    for agent in data["agents"]:
        agent["required_data"] = "Цели ученика, уровень подготовки"
        agent["integrations"] = "CRM; Telegram"
        agent["kpis"] = "Конверсия в заявку\nСкорость ответа"
        agent["risks"] = "- Неполная база знаний\n- Ошибочные ответы"
        agent["priority_score"] = "8/10"
        agent["implementation_complexity"] = "Низкая"
    return data


def test_proxyapi_like_response_normalizes_locally(proxyapi_like_response):
    result = AuditResult.model_validate(proxyapi_like_response)
    assert result.confidence == 0.9
    assert result.products_services == ["Онлайн-уроки", "Подготовка к экзаменам"]
    assert result.agents[0].required_data == ["Цели ученика, уровень подготовки"]
    assert result.agents[0].integrations == ["CRM", "Telegram"]
    assert result.agents[0].kpis == ["Конверсия в заявку", "Скорость ответа"]
    assert result.agents[0].risks == ["Неполная база знаний", "Ошибочные ответы"]
    assert result.agents[0].priority_score == 8
    assert result.agents[0].implementation_complexity == "низкая"
    assert result.factual_basis == ["На сайте указаны образовательные услуги"]
    assert result.top_3_agents == ["Agent 0", "Agent 1", "Agent 2"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("80%", 0.8), ("8/10", 0.8), ("high", 0.9), ("medium", 0.6), ("low", 0.3)],
)
def test_confidence_formats(raw, expected):
    data = sample_json(5)
    data["confidence"] = raw
    assert AuditResult.model_validate(data).confidence == expected


def test_original_arrays_are_not_damaged():
    data = sample_json(5)
    result = AuditResult.model_validate(data)
    assert result.agents[0].required_data == ["d"]
    assert result.top_3_agents == ["Agent 0", "Agent 1", "Agent 2"]


def test_mixed_invalid_type_becomes_readable_validation_error(proxyapi_like_response):
    proxyapi_like_response["confidence"] = "очень уверенно"
    with pytest.raises(ValueError, match="confidence должен"):
        AuditResult.model_validate(proxyapi_like_response)


def test_run_audit_successful_local_normalization_without_repair(proxyapi_like_response):
    llm = FakeLLM([json.dumps(proxyapi_like_response, ensure_ascii=False)])
    result = run_audit(llm, [PageContent(url="https://example.test", text="текст")])
    assert result.confidence == 0.9
    assert len(llm.calls) == 1


def test_repair_called_only_after_local_validation_failure(proxyapi_like_response):
    bad = dict(proxyapi_like_response)
    bad["confidence"] = "непонятно"
    fixed = dict(proxyapi_like_response)
    fixed["confidence"] = 0.8
    llm = FakeLLM([json.dumps(bad, ensure_ascii=False), json.dumps(fixed, ensure_ascii=False)])
    result = run_audit(llm, [PageContent(url="https://example.test", text="текст")])
    assert result.confidence == 0.8
    assert len(llm.calls) == 2


def test_repair_called_maximum_once(proxyapi_like_response):
    bad = dict(proxyapi_like_response)
    bad["confidence"] = "непонятно"
    llm = FakeLLM([json.dumps(bad, ensure_ascii=False), json.dumps(bad, ensure_ascii=False), json.dumps(proxyapi_like_response, ensure_ascii=False)])
    with pytest.raises(LLMResponseError, match="проверка структуры не прошла"):
        run_audit(llm, [PageContent(url="https://example.test", text="текст")])
    assert len(llm.calls) == 2


def test_repair_function_is_testable(proxyapi_like_response):
    invalid = dict(proxyapi_like_response)
    invalid["confidence"] = "непонятно"
    with pytest.raises(Exception) as exc_info:
        AuditResult.model_validate(invalid)
    fixed = dict(proxyapi_like_response)
    fixed["confidence"] = "80%"
    llm = FakeLLM([json.dumps(fixed, ensure_ascii=False)])
    result = repair_audit_json(llm, invalid, exc_info.value)
    assert result.confidence == 0.8


def test_prompt_example_is_valid_and_does_not_need_repair():
    from src.audit_service import build_audit_prompt
    from src.prompts import SYSTEM_PROMPT, VALID_AUDIT_JSON_EXAMPLE_TEXT

    assert VALID_AUDIT_JSON_EXAMPLE_TEXT in SYSTEM_PROMPT
    assert VALID_AUDIT_JSON_EXAMPLE_TEXT in build_audit_prompt([PageContent(url="https://example.test", text="текст")])

    result = AuditResult.model_validate_json(VALID_AUDIT_JSON_EXAMPLE_TEXT)
    assert len(result.agents) == 5
    assert result.top_3_agents == [agent.name for agent in result.agents[:3]]

    llm = FakeLLM([VALID_AUDIT_JSON_EXAMPLE_TEXT])
    run_audit(llm, [PageContent(url="https://example.test", text="текст")])
    assert len(llm.calls) == 1
