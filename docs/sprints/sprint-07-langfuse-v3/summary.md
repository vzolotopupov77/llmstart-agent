# Summary: Sprint 07 — langfuse-v3

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-10

---

## Что сделано

### DevOps — Langfuse v3 compose

- `devops/docker-compose.yml`: web + worker + Postgres + ClickHouse + Redis + MinIO
- Образы: `langfuse:3.125.0`, worker digest-pinned, `clickhouse:24.8`, `redis:7.4.2-alpine`, `minio:RELEASE.2024-11-07`
- `.env.example`: `LANGFUSE_CLICKHOUSE_*`, `LANGFUSE_REDIS_AUTH`, `LANGFUSE_MINIO_*`, `LANGFUSE_S3_EVENT_UPLOAD_BUCKET`
- UI: `127.0.0.1:3001`; storage-сервисы только internal network

### Документация

- `devops/README.md` — v3 stack, clean start v2→v3, troubleshooting
- `backend/README.md` — E2E runbook trace за turn
- `docs/concept/integrations.md` §4 — self-hosted v3, OTLP
- `docs/roadmap.md` — sprint-07 ✅, пункт Langfuse v3 отмечен

### Backend / тесты

- `observability/langfuse.py` без изменений (SDK v3 + CallbackHandler совместим с server v3)
- `test_chat_returns_200_when_langfuse_disabled` — регрессия
- `test_langfuse_live.py` — `@pytest.mark.live` (health, OTLP ≠ 404, SDK trace.list)

---

## Приёмка

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | v3 stack healthy | ✅ |
| 2 | UI :3001 | ✅ |
| 3 | Runbook clean start | ✅ |
| 4 | Trace за turn в UI | ✅ ручная проверка |
| 5 | Langfuse down → chat 200 | ✅ автотест |
| 6 | `make test-backend` | ✅ 40 passed |
| 7 | Roadmap | ✅ |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Clean start dev-данных | Выбор пользователя; проще, чем background migration v2→v3 |
| Worker digest-pinned | На Docker Hub нет тега `langfuse-worker:3.125.0` |
| Backend SDK остаётся v3 | Совместим с server ≥ 3.125.0; минимальный diff |

---

## Заметки для dev (Windows)

- `curl` в PowerShell ≠ curl — использовать `Invoke-RestMethod` или `curl.exe`
- После clean start обязательны новые `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` и перезапуск backend

---

## Что дальше (v0.2)

- Guardrails + policy layer
- Rate limits, квоты LLM
- Security review (CORS prod, headers, secrets CI)
- Загрузка validation datasets в Langfuse — отдельная задача
