# Summary: Task 04 — neo4j-infra

> **План:** [plan.md](./plan.md)  
> **Дата закрытия:** 2026-06-28

---

## Что реализовано

### `devops/docker-compose.yml`

- Сервис `neo4j:2026.04.0-community`, APOC, volumes `neo4j_data` / `neo4j_logs`.
- Порты `127.0.0.1:7474` / `7687`, `NEO4J_AUTH` из env.
- Healthcheck: `cypher-shell … RETURN 1` через Bolt (см. отклонения).

### `.env.example`

- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_RO_USER`, `NEO4J_RO_PASSWORD` с dev-дефолтами.

### `Makefile`

- `graph-up`, `graph-down`, `graph-status`, `graph-shell`, `graph-init-ro` + help.

### `mcp_server`

- `pyproject.toml`: `neo4j==6.2.0`.
- `scripts/neo4j_smoke.py` — smoke для `make graph-status` (`Connection OK`).
- `scripts/neo4j_init_ro.py` — idempotent создание `text2cypher_ro`.
- `scripts/neo4j_shell.py` — cross-platform launcher для cypher-shell.
- `tests/test_neo4j_smoke.py` — skip без `NEO4J_PASSWORD`, pass при поднятом Neo4j.

### Документация

- `devops/README.md` — runbook Neo4j, make-цели, persistence, RO-user.
- `devops/neo4j/init-text2cypher-ro.cypher` — справочный Cypher.
- `docs/adrs/ADR-0010-graphrag.md` — amend после Task 04 (§3.7 infra, driver 6.2.0, Community RBAC).

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| Healthcheck `GET /db/neo4j/available` | `cypher-shell RETURN 1` | Endpoint → 404 на Neo4j 2026.04 |
| `neo4j==6.3.0` | `neo4j==6.2.0` | 6.3.0 отсутствует на PyPI |
| `NEO4J_USERNAME`, `NEO4J_DATABASE` | `NEO4J_USER`, без `DATABASE` | По согласованному scope Task 04 |
| Make `neo4j-shell` / `neo4j-status` | `graph-*` | По согласованному scope Task 04 |
| `graph-init-ro` через cypher-shell в Makefile | Python-скрипт | Windows: bash-подстановки в Makefile ненадёжны |
| `GRANT ROLE reader` | Только `CREATE USER` на Community | RBAC — Enterprise-only |

---

## Принятые решения

| Решение | Причина | ADR |
|---------|---------|-----|
| Healthcheck через Bolt, не HTTP | DB readiness, не только HTTP up | [ADR-0010 §3.7](../../../../adrs/ADR-0010-graphrag.md) |
| Driver `6.2.0` | Последняя доступная 6.x на PyPI | ADR-0010 §3.2 |
| RO-user: отдельные creds + app guardrails | Community без `GRANT ROLE reader` | ADR-0010 §5 |
| `graph-shell` / `graph-init-ro` через Python | Кросс-платформенность (Windows + make) | — |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `/db/neo4j/available` → 404 | Healthcheck на `cypher-shell RETURN 1` |
| `neo4j==6.3.0` не резолвится | Pin `6.2.0`, amend ADR |
| `GRANT ROLE` на Community | Warning + документация; guardrails 2–4 в Task 07 |
| Makefile + `$NEO4J_*` на Windows | Wrapper-скрипты в `mcp_server/scripts/` |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Neo4j healthy после `make graph-up` | ✅ (агент + пользователь) |
| 2 | `make graph-status` → `Connection OK` | ✅ |
| 3 | RO-пользователь `text2cypher_ro` | ✅ (`graph-init-ro`; роль reader — Enterprise-only) |
| 4 | Lint | ✅ `make lint-mcp` |
| 5 | Тесты | ✅ `make test-mcp` (skip/pass) |
| 6 | `.env.example` — 5 переменных Neo4j | ✅ |
| 7 | Persistence volume | ✅ (пользователь) |

---

## Что дальше

- **Task 05:** `scripts/seed.cypher`, `graph_indexer.py`, `make graph-index`.
- **Task 07:** regex/LIMIT guardrails для text2cypher (компенсация отсутствия RBAC на Community).

---

## Ссылки

- [ADR-0010 — GraphRAG](../../../../adrs/ADR-0010-graphrag.md)
- [devops/README.md](../../../../../devops/README.md) — Neo4j runbook
