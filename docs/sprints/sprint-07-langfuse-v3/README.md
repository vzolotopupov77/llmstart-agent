# Sprint 07: langfuse-v3

> **Версия roadmap:** v0.2  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-10  
> **Закрыт:** 2026-06-10

---

## Цель спринта

Апгрейд self-hosted Langfuse **v2.95.11 → v3** в `devops/docker-compose.yml`; clean start dev-данных; закрыть отложенный DoD «trace за turn» из sprint-03/06.

---

## DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make up` поднимает v3 stack (web, worker, postgres, clickhouse, redis, minio) | ✅ |
| 2 | UI на :3001, health 200 | ✅ |
| 3 | Runbook clean start v2→v3 | ✅ `devops/README.md` |
| 4 | Trace за turn — runbook E2E | ✅ ручная проверка (трейсы в UI) |
| 5 | Langfuse down → chat 200 | ✅ `test_chat_returns_200_when_langfuse_disabled` |
| 6 | `make test-backend` зелёный | ✅ 40 passed |
| 7 | Roadmap обновлён | ✅ |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | compose-v3-stack | ✅ | [plan](tasks/01-compose-v3-stack/plan.md) | [summary](tasks/01-compose-v3-stack/summary.md) |
| 02 | migration-fresh-start-runbook | ✅ | [plan](tasks/02-migration-fresh-start-runbook/plan.md) | [summary](tasks/02-migration-fresh-start-runbook/summary.md) |
| 03 | trace-per-turn-verification | ✅ | [plan](tasks/03-trace-per-turn-verification/plan.md) | [summary](tasks/03-trace-per-turn-verification/summary.md) |
| 04 | roadmap-and-sprint-close | ✅ | [plan](tasks/04-roadmap-and-sprint-close/plan.md) | [summary](tasks/04-roadmap-and-sprint-close/summary.md) |

---

## Итог

- Compose: Langfuse v3 (`langfuse-web:3.125.0`, worker digest-pinned), ClickHouse, Redis, MinIO, Postgres 15
- Миграция dev: **clean start** (`down -v`), новые env в `.env.example`
- Backend SDK без изменений; OTLP endpoint доступен на v3
- Live-тесты: `pytest -m live tests/test_langfuse_live.py` (skip без `LANGFUSE_*`)
