# Plan: Task 03 — graph-schema-adr

> **Sprint:** sprint-09-graphrag  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-28

---

## Цель

Спроектировать LPG-схему каталога курсов, зафиксировать boundary rule и принять ADR с версиями Neo4j и SDK.

---

## Состав работ

- Спроектировать LPG-схему: узлы `Combo`, `Course`, `Module`, `Theme`, `Audience`, `Format`, `Level`; рёбра с явными направлениями.
- Сформулировать boundary rule: что в граф, что в Qdrant, связь по `id`.
- Привязать каждый класс вопросов к маршруту обхода (Cypher-паттерн).
- Выбрать SDK; зафиксировать версии образа Neo4j и Python-пакетов.
- Зафиксировать конвенции именования.
- Создать `docs/adrs/ADR-0010-graphrag.md`.
- Создать `docs/sprints/sprint-09-graphrag/schema.md` (опционально → выполнено).
- Обновить архитектурную документацию.

---

## Skills применены

- `neo4j-modeling-skill` — anti-patterns, direction conventions, naming, constraints DDL
- `neo4j-graphrag-skill` — retriever selection (VectorCypherRetriever, Text2CypherRetriever, ToolsRetriever)

---

## DoD

| # | Критерий |
|---|----------|
| 1 | `ADR-0010-graphrag.md` содержит схему, boundary rule, версии (не `latest`), конвенции |
| 2 | Каждый класс вопросов привязан к Cypher-маршруту |

---

## Артефакты

- [`docs/adrs/ADR-0010-graphrag.md`](../../../../adrs/ADR-0010-graphrag.md)
- [`docs/sprints/sprint-09-graphrag/schema.md`](../../schema.md)
