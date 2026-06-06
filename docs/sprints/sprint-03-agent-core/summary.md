# Summary: Sprint 03 — agent-core

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-05

---

## Что реализовано

- **`backend/` Agent Core:** ReAct (`create_agent`), `POST /api/v1/chat` (JSON), `GET /ready`, in-memory сессии (TTL 24 ч)
- **Tools:** in-process вызов handlers `mcp_server` (`sync_tools.py`) — без deadlock LangGraph ↔ async MCP
- **Слои:** `agent/`, `services/`, `mcp_client/`, `observability/`, `api/schemas`, `factory.py` с lifespan
- **Конфиг:** `.env` из корня репо (`REPO_ROOT/.env`), fail-fast `OPENAI_API_KEY`, RAG index при старте
- **Langfuse:** опциональные callbacks (`langfuse.langchain.CallbackHandler`); сбой не блокирует чат
- **Channel:** `web` / `telegram` (`message_html` через bleach + markdown)
- **SSE:** заглушка `501` до sprint-04
- **Тесты:** 14 pytest (session, formatter, chat contract, ready, B2B mock)
- **Документация:** `backend/README.md`, секция Agent Core в корневом README

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| MCP stdio subprocess на каждый tool call | In-process handlers + `llmstart-agent-mcp-server` как зависимость | Deadlock sync route + LangGraph threads ↔ async MCP event loop |
| MCP subprocess при старте для tools | RAG `ensure_index` при lifespan; `/ready` по `tools_ready` | Один процесс, быстрее старт, стабильнее на Windows |
| E2E воронка B2C в backend pytest | Live-проверка + E2E на уровне `mcp_server` (sprint-02) | CI без live LLM; воронка tools проверена в mcp_server |
| Langfuse trace в DoD | Код интеграции готов; UI — ручная проверка | Зависит от `LANGFUSE_*` и поднятого Langfuse |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `sync_tools.execute_tool()` вместо `call_tool_sync` через MCP stdio | Устранение deadlock; тот же код handlers, та же граница `mcp_server` |
| `TurnContext` в module-level + ContextVar | Inject `session_id` / `channel` в tools из worker-потоков LangGraph |
| `FakeReactRunner` в тестах | CI без OpenRouter; контракт API проверяется детерминированно |
| Зависимость `llmstart-agent-mcp-server` path `../mcp_server` | Shared handlers и RAG без дублирования |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `OPENAI_API_KEY is required` при `make dev-backend` | `env_file=(REPO_ROOT / ".env", ".env")` в backend config |
| `ReadTimeout` / зависание на `/chat` | Deadlock async MCP → sync in-process handlers |
| `StructuredTool does not support sync invocation` | Sync `func` в tool adapter |
| Зависший процесс на :8000 после deadlock | Перезапуск backend; при необходимости uvicorn без `--reload` |
| `ensure_index()` возвращает `None` | `return 0` в `ensure_rag_index()` |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `POST /chat` JSON контракт | ✅ pytest + live `200` |
| 2 | Создание / reuse `session_id` | ✅ pytest |
| 3 | Неизвестная сессия → `400` | ✅ pytest |
| 4 | MCP tools в ответе | ✅ live (`list_b2c_products`, RAG); все 5 через handlers |
| 5 | B2B → `search_knowledge_base` | ✅ pytest (mock) + live |
| 6 | Воронка B2C → лид | ⚠️ mcp_server E2E; live воронка — ручная |
| 7 | `GET /ready`, tools готовы | ✅ in-process, `mcp_tools: 5` |
| 8 | Langfuse trace | ⚠️ код готов; UI — при настроенном Langfuse |
| 9 | Langfuse down → чат жив | ✅ optional callback |
| 10 | `make test-backend` / CI | ✅ 14 passed |
| 11 | Структура `backend/` | ✅ по architecture.md |

---

## Что дальше

- **Sprint 04:** SSE `POST /chat`, `GET /products`, контракты для виджета
- Перед виджетом: стабильный `make dev-backend` (при зависаниях — uvicorn без `--reload`)

---

## Ссылки

- [Sprint 04: api-stream-catalog](../sprint-04-api-stream-catalog/README.md)
- [backend/README.md](../../../backend/README.md)
- [mcp_server/README.md](../../../mcp_server/README.md)
