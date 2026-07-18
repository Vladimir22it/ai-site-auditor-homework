from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


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
    implementation_complexity: Literal["низкая", "средняя", "высокая"] | str
    estimated_mvp_time: str
    priority_score: int = Field(ge=1, le=10)
    risks: list[str]


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
