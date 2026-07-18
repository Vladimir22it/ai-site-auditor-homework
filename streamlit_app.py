from __future__ import annotations

import streamlit as st
from src.audit_service import run_audit
from src.chat_service import answer_chat
from src.config import load_settings
from src.crawler import crawl_site
from src.llm_client import LLMClient, LLMConfigurationError

st.set_page_config(page_title="AI Site Auditor", page_icon="🤖", layout="wide")
st.title("🤖 AI Site Auditor — аудитор возможностей внедрения AI-агентов")
st.write("Введите URL сайта компании. Приложение загрузит главную и до четырёх внутренних страниц, определит специфику бизнеса и предложит AI-агентов для продаж, сервиса, HR и операций.")

for key, default in {"audit_result": None, "pages": [], "urls": [], "chat_history": [], "warnings": []}.items():
    st.session_state.setdefault(key, default)

settings = load_settings()
if not settings.is_llm_configured:
    st.info("Для анализа настройте LLM_API_KEY, LLM_BASE_URL и LLM_MODEL в переменных окружения, Streamlit Secrets или .env. Поддерживаются ProxyAPI, RouterAI, KodikRouter и custom OpenAI-compatible API.")

col1, col2 = st.columns([3, 1])
with col1:
    url = st.text_input("URL сайта", placeholder="example.com")
with col2:
    st.write("")
    st.write("")
    analyze = st.button("Проанализировать", type="primary", use_container_width=True)

if st.button("Очистить результаты"):
    st.session_state.audit_result = None
    st.session_state.pages = []
    st.session_state.urls = []
    st.session_state.chat_history = []
    st.session_state.warnings = []
    st.rerun()

if analyze:
    try:
        progress = st.progress(0, text="Загружаем сайт…")
        crawl = crawl_site(url, settings)
        progress.progress(40, text="Готовим текст страниц…")
        llm = LLMClient(settings)
        progress.progress(65, text="Запрашиваем LLM-анализ…")
        audit = run_audit(llm, crawl.pages)
        progress.progress(100, text="Готово")
        st.session_state.audit_result = audit
        st.session_state.pages = crawl.pages
        st.session_state.urls = [p.url for p in crawl.pages]
        st.session_state.warnings = crawl.warnings
    except LLMConfigurationError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Аудит не выполнен: {exc}")

if st.session_state.warnings:
    for warning in st.session_state.warnings:
        st.warning(warning)

result = st.session_state.audit_result
if result:
    st.header("Результаты аудита")
    st.subheader(result.company_name)
    st.write(f"**Отрасль:** {result.industry}")
    st.write(result.business_description)
    st.write(f"**Уверенность анализа:** {result.confidence:.0%}")

    st.subheader("Использованные страницы")
    for used_url in st.session_state.urls:
        st.markdown(f"- {used_url}")

    st.subheader("Три приоритетных AI-агента")
    st.write(result.top_3_rationale)
    cols = st.columns(3)
    agents_by_name = {agent.name: agent for agent in result.agents}
    for idx, name in enumerate(result.top_3_agents):
        agent = agents_by_name[name]
        with cols[idx]:
            st.metric(agent.name, agent.priority_score)
            st.write(agent.benefit)

    st.subheader("Все AI-агенты")
    for agent in result.agents:
        with st.expander(f"{agent.name} — {agent.department} (приоритет {agent.priority_score}/10)"):
            st.write(f"**Проблема:** {agent.problem}")
            st.write(f"**Функция:** {agent.function}")
            st.write(f"**Сценарий:** {agent.example_scenario}")
            st.write(f"**Польза:** {agent.benefit}")
            st.write("**Данные:** " + ", ".join(agent.required_data))
            st.write("**Интеграции:** " + ", ".join(agent.integrations))
            st.write("**KPI:** " + ", ".join(agent.kpis))
            st.write(f"**Сложность:** {agent.implementation_complexity}; **MVP:** {agent.estimated_mvp_time}")
            st.write("**Риски:** " + ", ".join(agent.risks))

st.header("Чат по результатам аудита")
if not result:
    st.chat_input("Сначала завершите аудит сайта", disabled=True)
else:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    question = st.chat_input("Задайте вопрос про AI-агентов, пилот, KPI или риски")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        try:
            llm = LLMClient(settings)
            answer = answer_chat(llm, result, st.session_state.pages, st.session_state.chat_history, question)
        except Exception as exc:
            answer = f"Не удалось получить ответ: {exc}"
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
