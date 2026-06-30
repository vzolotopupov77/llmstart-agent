# Task 04: neo4j-infra

> **Sprint:** [../../README.md](../../README.md)
> **Тип:** feat
> **Ветка:** `feat/graphrag-04-neo4j-infra`
> **Spec:** ADR-0010, sprint Task 04

---

## Цель

Добавить Neo4j Community в docker-compose с APOC, persistence и health check; make-цели `graph-*`, smoke-проверку подключения и RO-пользователя для text2cypher.

---

## Состав работ

- [x] Сервис `neo4j` в `devops/docker-compose.yml` (образ `neo4j:2026.04.0-community`, APOC, health via cypher-shell, volumes)
- [x] Переменные `NEO4J_*` в `.env.example`
- [x] Make-цели: `graph-up`, `graph-down`, `graph-status`, `graph-shell`, `graph-init-ro`
- [x] `mcp_server/scripts/neo4j_smoke.py` + `tests/test_neo4j_smoke.py`
- [x] `devops/neo4j/init-text2cypher-ro.cypher` + документация в `devops/README.md`
- [x] Самопроверка по критериям DoD

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Neo4j healthy после поднятия | `make graph-up` → `docker compose ps neo4j` → healthy |
| 2 | Smoke-проверка подключения | `make graph-status` → `Connection OK` |
| 3 | RO-пользователь создан | `make graph-init-ro` → `text2cypher_ro` с ролью reader |
| 4 | Lint проходит | `make lint-mcp` |
| 5 | Тесты проходят | `make test-mcp` (skip без `NEO4J_PASSWORD`) |
| 6 | `.env.example` содержит все Neo4j-переменные | ревью файла |
| 7 | Persistence volume | `make graph-down && make graph-up` — данные сохраняются |

---

## Артефакты

- `devops/docker-compose.yml` — сервис neo4j + volumes
- `.env.example` — NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_RO_USER, NEO4J_RO_PASSWORD
- `Makefile` — graph-* цели
- `mcp_server/pyproject.toml` — `neo4j==6.2.0` (6.3.0 отсутствует на PyPI)
- `mcp_server/scripts/neo4j_smoke.py` — smoke для graph-status
- `mcp_server/tests/test_neo4j_smoke.py` — pytest
- `devops/neo4j/init-text2cypher-ro.cypher` — справочный Cypher для RO-user
- `devops/README.md` — runbook Neo4j

---

## Scope

**Трогаем:** только файлы из списка «Артефакты» и этот `plan.md`.

**НЕ трогаем:**
- graph-index, retriever, text2cypher tool (Tasks 05–07)
- backend/bot/frontend

---

## Риски и допущения

- Tag `neo4j:2026.04.0-community` существует на Docker Hub (верификация через `docker pull`)
- `make graph-init-ro` передаёт пароль inline в cypher-shell (dev-only; не для production)

---

## Открытые вопросы

- [x] Именование make-целей: `graph-*` (не `neo4j-*` из sprint README)
