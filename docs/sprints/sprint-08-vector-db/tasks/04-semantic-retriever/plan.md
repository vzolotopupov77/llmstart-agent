# Plan: 04-semantic-retriever

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-23

## Цель

Переписать `search_knowledge_base` через абстрактный `BaseRetriever`; реализация выбирается через `RETRIEVER_BACKEND`.

## Состав работ

- [x] `retriever/base.py` — Protocol, типы
- [x] `retriever/qdrant.py`, `retriever/chroma.py`, `retriever/factory.py`
- [x] `config.py` — `RETRIEVER_BACKEND`
- [x] `tools/search_knowledge_base.py` — через интерфейс
- [x] `server.py` — убрать `ensure_index` при старте
- [x] Тесты — mock retriever для tool-тестов

## Дополнения по итогам ревью (RAG review drill)

- [x] `qdrant_indexer.py` — payload index для `segment` (filterable HNSW, до upsert)
- [x] `qdrant_indexer.py` — отдельный путь чанкинга для PDF/TXT (без heading-split)
- [x] `qdrant_indexer.py` — фильтрация пустых чанков (пустые строки из PDF → `No embedding data received`)
- [x] `embeddings.py` — настраиваемый `OPENAI_TIMEOUT_SECONDS` (default 120 с)

## DoD

- [x] `BaseRetriever` определён; Qdrant/Chroma изолированы
- [x] `RETRIEVER_BACKEND` переключает реализацию
- [x] `search_knowledge_base` не импортирует SDK напрямую
- [x] `make test-mcp` зелёный (22 passed)
- [x] ChromaDB в pyproject остаётся (bench Task 05)
- [x] `make index` завершается без ошибок (после фикса пустых чанков)

## Артефакты

- `mcp_server/mcp_server/retriever/` — base, qdrant, chroma, factory
- обновлённые tool, server, tests, config, embeddings, qdrant_indexer

## Scope

**In:** retriever interface, factory, tool rewrite, tests, qdrant indexer improvements.  
**Out:** удаление Chroma (Task 05 bench), backend `ensure_rag_index` refactor.
