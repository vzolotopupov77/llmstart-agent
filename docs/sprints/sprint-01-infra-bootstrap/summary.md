# Summary: Sprint 01 — infra-bootstrap

> **План:** [README.md](./README.md)  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Дата закрытия:** 2026-06-05

---

## Что реализовано

- Monorepo: `backend/`, `frontend/`, `bot/`, `mcp_server/`, `data/`, `devops/`, корневой `README.md`, `.gitignore`
- **Backend:** FastAPI, `GET /health` → `{status, version}`, uv/ruff/mypy/pytest
- **DevOps:** Langfuse v2 (`2.95.11`) + Postgres 15 в `devops/docker-compose.yml`
- **Makefile:** `make dev`, `up`/`down`, `lint`, `test`, `ci`
- **Frontend:** Next.js 16 заглушка на :3000
- **CI/CD:** `.github/workflows/ci.yml`, `.devcontainer/devcontainer.json`
- **Task 06:** секреты compose в `.env`, bind `127.0.0.1:3001`, healthcheck Langfuse, troubleshooting P1000

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| 5 задач | 6 задач (+ compose-secrets-hardening) | Ревью docker-expert после реализации |
| `langfuse/langfuse:2` | Pin `2.95.11` | Воспроизводимость dev-окружения |
| Health response `service` field | `version` по api-contracts | Следование `api-contracts.md` |
| DoD #4 Codespaces | Не проверялся пользователем | Devcontainer создан; приёмка — при первом использовании |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Langfuse v2 (2 сервиса), не v3 | Проще для локального dev без ClickHouse/Redis/MinIO |
| Секреты compose только в `.env` | Не коммитить креды; fail-fast через `:?` |
| Postgres volume + смена пароля → `down -v` | Ограничение Postgres: пароль фиксируется при init |
| `make ci` без обязательного `.env` | CI backend/frontend не зависит от Docker |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Docker не запущен на первой проверке | Документировано в DoD; пользователь поднял позже |
| P1000: пароль `.env` ≠ пароль в volume | `docker compose down -v` + troubleshooting в `devops/README.md` |
| `make up` с `test -f` не работает в Windows make | Убрали shell-check; `--env-file .env` + ошибка compose |
| Ctrl+C на Windows → `Error 255` | Ожидаемое поведение `make -j2` в cmd |

---

## Итог DoD спринта

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make dev` → :8000, :3000, :3001 | ✅ подтверждено пользователем |
| 2 | `GET /health` → 200 | ✅ |
| 3 | `make ci` | ✅ |
| 4 | Devcontainer / Codespaces | ⚠️ артефакт готов, E2E не в приёмке |
| 5 | Структура каталогов | ✅ |

---

## Что дальше

- **Sprint 02:** `mcp_server/` — RAG B2B/B2C, 5 tools, seed `data/`
- Заполнить `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` в `.env` перед sprint-03

---

## Ссылки

- [Sprint 02: mcp-tools-rag](../sprint-02-mcp-tools-rag/README.md)
- [devops/README.md](../../../devops/README.md)
