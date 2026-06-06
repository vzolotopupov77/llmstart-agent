# Summary: Sprint 02 — mcp-tools-rag

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-05

---

## Что реализовано

- **`mcp_server/`** — FastMCP stdio-сервер с 5 tools
- **RAG:** indexer + retriever, Chroma persist в `data/.chroma/`, embeddings через OpenRouter
- **`data/`:** seed B2B/B2C (4 MD), `catalog.json` (6 продуктов), `leads.txt`, runtime `payments.json`
- **Tools:** `search_knowledge_base`, `list_b2c_products`, `create_payment_link`, `confirm_payment`, `save_lead`
- **Тесты:** 17 pytest (unit + integration + E2E воронка + список MCP tools)
- **Инфра:** `make test-mcp`, `make reindex`, CI job `mcp-server`, `mcp_server/README.md`

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| PDF-парсинг (stretch) | Только MD | YAGNI для MVP спринта |
| 1 задача в README | 1 task `01-mcp-server-rag` | Весь scope в одном потоке |
| MCP Inspector вручную | Тест `test_server_lists_five_tools` + ручной stdio | Достаточно для DoD без UI-клиента |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| FastMCP + stdio | Минимум boilerplate; контракт из architecture.md |
| `get_settings()` в runtime, не module-level `settings` | Корректный `DATA_DIR` в тестах и subprocess |
| Mock embeddings при `OPENAI_API_KEY=test-key` или пустом ключе | CI без OpenRouter; детерминированные тесты |
| Manifest индекса по относительным путям | Стабильное сравнение mtime на Windows |
| State оплаты в `data/payments.json` | Persist между перезапусками MCP |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Тесты писали в repo `data/leads.txt` | `paths.py` → `get_settings()` вместо кэшированного `settings` |
| Dimension mismatch 384 vs 1536 в RAG-тестах | Mock client при test-key; единый клиент для index и query |
| `mcp_serve` — опечатка при запуске | Документировано: `python -m mcp_server` |
| stdio «зависает» без вывода | Ожидаемое поведение — ждёт MCP-клиента |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | MCP stdio, 5 tools | ✅ тест + ручной старт |
| 2 | RAG B2B/B2C | ✅ pytest |
| 3 | 6 продуктов | ✅ pytest + catalog.json |
| 4 | Воронка payment → lead | ✅ E2E pytest + ручная проверка |
| 5 | Chroma + reindex | ✅ pytest + `make reindex` |
| 6 | `make ci` | ✅ |
| 7 | Seed-данные | ✅ |

---

## Что дальше

- **Sprint 03:** MCP-клиент в backend, ReAct, `POST /chat`, Langfuse traces
- Перед sprint-03: `OPENAI_API_KEY` и `LANGFUSE_*` в `.env`

---

## Ссылки

- [Sprint 03: agent-core](../sprint-03-agent-core/README.md)
- [mcp_server/README.md](../../../mcp_server/README.md)
- [Task 01 summary](./tasks/01-mcp-server-rag/summary.md)
