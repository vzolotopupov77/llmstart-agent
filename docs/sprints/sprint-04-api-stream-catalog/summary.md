# Summary: Sprint 04 — api-stream-catalog

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-05

---

## Что реализовано

- **`POST /api/v1/chat` (SSE):** `Accept: text/event-stream` → `StreamingResponse`; события `reasoning`, `tool` (started/done/error), `products`, `message`, `payment_link`, `done`, `error`
- **`GET /api/v1/products`:** пагинация B2C-каталога (`limit`/`offset`) из `mcp_server.data_access.catalog`
- **JSON `/chat`:** без регрессий sprint-03
- **Слои:** `services/sse_formatter.py`, `catalog_service.py`, `message_chunker.py`; `agent/streaming_callbacks.py` (`ToolEventCollector`); схемы `api/schemas/sse.py`, `product.py`, `products.py`
- **CORS:** `CORSMiddleware`, default `http://localhost:3000` (`CORS_ORIGINS`)
- **Конфиг:** `cors_origins` в `Settings`
- **Тесты:** 25 backend pytest (+11): `test_chat_sse.py`, `test_products.py`, `test_message_chunker.py`
- **Документация:** `backend/README.md`, корневой `README.md` (SSE + `/products`)

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| Real-time token-stream LLM | Чанки финального `message` после `invoke` | YAGNI; достаточно для виджета sprint-05 |
| `run_chat_turn_stream` как async generator | Turn выполняется до yield; generator отдаёт готовые события | Проще, без mid-stream deadlock; pre-flight ошибки — JSON |
| Mid-stream `event: error` в integration | Unit-тест формата; pre-stream LLM → `503` JSON | Атомарный `invoke` до первого SSE-события |
| `StreamingReactRunner` отдельным классом | `ToolEventCollector` + синтез `started` из `TurnResult.tools` | Меньше дублирования с `ReactRunner` |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `_execute_turn()` — общий путь JSON и SSE | Единое обновление `session_store`, один вызов ReAct |
| Синтез `tool started` при пустом collector | Детерминированные SSE-тесты с `FakeReactRunner` |
| `response_model=None` на `/chat` | Union `ChatResponse \| StreamingResponse` несовместим с OpenAPI field |
| Каталог через `catalog.list_products()` | Тот же источник, что MCP `list_b2c_products` |
| `uvicorn` без `--reload` на Windows (dev note) | Избежание «призрачных» слушателей :8000 и зависаний |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Старый backend на :8000 (`501 SSE not implemented`) | Перезапуск; проверка на чистом порту |
| Несколько `LISTENING` на :8000 (Windows) | Kill процессов; dev без `--reload` |
| PowerShell `curl` ломает JSON | `ConvertTo-Json` / `httpx` / `curl.exe --data-raw` с одинарными кавычками |
| Live turn 2 → `503` (`tool failed: segment/product_id`) | Флаки LLM; reuse сессии покрыт pytest; не блокер sprint-04 API |
| `CatalogService` 503 в тестах без `DATA_DIR` | `apply_mcp_server_env()` в `conftest.py` |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | SSE `200` + заголовки | ✅ pytest + live на :8002 |
| 2 | Порядок SSE-событий | ✅ pytest |
| 3 | `done.session_id`, reuse сессии | ✅ pytest; live reuse — pytest |
| 4 | Ошибки до стрима → JSON | ✅ pytest (`400` session) |
| 5 | JSON `/chat` без регрессий | ✅ `test_chat.py` |
| 6 | `GET /products`, 6 items | ✅ pytest + live |
| 7 | Пагинация + `422` | ✅ pytest |
| 8 | Каталог = MCP source | ✅ pytest |
| 9 | CORS preflight | ✅ pytest |
| 10 | OpenAPI `/docs` | ✅ ручная проверка |
| 11 | `make ci` | ✅ 25 backend + полный CI |
| 12 | `backend/README.md` | ✅ |

---

## Что дальше

- **Sprint 05:** Next.js виджет — SSE UI, reasoning/tools, `GET /products` витрина
- **Sprint 06:** Telegram-бот, handoff `session_id`, E2E воронка
- Dev на Windows: предпочитать `uvicorn` без `--reload` при зависаниях `:8000`

---

## Ссылки

- [Sprint 05: web-widget](../sprint-05-web-widget/README.md)
- [backend/README.md](../../../backend/README.md)
- [api-contracts.md](../../concept/api-contracts.md)
