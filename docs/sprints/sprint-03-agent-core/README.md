# Sprint 03: agent-core

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Зависит от:** [sprint-02-mcp-tools-rag](../sprint-02-mcp-tools-rag/README.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-05  
> **Закрыт:** 2026-06-05

---

## Цель спринта

Реализовать **Agent Core** в `backend/`: ReAct-агент на LangChain, MCP-клиент (stdio → `mcp_server`), in-memory сессии, `POST /api/v1/chat` с ответом **JSON** (`Accept: application/json`), форматирование под `channel`, трассировка turn'ов в Langfuse. После спринта диалог с tools доступен через HTTP (curl, будущий Telegram-бот) — без SSE и без виджета.

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `POST /api/v1/chat` + `Accept: application/json` → `200` с полями контракта (`session_id`, `message`, `reasoning`, `tools`, опционально `products`, `payment_link`, `message_html` для `channel=telegram`) | `curl` по [api-contracts.md § POST /chat](../../concept/api-contracts.md#post-apiv1chat) |
| 2 | Без `session_id` Core создаёт UUID; повторный запрос с тем же `session_id` продолжает диалог (история в памяти) | Два последовательных `curl` с одним `session_id` |
| 3 | Неизвестный/истёкший `session_id` → `400` `"Session not found or expired"` | `curl` с несуществующим UUID |
| 4 | Агент вызывает MCP tools: `search_knowledge_base` (с `segment` b2b/b2c), `list_b2c_products`, `create_payment_link`, `confirm_payment`, `save_lead` | Ответ содержит `tools[]`; интеграционный тест воронки B2C |
| 5 | Сегмент B2B/B2C определяет агент (поля `segment` в API нет); B2B-запрос → RAG с `segment=b2b` | Ручной сценарий + pytest с мок LLM или маркер `@pytest.mark.live` |
| 6 | Воронка B2C end-to-end через JSON API: вопрос → подбор продукта → мок-ссылка → «оплатил» → лид в `data/leads.txt` (6 полей) | pytest + проверка append в tmp `DATA_DIR` |
| 7 | MCP-клиент: subprocess `mcp_server` при старте Core; `GET /ready` → `200` когда MCP и конфиг валидны | `curl http://localhost:8000/ready` после `make dev-backend` |
| 8 | Langfuse: один trace на turn с LLM- и tool-spans (видно в UI :3001) | Ручная проверка после диалога с `LANGFUSE_*` в `.env` |
| 9 | При недоступном Langfuse диалог не падает (ошибки только в логах) | Остановить Langfuse / неверный ключ → `POST /chat` всё ещё `200` |
| 10 | `make test` / `make ci` включают тесты backend (unit + integration с мок MCP/LLM) | `make ci` |
| 11 | Структура `backend/` соответствует [architecture.md § Agent Core](../../concept/architecture.md#agent-core-backend--внутренняя-структура) | Сравнение дерева каталогов |

---

## Scope

### В scope

| Область | Содержание |
|---------|------------|
| `backend/app/` | Расширение FastAPI: роуты, сервисы, агент, MCP-клиент, observability |
| `POST /api/v1/chat` | Только **JSON**-ветка (`Accept: application/json`); валидация Pydantic по контракту |
| `GET /ready` | Readiness: MCP subprocess жив, обязательные env заданы |
| ReAct-агент | LangChain `create_agent` (или эквивалент v1 API), system prompt, привязка 5 MCP tools |
| `mcp_client/` | stdio-сессия к `mcp_server`; lifecycle на startup/shutdown FastAPI |
| `services/session_store.py` | `dict[session_id → Session]`, TTL **24 ч**, sweep по активности |
| `services/channel_formatter.py` | `web` vs `telegram`: `message_html`, экранирование для Telegram HTML |
| `services/agent_service.py` | Оркестрация turn: история → ReAct → маппинг в JSON-ответ |
| `observability/langfuse.py` | Callback / OTEL для traces, generations, tool spans |
| `core/config.py` | Fail-fast: `OPENAI_API_KEY`, `OPENAI_MODEL`, `LANGFUSE_*` (опционально с warn) |
| Промпты | Роль продавца llmstart.ru, сегмент B2B/B2C, воронка, политика «только через tools» |
| Тесты | Unit (session, formatter, schemas); integration (TestClient + мок MCP/LLM); E2E воронка с tmp `data/` |
| Makefile | Цели без изменения контракта корня: тесты backend уже в `make test-backend` / `make ci` |
| Документация | `backend/README.md`: env, запуск, примеры `curl`, Langfuse |

### Вне scope

| Область | Спринт |
|---------|--------|
| SSE-поток (`Accept: text/event-stream`) | sprint-04 |
| `GET /api/v1/products` | sprint-04 |
| Next.js виджет, UI reasoning/tools | sprint-05 |
| Telegram-бот (aiogram), handoff deep link | sprint-06 |
| Прямое чтение `data/` из Core (только MCP) | — |
| Postgres/Redis для сессий | v1.0 |
| Guardrails, rate limits | v0.2 |
| HTTP-транспорт MCP | post-MVP |

---

## Контракт `POST /chat` (JSON, MVP)

Согласовано с [api-contracts.md](../../concept/api-contracts.md) и [architecture.md § Сессии](../../concept/architecture.md#сессии):

**Запрос:**

```json
{
  "message": "Какой курс выбрать новичку?",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "channel": "web"
}
```

| Поле | Правило |
|------|---------|
| `message` | 1–4000 символов, обязательное |
| `session_id` | UUID, опционально — создаётся Core |
| `channel` | `web` \| `telegram`, обязательное |

**Ответ `200` (ключевые поля):** `session_id`, `channel`, `message`, `message_html` (для telegram), `reasoning`, `tools[]`, `products` (nullable), `payment_link` (nullable).

**Ошибки:** `422` (схема), `400` (сессия), `503` (OpenRouter / MCP).

> SSE-события (`reasoning`, `tool`, `products`, `message`, `payment_link`, `done`, `error`) — реализация в sprint-04; в sprint-03 достаточно заглушки `406` или `501` при `Accept: text/event-stream`, либо явный `400` с понятным `detail` — зафиксировать в OpenAPI.

---

## Шаги реализации

### 1. Зависимости и каркас backend

- Добавить в `backend/pyproject.toml`: `langchain`, `langchain-openai`, `mcp` (SDK), `langfuse` (SDK), `markdown` / `bleach` (HTML для Telegram).
- Развернуть структуру по architecture:

```
backend/app/
├── main.py                    # lifespan: MCP startup/shutdown
├── core/
│   └── config.py              # Settings, fail-fast
├── api/
│   ├── routes/
│   │   ├── chat.py            # POST /api/v1/chat (JSON)
│   │   ├── health.py          # уже есть
│   │   └── ready.py           # GET /ready
│   └── schemas/
│       ├── chat.py            # ChatRequest, ChatResponse, ToolStatus
│       └── common.py          # ErrorDetail
├── services/
│   ├── session_store.py
│   ├── channel_formatter.py
│   └── agent_service.py
├── agent/
│   ├── react_runner.py        # create_agent + invoke
│   └── prompts.py             # system + segment/funnel instructions
├── mcp_client/
│   ├── client.py              # stdio session, list_tools, call_tool
│   └── tool_adapter.py        # MCP tools → LangChain StructuredTool
└── observability/
    └── langfuse.py            # callbacks, trace metadata (session_id, channel)
```

- `main.py`: `lifespan` — старт MCP subprocess, регистрация роутеров `/api/v1`.

### 2. Конфигурация (fail-fast)

- Расширить `Settings`: `openai_api_key`, `openai_base_url`, `openai_model`, `langfuse_public_key`, `langfuse_secret_key`, `langfuse_host`, `session_ttl_hours` (default 24), `mcp_server_module` (default `mcp_server`), `data_dir`.
- При старте: без `OPENAI_API_KEY` — процесс не поднимается; без Langfuse keys — WARN + no-op callback.

### 3. MCP-клиент (stdio)

- `mcp_client/client.py`:
  - Запуск: `uv run python -m mcp_server` (cwd корень репо, env `DATA_DIR`, `OPENAI_*` для embeddings в subprocess).
  - `async with` / singleton на lifespan приложения.
  - Методы: `list_tools()`, `call_tool(name, arguments)`, health-check для `/ready`.
- `tool_adapter.py`: обёртка MCP tool definitions в LangChain tools с передачей `session_id` в `create_payment_link` / `confirm_payment` / `save_lead` (inject из контекста turn, не от LLM).

### 4. In-memory сессии

- `Session`: `id`, `channel`, `messages[]` (LangChain message history), `created_at`, `last_active_at`, опционально `metadata` (последний `segment`, pending product).
- `session_store.py`:
  - `get_or_create(session_id?, channel)` → `(session, created)`.
  - `touch(session_id)` при каждом turn.
  - Фоновый sweep / lazy purge: TTL 24 ч с `last_active_at`.
  - `get(session_id)` → `None` если нет или expired → роут отдаёт `400`.

### 5. ReAct-агент и промпты

- `prompts.py`:
  - Роль: консультант llmstart.ru (B2C курсы, B2B корп. обучение и разработка).
  - Сегмент: агент сам выбирает `b2b` / `b2c` для `search_knowledge_base`.
  - Воронка: уточнение → каталог/RAG → при намерении купить — `create_payment_link`; при «оплатил» — `confirm_payment` → сбор контактов → `save_lead`.
  - Запрет: не выдумывать цены/продукты — только `list_b2c_products` и RAG.
- `react_runner.py`:
  - LLM: `ChatOpenAI` с `base_url=OPENAI_BASE_URL`, timeout.
  - `create_agent(model, tools, system_prompt)`.
  - `run_turn(session, user_message)` → структура: финальный текст, reasoning (из промежуточных шагов или отдельного поля), список tool calls со статусами.

### 6. Agent service и channel formatter

- `agent_service.py`:
  - Загрузка истории сессии, append user message.
  - Вызов `react_runner`, обновление истории assistant/tool messages.
  - Извлечение `products` / `payment_link` из результатов tools для JSON-ответа.
- `channel_formatter.py`:
  - `web`: `message` plain/markdown; `message_html` опционально.
  - `telegram`: безопасный HTML (`<p>`, `<b>`, `<a href>`), `message_html` обязателен.

### 7. HTTP: `POST /api/v1/chat` (JSON)

- `api/routes/chat.py`:
  - Парсинг `Accept`: если `application/json` — синхронный turn, полный JSON-ответ.
  - Если `text/event-stream` — **не реализовывать** (заглушка до sprint-04).
  - Маппинг исключений: OpenRouter → `503`, MCP → `503`, бизнес → `400`.
- Pydantic-схемы зеркалят [api-contracts.md](../../concept/api-contracts.md).

### 8. `GET /ready`

- Проверка: MCP client connected, `list_tools()` возвращает 5 tools, LLM config present.
- `200`: `{"status": "ready", "mcp_tools": 5}`; иначе `503`.

### 9. Langfuse observability

- `observability/langfuse.py`:
  - Инициализация Langfuse client из env.
  - Callback handler на каждый turn: `trace_id` = `session_id` или nested span per message.
  - Метаданные: `channel`, `session_id` (без PII в attributes).
  - Tool calls как child spans.
- Сбой экспорта — log `WARNING`, не пробрасывать в HTTP-ответ.

### 10. Тесты и качество

- **Unit:** `session_store` (TTL, get_or_create), `channel_formatter` (HTML escape), schemas validation.
- **Integration:** TestClient + `unittest.mock` / фикстура fake MCP (возврат фиксированных tool results) + fake LLM (возврат scripted tool_calls).
- **Integration (воронка):** сценарий «курс → оплата → лид» с tmp `DATA_DIR` и реальным MCP subprocess (маркер `integration`).
- **Live (опционально):** `@pytest.mark.live` — реальный OpenRouter + Langfuse, skip без ключей.
- Цикл Edit → Sanitize → Verify на каждый модуль; `make ci` зелёный.

### 11. Документация

- `backend/README.md`: архитектура слоёв, env, `make dev-backend`, примеры `curl` (JSON), просмотр trace в Langfuse UI.
- Обновить корневой `README.md`: секция Agent Core, ссылка на `POST /chat`.
- OpenAPI `/docs` — актуальные схемы запроса/ответа.

---

## Зависимости и env

| Переменная | Компонент | Назначение |
|------------|-----------|------------|
| `OPENAI_API_KEY` | backend | Chat LLM (OpenRouter) |
| `OPENAI_BASE_URL` | backend, mcp_server (subprocess) | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | backend | Chat-модель, напр. `openai/gpt-4o-mini` |
| `DATA_DIR` | mcp_server subprocess | Путь к `data/` |
| `LANGFUSE_PUBLIC_KEY` | backend | Tracing |
| `LANGFUSE_SECRET_KEY` | backend | Tracing |
| `LANGFUSE_HOST` | backend | `http://localhost:3001` (compose) или Cloud |

Полный список — [.env.example](../../../.env.example).

---

## Риски и допущения

| Риск | Митигация |
|------|-----------|
| LangChain API меняется (`create_agent` vs legacy ReAct) | Перед кодом — skill `langchain-fundamentals` + MCP `langchain-docs` |
| Subprocess MCP падает при старте | `/ready` + `503` на `/chat`; лог с stderr subprocess |
| Flaky live LLM в CI | CI только моки; live-тесты за маркером |
| Долгий cold start (reindex Chroma) | MCP уже индексирует при старте (sprint-02); документировать первый запрос |
| `session_id` в tool args | Inject в adapter, не полагаться на LLM |

**Допущения:**

- Один процесс backend = один MCP subprocess (dev/MVP).
- История сессии — список LangChain messages в памяти; лимит длины — YAGNI до v0.2.
- Reasoning в JSON — агрегат из шагов агента (краткий summary), не обязательно token-level chain-of-thought.

---

## Skills

Перед реализацией прочитать:

- `langchain-fundamentals` — `create_agent`, tools, middleware
- `fastapi-templates` — роутеры, lifespan, DI
- `modern-python`, `uv-package-manager` — зависимости backend
- `python-testing-patterns` — TestClient, мок subprocess/LLM
- MCP `langchain-docs` — актуальный API агента и tool binding
- MCP `langfuse-docs` — callback / tracing с LangChain

---

## Итог (заполняется после закрытия)

Sprint закрыт 2026-06-05. Agent Core: ReAct, `POST /api/v1/chat` (JSON), сессии, Langfuse (optional), in-process tools через `mcp_server`; 14 тестов, live-чат с OpenRouter.

Подробности: [summary.md](./summary.md).
