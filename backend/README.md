# Agent Core — LLMStart Backend

FastAPI-сервис: ReAct-агент, MCP tools (in-process), in-memory сессии, `POST /api/v1/chat` (JSON + SSE), `GET /api/v1/products`, Langfuse tracing.

## Архитектура

```
backend/app/
├── main.py                 # entrypoint
├── factory.py              # lifespan, CORS, routers
├── api/routes/             # chat, products, health, ready
├── services/               # agent_service, catalog_service, sse_formatter
├── agent/                  # react_runner, streaming_callbacks, prompts
├── mcp_client/             # in-process MCP handlers + LangChain tools
└── observability/          # Langfuse callbacks
```

Каталог продуктов читается через `mcp_server.data_access.catalog` (тот же `catalog.json`, что MCP tool `list_b2c_products`). Диалоговые side-effects — через MCP handlers.

## Переменные окружения

| Переменная | Обязательная | Назначение |
|------------|:---:|------------|
| `OPENAI_API_KEY` | ✅ | Chat LLM (OpenRouter) |
| `OPENAI_BASE_URL` | ❌ | Default: `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | ❌ | Default: `openai/gpt-4o-mini` |
| `DATA_DIR` | ❌ | Путь к `data/` |
| `CORS_ORIGINS` | ❌ | Default: `http://localhost:3002` |
| `LANGFUSE_PUBLIC_KEY` | ❌ | Tracing (опционально) |
| `LANGFUSE_SECRET_KEY` | ❌ | Tracing |
| `LANGFUSE_HOST` | ❌ | напр. `http://localhost:3001` |

См. корневой `.env.example`.

## Запуск

```bash
# из корня репо
make dev-backend

# или
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8003
```

При старте: RAG index (`ensure_index`) + регистрация MCP tools in-process.

Полный список make-целей: `make help`.

## API

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | MCP + LLM config ready |
| `POST` | `/api/v1/chat` | Диалог: JSON (`Accept: application/json`) или SSE (`Accept: text/event-stream`) |
| `GET` | `/api/v1/products` | B2C-каталог для виджета (пагинация) |

OpenAPI: http://localhost:8003/docs

### Пример JSON-чата

```bash
curl -s -X POST http://localhost:8003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"message":"Какой курс новичку?","channel":"web"}'
```

Продолжение диалога — передать `session_id` из ответа.

### Пример SSE-чата (виджет)

```bash
curl -N -X POST http://localhost:8003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"Какой курс новичку?","channel":"web"}'
```

События: `reasoning`, `tool`, `products`, `message`, `payment_link`, `done`, `error`.

### Пример каталога

```bash
curl -s "http://localhost:8003/api/v1/products?limit=20&offset=0"
```

## Langfuse

При заполненных `LANGFUSE_*` каждый turn пишет trace с LLM- и tool-spans. UI: http://localhost:3001 (`make up`, Langfuse **v3**).

При недоступном Langfuse диалог продолжается; ошибки только в логах.

### Проверка trace за turn (E2E)

Предусловия: `make up` (v3 stack healthy), `OPENAI_API_KEY` и `LANGFUSE_*` в `.env`.

```bash
make dev-backend
```

```bash
curl -s -X POST http://127.0.0.1:8003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"message":"Какие B2C курсы есть?","channel":"web"}'
```

В UI http://localhost:3001 → **Tracing** → Traces (подождите ~30 с):

- один trace на turn;
- metadata: `session_id` из ответа API;
- tag `channel:web`;
- nested spans: LLM generation + tool call(s).

Подробнее: [devops/README.md](../devops/README.md).

### Live-тест (опционально)

```bash
cd backend && uv run pytest -m live tests/test_langfuse_live.py
```

Требует запущенный Langfuse v3 и `LANGFUSE_*` в окружении. В CI не запускается.

### Загрузка eval-датасета в Langfuse

```bash
# из корня репо — upsert items из datasets/b2c/v2/dataset.jsonl
make upload-langfuse-dataset

# полная перезагрузка (удалить items, загрузить заново)
make reload-langfuse-dataset
```

Скрипт: [`datasets/scripts/upload_langfuse_dataset.py`](../datasets/scripts/upload_langfuse_dataset.py). Переменные: `DATASET_NAME`, `DATASET_SOURCE` (см. `make help`).

## Тесты

```bash
make lint-backend
make format-backend
make typecheck-backend
make test-backend
# или
cd backend && uv run pytest
```

CI использует мок MCP/LLM; live-тесты с реальным OpenRouter — вне scope CI.
