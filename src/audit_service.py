from __future__ import annotations

from .llm_client import LLMClient, parse_audit_json
from .models import AgentRecommendation, AuditResult, PageContent
from .prompts import SYSTEM_PROMPT


def pages_to_context(pages: list[PageContent]) -> str:
    return "\n\n".join(f"URL: {p.url}\nTITLE: {p.title}\nTEXT: {p.text}" for p in pages)


def normalize_agents(result: AuditResult) -> AuditResult:
    unique: dict[str, AgentRecommendation] = {}
    for agent in sorted(result.agents, key=lambda a: a.priority_score, reverse=True):
        key = agent.name.strip().lower()
        if key not in unique:
            unique[key] = agent
    agents = list(unique.values())[:10]
    if len(agents) < 5:
        raise ValueError("После удаления дублей осталось меньше пяти агентов")
    result.agents = agents
    names = {a.name for a in agents}
    top = [n for n in result.top_3_agents if n in names]
    for agent in agents:
        if len(top) == 3:
            break
        if agent.name not in top:
            top.append(agent.name)
    result.top_3_agents = top[:3]
    AuditResult.model_validate(result.model_dump())
    return result


def build_audit_prompt(pages: list[PageContent]) -> str:
    return f"""Проанализируй сайт компании и верни JSON с полями схемы AuditResult. Предложи 5-10 AI-агентов с required_data, integrations, kpis и priority_score.\n\nСТРАНИЦЫ:\n{pages_to_context(pages)}"""


def run_audit(llm: LLMClient, pages: list[PageContent]) -> AuditResult:
    raw = llm.complete([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_audit_prompt(pages)}])
    return normalize_agents(parse_audit_json(raw))
