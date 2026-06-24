# Plan: 03-indexing-pipeline

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-23

## Цель

Скрипт индексации: читает `data/` (md, txt, pdf), чанкинг, эмбеддинги, idempotent upsert в Qdrant; запуск через `make index`.

## Состав работ

- [x] Добавить `qdrant-client` и `pypdf` в `mcp_server/pyproject.toml`
- [x] Расширить `Settings`: Qdrant URL/collection/api_key, embedding_dim
- [x] Создать `mcp_server/mcp_server/rag/qdrant_indexer.py`
- [x] Добавить цель `make index` в `Makefile`
- [x] Самопроверка по критериям DoD

## DoD

- [x] `make index` завершается с кодом 0
- [x] Повторный `make index` не создаёт дубликатов (upsert по детерминированному id)
- [x] Логи содержат итог: N файлов, M чанков
- [x] `cd mcp_server && uv run ruff check .` — зелёный

## Артефакты

- `mcp_server/pyproject.toml` — зависимости Qdrant + PDF
- `mcp_server/mcp_server/config.py` — Qdrant settings
- `mcp_server/mcp_server/rag/qdrant_indexer.py` — индексатор
- `Makefile` — цель `index`

## Scope

**In:** индексатор Qdrant, make-цель, env-driven config.  
**Out:** абстрактный retriever (Task 04), удаление Chroma (Task 04), smoke-тест коллекции (опционально).
