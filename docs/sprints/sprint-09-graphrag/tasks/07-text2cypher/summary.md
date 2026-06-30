# Summary: Task 07 — text2cypher

> **План:** [plan.md](./plan.md)  
> **Дата закрытия:** 2026-06-29

---

## Что реализовано

### Guardrails и retriever

- `mcp_server/mcp_server/text2cypher/guardrails.py` — `validate_read_only_cypher`, `ensure_limit`, `Text2CypherGuardrailError`.
- `mcp_server/mcp_server/text2cypher/schema.py` — `load_enhanced_schema()` (`get_schema(..., is_enhanced=True)`), `load_few_shot_examples()`.
- `mcp_server/mcp_server/retriever/text2cypher.py` — `GuardedText2CypherRetriever` (override `get_search_results`: regex → LIMIT → EXPLAIN → execute с timeout).
- `mcp_server/mcp_server/retriever/neo4j_driver.py` — `get_neo4j_ro_driver()` (отдельный кеш от admin driver).

### MCP tool

- `mcp_server/mcp_server/tools/text2cypher.py` — `handle_text2cypher`, `TEXT2CYPHER_TOOL_DESCRIPTION` (guardrail #4).
- `mcp_server/mcp_server/server.py` — регистрация `text2cypher_tool` (6 tools total).

### Конфиг и данные

- `mcp_server/mcp_server/config.py`, `.env.example` — `NEO4J_RO_*`, `TEXT2CYPHER_MODEL`, `TEXT2CYPHER_RESULT_LIMIT`, `TEXT2CYPHER_QUERY_TIMEOUT_SECONDS`.
- `scripts/few_shot_examples.json` — 5 NL→Cypher пар из [schema.md](../../schema.md) §5.2–5.3.

### Тесты

- `mcp_server/tests/test_text2cypher_guardrails.py` — 18 tests: regex block (9 cases), LIMIT, few-shot load, docstring scope, mock pipeline (write block, LIMIT inject, EXPLAIN reject).
- `mcp_server/tests/test_server.py` — обновлён на 6 MCP tools.

---

## 4 guardrails — как реализованы

| # | Guardrail | Реализация |
|---|-----------|------------|
| 1 | RO credentials | `get_neo4j_ro_driver()` + `NEO4J_RO_*`; fail fast без `NEO4J_RO_PASSWORD` |
| 2 | Regex write-filter | `validate_read_only_cypher` до EXPLAIN; SDK `query_type == 'r'` — второй слой |
| 3 | LIMIT + timeout | `ensure_limit(25)`; `execute_query(..., timeout=5s)` |
| 4 | Узкий tool scope | `TEXT2CYPHER_TOOL_DESCRIPTION` на MCP tool |

---

## Примеры вызовов (smoke)

```python
from mcp_server.tools.text2cypher import handle_text2cypher

# ✅ structural
handle_text2cypher("Сколько курсов в каталоге?", "b2c")
handle_text2cypher("Какие курсы входят в комбо ai-agents-combo?", "b2c")
handle_text2cypher("В каких курсах встречается тема MCP?", "b2c")

# ❌ blocked at guardrail #2
handle_text2cypher("CREATE (n:Hack) RETURN n", "b2c")  # → ValueError: write operation blocked
```

**Ожидаемый формат ответа:** chunk с `branch=text2cypher`, header `[text2cypher] cypher=... | rows=N`.

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| `make test-backend` | `make test-mcp` (66 passed) | Tool и тесты в `mcp_server/`, не backend |
| `GraphCypherQAChain` fallback | не нужен | `Text2CypherRetriever` из neo4j-graphrag достаточен |
| `RETRIEVER_BRANCH=text2cypher` | не добавлено | text2cypher — отдельный MCP tool, не ветка factory (Task 08 eval) |
| RO `CREATE` blocked в Neo4j | regex на Python-слое | Community Edition без RBAC `reader` |
| Langfuse / routing examples | deferred | Task 08 — agent system prompt |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Подкласс `Text2CypherRetriever` с override `get_search_results` | Минимальный diff; SDK EXPLAIN-guard сохранён |
| Enhanced schema — live fetch + `@lru_cache` | Каталог малый; стабильность промпта на process lifetime |
| Few-shot в `scripts/few_shot_examples.json` | Переиспользуемо; формат `"Q: ... A: MATCH ..."` для SDK |
| Mock retriever tests через `__new__` | SDK pydantic требует real `neo4j.Driver` в `__init__` |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | RO driver (`NEO4J_RO_*`) | ✅ `get_neo4j_ro_driver()` |
| 2 | Enhanced schema + 5 few-shot | ✅ `load_enhanced_schema()`, `few_shot_examples.json` |
| 3 | Guardrails #1–#4 | ✅ см. таблицу выше |
| 4 | `test_text2cypher_blocks_write`, `test_text2cypher_adds_limit` | ✅ pass |
| 5 | `make test-mcp` зелёный | ✅ 66 passed |
| 6 | Smoke NL→Cypher на живом Neo4j | ✅ пользователь |
| 7 | Docstring tool понятен | ✅ пользователь |
| 8 | Langfuse / «расскажи про X» не вызывает tool | ⏳ Task 08 |

**Согласование:** 2026-06-29 («ок»).

---

## Что дальше

- **Task 08:** agent routing — `vector_search` / `graph_search` / `global_catalog` / `text2cypher_tool`; Langfuse traces; `graphrag-final.md`.
- **Housekeeping:** sprint README DoD #5 — ссылка на `make test-mcp` (исправлено в README).

---

## Ссылки

- [plan.md](./plan.md)
- [schema.md](../../schema.md)
- [ADR-0010 §5 guardrails](../../../../adrs/ADR-0010-graphrag.md)
- [Task 04 summary](../04-neo4j-infra/summary.md) — RO user infra
- [Task 06 summary](../06-graph-retrieval/summary.md)
