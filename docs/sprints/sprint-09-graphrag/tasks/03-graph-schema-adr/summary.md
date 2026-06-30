# Summary: Task 03 — graph-schema-adr

> **Sprint:** sprint-09-graphrag  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-28

---

## Что сделано

### `docs/sprints/sprint-09-graphrag/schema.md`

- **7 классов узлов** с полными свойствами, типами и ключами нормализации (`id` = URL-slug).
- **8 типов рёбер** с явными направлениями, свойствами и обоснованием каждого.
- Mermaid-диаграмма схемы.
- Boundary rule: структура → Neo4j, семантика → Qdrant, связь по `id`.
- **15 Cypher-паттернов** по трём классам вопросов (single-hop × 1, multi-hop × 6, global × 5).
- DDL: constraints + indexes (все с `IF NOT EXISTS`).

### `docs/adrs/ADR-0010-graphrag.md`

- 3 рассмотренных варианта: A (Qdrant+metadata) ❌, B (Neptune/ArangoDB) ❌, C (Neo4j) ✅.
- Зафиксированные версии: `neo4j:2026.04.0-community`, `neo4j==6.3.0`, `neo4j-graphrag==1.16.0`, `langchain-neo4j==0.4.0`.
- Routing-таблица: single-hop → Qdrant, multi-hop → VectorCypherRetriever, global → Cypher-агрегат, text2cypher → Text2CypherRetriever.
- 4 обязательных guardrail для text2cypher.
- Plan внедрения (Tasks 04–08).

### `docs/concept/architecture.md` — обновления

- Добавлен Neo4j в mermaid-диаграмму контекста системы (рядом с Qdrant).
- Обновлена таблица контейнеров и раздел деплоя (порты 7474/7687).
- Sequence diagram: `data/ + Chroma` → `Qdrant + Neo4j`.
- Добавлен раздел «ADR по хранилищам» (ADR-0009 + ADR-0010).

### `docs/README.md`, `docs/concept/vision.md`

- ADR-0010 добавлен в навигационные таблицы.

---

## Ключевые решения

| Решение | Обоснование |
|---------|-------------|
| `Module` — деферред | На 4 курсах нет смысла; вводить при ≥ 10 курсах |
| `Format`/`Level` — узлы с оговоркой | Явно указаны в задаче; если traversal не нужен — вернуть как свойства в Task 06 |
| SDK: `neo4j-graphrag` (основной) + `langchain-neo4j` (опционально) | neo4j-graphrag — официальный; langchain-neo4j — fallback для `GraphCypherQAChain` |
| Граф не включается на single-hop | Явное правило routing для защиты baseline-метрики |
| `(Theme)-[:REQUIRES]->(prereq)` | Направление «A REQUIRES B» — от зависимого к базовому; обход `(A)-[:REQUIRES*]->()` даёт все prerequisites |

---

## Открытые вопросы (передаются в Task 04)

- Верифицировать актуальные версии `neo4j:2026.04.0-community`, `neo4j==6.3.0`, `neo4j-graphrag==1.16.0` перед добавлением в docker-compose.

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `ADR-0010-graphrag.md`: схема, boundary rule, версии (не `latest`), конвенции | ✅ |
| 2 | Каждый класс вопросов привязан к Cypher-маршруту | ✅ (schema.md §5 + ADR §3.5) |
