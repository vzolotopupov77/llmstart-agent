# Task 01: mcp-server-rag

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** feat  
> **Spec:** [architecture.md](../../../../concept/architecture.md#mcp-core--mcp_server), [integrations.md](../../../../concept/integrations.md)

---

## Цель

Реализовать MCP-сервер (`mcp_server/`) с 5 tools, RAG B2B/B2C, seed `data/`, тесты и интеграция в `make ci`.

---

## Состав работ

- [x] Каркас `mcp_server/` (uv, pyproject, FastMCP stdio) — закрыто 2026-06-05
- [x] Seed `data/`: catalog.json (6 продуктов), MD b2b/b2c, leads.txt
- [x] RAG: indexer + retriever, Chroma в `data/.chroma/`
- [x] Tools: search_knowledge_base, list_b2c_products, create_payment_link, confirm_payment, save_lead
- [x] Тесты unit + integration; `make test-mcp`; CI job
- [x] `mcp_server/README.md`, обновить корневой README
- [x] `summary.md`, обновить sprint README и roadmap

---

## Критерии готовности (DoD)

См. [sprint README](../../README.md#dod-спринта).

---

## Scope

**Трогаем:** `mcp_server/`, `data/`, `Makefile`, `.env.example`, `.github/workflows/ci.yml`, `README.md`

**НЕ трогаем:** `backend/` Agent Core, `bot/`, `frontend/` (sprint-03+)
