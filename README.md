# AI Site Auditor — аудитор возможностей внедрения AI-агентов

Streamlit-приложение для домашнего задания курса «AI-агенты для продаж, сервиса и HR». Пользователь вводит сайт компании, приложение безопасно загружает главную и до четырёх внутренних HTML-страниц, очищает текст, отправляет его в OpenAI-compatible LLM и показывает 5–10 релевантных AI-агентов, top 3 и чат по результатам.

## Возможности
- Русский интерфейс Streamlit без отдельного backend/frontend.
- SSRF-защита: только http/https, запрет localhost, private, reserved, link-local IP и проверка после redirect.
- Извлечение текста через BeautifulSoup и Trafilatura, лимиты 10 000 символов на страницу и 40 000 суммарно.
- Приоритетный выбор внутренних страниц: about, services, products, contacts, pricing, team и русские аналоги.
- Поддержка ProxyAPI, RouterAI, KodikRouter и custom OpenAI-compatible провайдера.
- Pydantic-валидация JSON, удаление дублей, ограничение 5–10 агентов, выбор top 3.
- Чат после аудита с ограниченной историей.

## Скриншоты
См. `docs/SCREENSHOTS.md`. Перед сдачей после запуска приложения добавьте реальные скриншоты: стартовый экран, результат аудита, список страниц, top 3, чат.

## Архитектура
`streamlit_app.py` управляет UI и `session_state`. `src/crawler.py` загружает страницы и применяет проверки из `src/url_security.py`. `src/content_extractor.py` очищает HTML. `src/audit_service.py` формирует основной запрос, `src/llm_client.py` вызывает LLM и парсит JSON, `src/chat_service.py` собирает контекст чата.

## Структура репозитория
```text
streamlit_app.py
src/ config.py models.py url_security.py crawler.py content_extractor.py llm_client.py prompts.py audit_service.py chat_service.py
tests/ fixtures/ ...
docs/ TEST_PLAN.md TEST_RESULTS.md DEMO_SCRIPT.md SCREENSHOTS.md SUBMISSION_CHECKLIST.md
.devcontainer/devcontainer.json
.github/workflows/ci.yml
.streamlit/config.toml
.env.example .gitignore AGENTS.md README.md requirements.txt LICENSE
```

## Локальная установка
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_app.py
```

## Codespaces
Откройте репозиторий в GitHub Codespaces. Devcontainer установит Python-зависимости командой `pip install -r requirements.txt`, затем установит Chromium и системные зависимости Playwright командой `python -m playwright install --with-deps chromium`. HTTP-режим остаётся основным: по умолчанию `ENABLE_BROWSER_FETCH=false`, поэтому браузерный fallback включайте только при необходимости для JS-сайтов. Секреты задавайте через переменные окружения Codespaces или `.env` только локально.

## Настройка LLM-провайдеров
Переменные читаются в порядке: environment → `st.secrets` → `.env`.

### ProxyAPI
```env
LLM_PROVIDER=proxyapi
LLM_API_KEY=...
LLM_BASE_URL=https://openai.api.proxyapi.ru/v1
LLM_MODEL=openai/gpt-4o-mini
```

ProxyAPI настроен через универсальный OpenAI-compatible endpoint. Через него можно использовать модели разных провайдеров, указывая соответствующие идентификаторы моделей с префиксом провайдера, например `openai/gpt-4o-mini`.

### RouterAI
```env
LLM_PROVIDER=routerai
LLM_API_KEY=...
LLM_BASE_URL=https://routerai.ru/api/v1
LLM_MODEL=идентификатор-модели-из-каталога
```

### KodikRouter
```env
LLM_PROVIDER=kodikrouter
LLM_API_KEY=...
LLM_BASE_URL=https://api.kodikrouter.ru/v1
LLM_MODEL=идентификатор-модели-из-каталога
```

### Custom OpenAI-compatible
```env
LLM_PROVIDER=custom
LLM_API_KEY=...
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=your-model
```

## Безопасная работа с ключами
Не коммитьте `.env` и `.streamlit/secrets.toml`: они добавлены в `.gitignore`. В Streamlit Community Cloud используйте Secrets. В `.env.example` используются только безопасные значения-примеры.

## Параметры crawler
- `HTTP_TIMEOUT_SECONDS` — timeout HTTP-запросов.
- `MAX_PAGES` — максимум страниц вместе с главной, не больше 5.
- `MAX_INTERNAL_PAGES` — максимум внутренних страниц, не больше 4.
- `MAX_PAGE_CHARS` — максимум символов с одной страницы, не больше 10 000.
- `MAX_TOTAL_CHARS` — максимум символов суммарно, не больше 40 000.
- `MIN_TEXT_CHARS_FOR_BROWSER_FALLBACK` — порог малого текста главной страницы для Playwright fallback.

## Запуск тестов и проверок
```bash
ruff check .
pytest -q
python -m compileall src streamlit_app.py
```

## Публикация в Streamlit Community Cloud
Создайте приложение из GitHub-репозитория, укажите `streamlit_app.py`, добавьте Secrets `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, при необходимости `LLM_PROVIDER` и `ENABLE_BROWSER_FETCH=false`.

## Ограничения
Проект не сохраняет историю в БД, анализирует только глубину 1 и максимум 5 страниц. Playwright fallback опционален и не обязателен для базовой работы. Автотесты не выполняют реальные HTTP/LLM-запросы.

## Тестовые сайты
Для ручной проверки используйте публичные сайты компаний с HTML-страницами: сайт курса/школы, локального сервиса, B2B SaaS. Не используйте личные кабинеты и закрытые страницы.
