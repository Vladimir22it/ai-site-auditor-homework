from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

LIST_SEPARATORS_RE = re.compile(r"(?:\r?\n)+|;+")
BULLET_RE = re.compile(r"^\s*(?:[-*•—–]|\d+[.)])\s*")


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    raw_items: list[Any]
    if isinstance(value, list):
        raw_items = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        parts = LIST_SEPARATORS_RE.split(text)
        raw_items = []
        for part in parts:
            cleaned = BULLET_RE.sub("", part).strip()
            if cleaned:
                raw_items.append(cleaned)
    else:
        raw_items = [value]

    result: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        if item is None:
            continue
        text = BULLET_RE.sub("", str(item)).strip()
        if not text:
            continue
        key = re.sub(r"\s+", " ", text).casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def normalize_confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("confidence должен быть числом от 0 до 1, а не boolean")
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        text = value.strip().lower().replace(",", ".")
        categories = {
            "высокая": 0.9,
            "высокий": 0.9,
            "high": 0.9,
            "средняя": 0.6,
            "средний": 0.6,
            "medium": 0.6,
            "низкая": 0.3,
            "низкий": 0.3,
            "low": 0.3,
        }
        if text in categories:
            return categories[text]
        if text.endswith("%"):
            return max(0.0, min(1.0, float(text[:-1].strip()) / 100))
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*([0-9]+(?:\.[0-9]+)?)", text)
        if match:
            denominator = float(match.group(2))
            if denominator == 0:
                raise ValueError("confidence не может быть дробью с нулевым знаменателем")
            return max(0.0, min(1.0, float(match.group(1)) / denominator))
        try:
            return max(0.0, min(1.0, float(text)))
        except ValueError as exc:
            raise ValueError("confidence должен быть числом 0-1, процентом, дробью вида 8/10 или категорией high/medium/low") from exc
    raise ValueError("confidence должен быть числом от 0 до 1")


def normalize_priority_score(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("priority_score должен быть числом от 1 до 10")
    if isinstance(value, int | float):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip().lower().replace(",", ".")
        match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*10", text)
        number = float(match.group(1)) if match else float(text)
    else:
        raise ValueError("priority_score должен быть числом от 1 до 10")
    return int(round(max(1.0, min(10.0, number))))


def normalize_complexity(value: Any) -> str:
    text = str(value).strip().lower()
    mapping = {
        "низкая": "низкая",
        "низкий": "низкая",
        "low": "низкая",
        "средняя": "средняя",
        "средний": "средняя",
        "medium": "средняя",
        "высокая": "высокая",
        "высокий": "высокая",
        "high": "высокая",
    }
    return mapping.get(text, text)


class AgentRecommendation(BaseModel):
    name: str
    department: str
    problem: str
    function: str
    example_scenario: str
    benefit: str
    required_data: list[str]
    integrations: list[str]
    kpis: list[str]
    implementation_complexity: Literal["низкая", "средняя", "высокая"]
    estimated_mvp_time: str
    priority_score: int = Field(ge=1, le=10)
    risks: list[str]

    _normalize_agent_lists = field_validator("required_data", "integrations", "kpis", "risks", mode="before")(normalize_string_list)
    _normalize_priority_score = field_validator("priority_score", mode="before")(normalize_priority_score)
    _normalize_complexity = field_validator("implementation_complexity", mode="before")(normalize_complexity)


class AuditResult(BaseModel):
    company_name: str
    industry: str
    business_description: str
    products_services: list[str]
    target_audiences: list[str]
    business_processes: list[str]
    assumed_problems: list[str]
    growth_points: list[str]
    confidence: float = Field(ge=0, le=1)
    factual_basis: list[str]
    agents: list[AgentRecommendation]
    top_3_agents: list[str]
    top_3_rationale: str

    _normalize_audit_lists = field_validator(
        "products_services",
        "target_audiences",
        "business_processes",
        "assumed_problems",
        "growth_points",
        "factual_basis",
        "top_3_agents",
        mode="before",
    )(normalize_string_list)
    _normalize_confidence = field_validator("confidence", mode="before")(normalize_confidence)

    @field_validator("agents")
    @classmethod
    def validate_agent_count(cls, value: list[AgentRecommendation]) -> list[AgentRecommendation]:
        if len(value) < 5:
            raise ValueError("Модель вернула меньше пяти AI-агентов")
        return value

    @model_validator(mode="after")
    def validate_top3(self) -> "AuditResult":
        names = {agent.name for agent in self.agents}
        if len(self.top_3_agents) != 3:
            raise ValueError("Должно быть выбрано ровно три приоритетных AI-агента")
        missing = [name for name in self.top_3_agents if name not in names]
        if missing:
            raise ValueError(f"Top 3 содержит неизвестных агентов: {', '.join(missing)}")
        return self


class PageContent(BaseModel):
    url: str
    title: str = ""
    text: str
