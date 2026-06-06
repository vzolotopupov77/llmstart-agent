# Sprint 04: api-stream-catalog

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Зависит от:** [sprint-03-agent-core](../sprint-03-agent-core/README.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-05  
> **Закрыт:** 2026-06-05

---

## Цель спринта

Расширить **Agent Core** (`backend/`) до полного публичного API MVP: **`POST /api/v1/chat` с SSE** (`Accept: text/event-stream`) для веб-виджета и **`GET /api/v1/products`** для витрины B2C-каталога. JSON-ветка `/chat` (sprint-03) сохраняется без регрессий. После спринта backend готов к интеграции виджета (sprint-05) и Telegram-бота (sprint-06) — оба потребляют стабильные контракты из [api-contracts.md](../../concept/api-contracts.md).

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `POST /api/v1/chat` + `Accept: text/event-stream` + `channel: web` → `200`, заголовки SSE (`Content-Type: text/event-stream`, `Cache-Control: no-cache`) | `curl -N` по [api-contracts.md § SSE](../../concept/api-contracts.md#ответ-при-accept-textevent-stream) |
| 2 | SSE-поток содержит события в корректном порядке: `reasoning` → `tool` (`started`/`done`) → опционально `products`, `message` (delta), `payment_link` → `done` | Парсинг потока в pytest или ручной `curl -N` с мок-агентом |
| 3 | Событие `done` включает `session_id` и полный `message`; сессия сохраняется в `session_store` как в JSON-ветке | Два SSE-turn с одним `session_id` |
| 4 | Ошибка до старта стрима → JSON `detail` (`400`/`503`); ошибка mid-stream → `event: error` + закрытие потока | Тесты: неизвестный `session_id`, недоступный LLM (мок) |
| 5 | `POST /api/v1/chat` + `Accept: application/json` — без регрессий sprint-03 | Существующие `test_chat.py` зелёные |
| 6 | `GET /api/v1/products?limit=&offset=` → `200` с `items`, `total`, `limit`, `offset`; 6 продуктов из `data/b2c/catalog.json` | `curl` + pytest |
| 7 | Пагинация: `limit` default 20, max 100; `offset` default 0; пустая страница → `200`, `items: []` | pytest граничные значения, `422` на невалидные query |
| 8 | Каталог `/products` и MCP `list_b2c_products` — один источник (`catalog.json` через `mcp_server.data_access.catalog`) | Сравнение `code`/`price` в ответах |
| 9 | CORS: `http://localhost:3000` разрешён для `GET`/`POST` API v1 (подготовка виджета) | Preflight `OPTIONS` или TestClient |
| 10 | OpenAPI `/docs` отражает оба Accept для `/chat`, схемы SSE-событий (описание), `GET /products` | Ручной просмотр |
| 11 | `make test-backend` / `make ci` зелёные (unit + integration, без live LLM в CI) | `make ci` |
| 12 | `backend/README.md` обновлён: примеры `curl` SSE и `GET /products` | Ручной просмотр |

---

## Scope

### В scope

| Область | Содержание |
|---------|------------|
| `POST /api/v1/chat` (SSE) | Ветка `Accept: text/event-stream`; `StreamingResponse` / `EventSourceResponse` |
| SSE-события | `reasoning`, `tool`, `products`, `message`, `payment_link`, `done`, `error` — по [api-contracts.md](../../concept/api-contracts.md) |
| `GET /api/v1/products` | Пагинированный B2C-каталог для виджета |
| `api/schemas/` | `ProductListResponse`, SSE payload-модели (`ReasoningEvent`, `ToolEvent`, …) |
| `api/routes/products.py` | Новый роутер; регистрация в `factory.py` |
| `services/agent_service.py` | Метод `run_chat_turn_stream()` — оркестрация turn + yield событий |
| `services/catalog_service.py` | Чтение каталога через `mcp_server` data access, slice по `limit`/`offset` |
| `agent/react_runner.py` | Колбэки / streaming-хуки: `tool started`/`done`, чанки `message` |
| `services/sse_formatter.py` | Сериализация `event:` / `data:` строк, валидация JSON payload |
| CORS middleware | `CORSMiddleware`, origin `http://localhost:3000` из конфига |
| Тесты | SSE contract (FakeReactRunner), products pagination, JSON regression |
| Документация | `backend/README.md`, ссылки в корневом README |

### Вне scope

| Область | Спринт / версия |
|---------|-----------------|
| Next.js виджет, UI reasoning/tools | sprint-05 |
| Telegram-бот (aiogram), deep link handoff | sprint-06 |
| Token-level LLM streaming (каждый токен от OpenRouter) | YAGNI; достаточно чанков финального `message` |
| `description` в `GET /products` | Не в контракте MVP |
| Production CORS (llmstart.ru) | post-MVP |
| WebSocket вместо SSE | — |
| Изменение MCP tools / RAG | sprint-02 (стабильно) |
| Postgres, rate limits | v1.0 / v0.2 |

---

## Контракты API (MVP)

Источник истины: [api-contracts.md](../../concept/api-contracts.md). Ключевые точки спринта:

### `POST /api/v1/chat` — SSE

**Запрос** — тот же, что в sprint-03 (`message`, `session_id?`, `channel`).

**Ответ** — последовательность SSE-событий; финал — `event: done`.

| event | data (ключевые поля) | Когда |
|-------|----------------------|-------|
| `reasoning` | `{ "text": string }` | После анализа turn (до или параллельно tools) |
| `tool` | `{ "name", "status", "title" }` | `status`: `started` → `done` \| `error` |
| `products` | `{ "items": Product[] }` | Если turn вернул продукты |
| `message` | `{ "delta": string }` | Чанки финального текста (1+ событий) |
| `payment_link` | `{ "url": string }` | Если `create_payment_link` в turn |
| `done` | `{ "session_id", "message" }` | Завершение; поток закрывается |
| `error` | `{ "detail": string }` | Ошибка генерации mid-stream |

**`tool.status` в SSE:** `started` | `done` | `error` (в JSON-ветке по-прежнему только `done` \| `error`).

### `GET /api/v1/products`

```json
{
  "items": [{ "code", "title", "price", "currency" }],
  "total": 6,
  "limit": 20,
  "offset": 0
}
```

Query: `limit` (1–100, default 20), `offset` (≥ 0, default 0).

### Product (общая схема)

`code`, `title`, `price` (int, копейки), `currency` (`RUB`) — для SSE `products`, JSON `/chat` и `GET /products`.

---

## Шаги реализации

### 1. Схемы и общие типы

- В `api/schemas/chat.py` — SSE payload-модели: `SseReasoningData`, `SseToolData` (со `status: started|done|error`), `SseProductsData`, `SseMessageData`, `SsePaymentLinkData`, `SseDoneData`, `SseErrorData`.
- Новый `api/schemas/products.py`: `ProductListResponse`, `ProductListQuery` (Pydantic для query validation).
- Переиспользовать `ProductItem` из chat-схем (или вынести в `api/schemas/product.py` при дублировании).

### 2. Catalog service

- `services/catalog_service.py`:
  - `list_products(limit: int, offset: int) -> ProductListResponse`.
  - Источник: `mcp_server.data_access.catalog.list_products()` (тот же `catalog.json`, что MCP tool).
  - Маппинг полей: только `code`, `title`, `price`, `currency` (без `description`).
  - `total` = len(full list); slice `[offset:offset+limit]`.
- Обработка `CatalogError` / отсутствия файла → `503` с `detail` «Catalog unavailable» (редкий dev-случай).

### 3. `GET /api/v1/products`

- `api/routes/products.py`:
  - `GET /products` с query-параметрами через Pydantic `Query` или dependency.
  - `422` на `limit < 1`, `limit > 100`, `offset < 0`.
  - Регистрация роутера в `factory.py` под prefix `/api/v1`.
- Smoke-тест: 6 items, pagination `offset=2&limit=2` → 2 items, `total=6`.

### 4. SSE formatter

- `services/sse_formatter.py`:
  - `format_sse_event(event_type: str, data: BaseModel) -> str` → строка `event: …\ndata: …\n\n`.
  - `json.dumps` с `ensure_ascii=False` для кириллицы.
  - Generator-helper `stream_events(events: Iterable[tuple[str, BaseModel]])` для тестов.

### 5. Streaming в agent layer

- Расширить `ReactRunner` (или добавить `StreamingReactRunner`):
  - Принимать `on_tool_start(name)`, `on_tool_end(name, status)` колбэки через LangChain `BaseCallbackHandler`.
  - Эмитить `tool started` при `on_tool_start`, `tool done`/`error` при `on_tool_end`.
  - После `invoke` — извлечь `reasoning`, `products`, `payment_link`, `final_message` (логика `_parse_turn` без дублирования).
- **Message delta (MVP):** разбить `final_message` на чанки (по предложениям или фиксированному размеру ~80–120 символов) — не требовать token-stream от OpenRouter.
- Сохранить sync `run_turn()` для JSON-ветки; streaming-обёртка вызывает тот же граф с колбэками.

### 6. Agent service — SSE orchestration

- `AgentService.run_chat_turn_stream()`:
  - Async generator `AsyncIterator[str]` (или sync generator + `StreamingResponse`).
  - Валидация сессии / `tools_ready` **до** yield первого события (иначе JSON-ошибка).
  - Порядок yield:
    1. `reasoning`
    2. Для каждого tool: `started` → `done`/`error`
    3. `products` (если есть)
    4. `message` delta(s)
    5. `payment_link` (если есть)
    6. `done` с `session_id` и полным `message`
  - Обновление `session_store` — после успешного turn (как в `run_chat_turn`).
  - При исключении после начала стрима — `event: error`, затем stop.

### 7. HTTP: `POST /api/v1/chat` — ветка SSE

- `api/routes/chat.py`:
  - Убрать заглушку `501`.
  - При `Accept: text/event-stream` → `StreamingResponse(agent_service.run_chat_turn_stream(...), media_type="text/event-stream")`.
  - Заголовки: `Cache-Control: no-cache`, `Connection: keep-alive` (FastAPI/Starlette defaults + явные).
  - При `Accept: application/json` — без изменений логики sprint-03.
  - Неподдерживаемый `Accept` → `406`.
- Ошибки до стрима (`SessionNotFoundError`, `McpUnavailableError`, `LlmUnavailableError`) — стандартный JSON через `HTTPException` (не SSE).

### 8. CORS

- В `factory.py` / `main.py`: `CORSMiddleware`.
- `allow_origins`: `[settings.cors_origins]` — default `http://localhost:3000` в `core/config.py`.
- `allow_methods`: `GET`, `POST`, `OPTIONS`; `allow_headers`: `Content-Type`, `Accept`.

### 9. Тесты

- **`test_products.py`:** список, pagination, пустая страница, `422` на невалидный `limit`.
- **`test_chat_sse.py`:**
  - Парсер SSE из `response.iter_lines()` / raw body.
  - Fake runner с scripted tools → проверка типов и порядка событий.
  - `done.session_id` совпадает с ответом; повторный turn с тем же id.
  - Неизвестный `session_id` → `400` JSON (не SSE).
  - Mid-stream error (мок LLM exception после `started`) → `event: error`.
- **Регрессия:** обновить `test_chat_sse_not_implemented` → `test_chat_sse_returns_stream`.
- **CORS:** TestClient `OPTIONS` с `Origin: http://localhost:3000`.
- CI: только моки; `@pytest.mark.live` для ручного SSE с OpenRouter — опционально.

### 10. Документация и OpenAPI

- `backend/README.md`: секции «SSE chat» и «Products catalog» с `curl -N` примерами.
- Корневой `README.md`: отметить готовность SSE + `/products`.
- OpenAPI: `responses` для `/chat` с `content: text/event-stream` (description + example events); тег `products`.

### 11. Качество

- Цикл Edit → Sanitize → Verify на каждый новый модуль (`ruff check/format`, `pytest` целевой файл).
- `make ci` зелёный перед закрытием спринта.

---

## Зависимости и env

| Переменная | Компонент | Назначение |
|------------|-----------|------------|
| `DATA_DIR` | backend (через mcp_server paths) | Путь к `data/b2c/catalog.json` |
| `CORS_ORIGINS` | backend | Опционально; default `http://localhost:3000` |
| `OPENAI_*`, `LANGFUSE_*` | backend | Без изменений sprint-03 |

Новых обязательных секретов нет. Зависимость `llmstart-agent-mcp-server` (path `../mcp_server`) — для `catalog.list_products()`.

---

## Риски и допущения

| Риск | Митигация |
|------|-----------|
| LangGraph `invoke` не даёт real-time tool events | Custom `BaseCallbackHandler` на `on_tool_start` / `on_tool_end` |
| Sync generator в async FastAPI | `StreamingResponse` с sync iterator допустим в Starlette; при блокировках — `run_in_executor` для turn |
| Дублирование логики JSON vs SSE | Общий `_parse_turn` + один путь обновления `session_store` |
| SSE буферизация nginx/proxy | `Cache-Control: no-cache`; для local dev — прямой uvicorn |
| Flaky порядок событий в тестах | Детерминированный `FakeReactRunner` с фиксированной последовательностью |

**Допущения:**

- `message` delta — постфактум чанкирование финального текста, не посимвольный LLM-stream (достаточно для виджета sprint-05).
- SSE только для `channel: web`; запрос с `channel: telegram` + SSE — допустим (тот же поток событий), специального HTML в SSE нет.
- `GET /products` читает файл напрямую через shared module, без MCP subprocess call (консистентность данных, не дублирование HTTP).
- JSON-ветка `/chat` остаётся sync endpoint — без breaking changes.

---

## Skills

Перед реализацией прочитать:

- `fastapi-templates` — `StreamingResponse`, CORS, роутеры
- `python-testing-patterns` — парсинг SSE в TestClient, async generators
- `api-design-principles` — пагинация, контракты ошибок
- `modern-python` — ruff, типы для generators

---

## Итог (заполняется после закрытия)

Sprint закрыт 2026-06-05. Backend API MVP: SSE `POST /chat`, `GET /products`, CORS; JSON без регрессий; 25 backend-тестов, `make ci` зелёный.

Подробности: [summary.md](./summary.md).
