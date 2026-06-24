# Summary: 01-adr-vector-db

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-22

## Что сделано

Создан [`docs/adrs/ADR-004-vector-db.md`](../../../adrs/ADR-004-vector-db.md) — статус Accepted.

## Решение

**Выбран Qdrant** как production-бэкенд RAG-слоя.

Ключевые аргументы:
- Server-side payload filter по `segment=b2b|b2c` (ChromaDB — client-side post-filter)
- Один контейнер, health check `/healthz`, named volume — production-паттерны
- Multi-process safe (embedded ChromaDB небезопасен при backend + mcp_server в двух процессах)
- pgvector отклонён как избыточный для текущего scope

## Версии

| Компонент | Версия |
|-----------|--------|
| Docker-образ | `qdrant/qdrant:v1.18.2` |
| Python SDK | `qdrant-client==1.18.0` |

Совместимость: SDK 1.18.0 ↔ server 1.18.2 — patch-релиз, breaking changes отсутствуют.

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | ADR содержит контекст, варианты, решение, последствия | ✅ |
| 2 | Версии зафиксированы (не `latest`) | ✅ |
| 3 | Причины отказа от кандидатов явны | ✅ |
