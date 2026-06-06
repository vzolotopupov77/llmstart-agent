# Sprint 01: infra-bootstrap

> **Версия roadmap:** v0.1  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-05  
> **Закрыт:** 2026-06-05

---

## Цель спринта

Поднять каркас monorepo и локальный dev-стек: одна команда `make dev` запускает backend с `GET /health`, заглушку frontend, Langfuse UI; репозиторий готов к разработке в облачном окружении (Codespaces / devcontainer).

---

## DoD спринта

Sprint считается завершённым, когда:

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Клон репо → `cp .env.example .env` → `make dev` поднимает backend :8000, frontend :3000, Langfuse UI :3001 | Ручная проверка после `make dev` |
| 2 | `GET http://localhost:8000/health` → `200` JSON `{ "status": "ok" }` | `curl http://localhost:8000/health` |
| 3 | `make ci` проходит для backend (lint + typecheck + test) | `make ci` |
| 4 | Devcontainer / Codespaces: post-create поднимает зависимости, `make dev` работает | Открыть репо в Codespaces, выполнить `make dev` |
| 5 | Структура каталогов соответствует [vision.md §6](../../concept/vision.md#6-структура-проекта) | Сравнить дерево с документом |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | monorepo-scaffold | ✅ | [plan](tasks/01-monorepo-scaffold/plan.md) | [summary](summary.md) |
| 02 | backend-health | ✅ | [plan](tasks/02-backend-health/plan.md) | [summary](summary.md) |
| 03 | devops-docker-langfuse | ✅ | [plan](tasks/03-devops-docker-langfuse/plan.md) | [summary](summary.md) |
| 04 | makefile-dev-stack | ✅ | [plan](tasks/04-makefile-dev-stack/plan.md) | [summary](summary.md) |
| 05 | cloud-ci | ✅ | [plan](tasks/05-cloud-ci/plan.md) | [summary](summary.md) |
| 06 | compose-secrets-hardening | ✅ | [plan](tasks/06-compose-secrets-hardening/plan.md) | [summary](summary.md) |

---

## Задача 01: monorepo-scaffold 📋

### Цель

Создать каркас monorepo с каталогами компонентов, корневым README и правилами игнорирования — без бизнес-логики.

> 💡 **Скиллы:** `modern-python` (структура Python-проектов), `docker-expert` (volumes/data).

### Состав работ

- [ ] Создать директории `backend/`, `frontend/`, `bot/`, `mcp_server/`, `data/`, `devops/`
- [ ] Добавить `data/b2b/`, `data/b2c/`, `data/leads.txt` (пустой), `data/.gitkeep` для `.chroma/`
- [ ] Корневой `README.md` с quick start (ссылка на `make dev` — после задачи 04)
- [ ] Обновить `.gitignore` по `.methodology/ci/gitignore-additions.txt`
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Все каталоги из vision §6 существуют | `ls` / tree |
| 2 | `.env` не в git, `.env.example` на месте | `git status` |

**Пользователь проверяет:**

- README описывает назначение каждого каталога
- `data/leads.txt` пустой, не содержит PII

### Артефакты

- `README.md` — quick start и структура проекта
- `.gitignore` — секреты, `.chroma/`, `node_modules/`, `__pycache__/`
- `data/b2b/.gitkeep`, `data/b2c/.gitkeep`, `data/leads.txt`

### Документы

- 📋 [План задачи](tasks/01-monorepo-scaffold/plan.md)
- 📝 [Summary](tasks/01-monorepo-scaffold/summary.md)

---

## Задача 02: backend-health 📋

### Цель

Минимальный Agent Core: FastAPI-приложение с `GET /health`, конфиг из env, smoke-тест и toolchain (uv, ruff, mypy).

> 💡 **Скиллы:** `modern-python`, `fastapi-templates`, `python-testing-patterns`.

### Состав работ

- [ ] `backend/pyproject.toml` (uv, ruff, mypy, pytest, FastAPI)
- [ ] `backend/app/main.py`, `backend/app/api/routes/health.py`
- [ ] `backend/app/core/config.py` — fail-fast для обязательных env (минимум для health)
- [ ] Smoke-тест `tests/test_health.py`
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `GET /health` → 200 | `uv run pytest tests/test_health.py` |
| 2 | ruff + mypy без ошибок | `uv run ruff check . && uv run mypy .` |

**Пользователь проверяет:**

- Swagger `/docs` открывается при `uvicorn app.main:app`

### Артефакты

- `backend/pyproject.toml`, `backend/app/**`, `backend/tests/test_health.py`

### Документы

- 📋 [План задачи](tasks/02-backend-health/plan.md)
- 📝 [Summary](tasks/02-backend-health/summary.md)

---

## Задача 03: devops-docker-langfuse 📋

### Цель

`devops/docker-compose.yml` с self-hosted Langfuse (UI :3001) и Postgres; документация env для observability.

> 💡 **Скиллы:** `docker-expert`.

### Состав работ

- [ ] `devops/docker-compose.yml`: `langfuse`, `langfuse-db` (Postgres internal)
- [ ] Health checks для сервисов Langfuse
- [ ] `devops/README.md` — как поднять только infra (`make up`)
- [ ] Согласовать `LANGFUSE_HOST` в `.env.example` с compose (localhost:3001)
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `docker compose -f devops/docker-compose.yml up -d` — Langfuse UI доступен | `curl -I http://localhost:3001` |
| 2 | Postgres Langfuse healthy | `docker compose ps` |

**Пользователь проверяет:**

- В UI Langfuse можно создать проект и получить ключи (для sprint-03)

### Артефакты

- `devops/docker-compose.yml`, `devops/README.md`
- Обновление `.env.example` (при необходимости)

### Документы

- 📋 [План задачи](tasks/03-devops-docker-langfuse/plan.md)
- 📝 [Summary](tasks/03-devops-docker-langfuse/summary.md)

---

## Задача 04: makefile-dev-stack 📋

### Цель

Корневой `Makefile` как единая точка входа; `make dev` оркестрирует compose + backend + frontend-заглушку.

> 💡 **Скиллы:** `nextjs-app-router-patterns` (минимальный scaffold frontend).

### Состав работ

- [ ] `Makefile`: `dev`, `dev-backend`, `dev-frontend`, `up`, `down`, `lint`, `format`, `typecheck`, `test`, `test-backend`, `ci`
- [ ] `make dev` = `make up` + backend :8000 + frontend :3000
- [ ] Минимальный `frontend/` (Next.js App Router, страница-заглушка «LLMStart Agent»)
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `make dev` поднимает все сервисы | `make dev` + `curl` :8000 и :3000 |
| 2 | `make ci` проходит | `make ci` |

**Пользователь проверяет:**

- Остановка `Ctrl+C` / `make down` корректно гасит процессы

### Артефакты

- `Makefile`, `frontend/package.json`, `frontend/app/page.tsx` (заглушка)

### Документы

- 📋 [План задачи](tasks/04-makefile-dev-stack/plan.md)
- 📝 [Summary](tasks/04-makefile-dev-stack/summary.md)

---

## Задача 05: cloud-ci 📋

### Цель

Облачное dev-окружение (devcontainer / GitHub Codespaces) и базовый CI для backend.

> 💡 **Скиллы:** `github-actions-templates`, `docker-expert`.

### Состав работ

- [ ] `.devcontainer/devcontainer.json` — Python 3.12, Node 20, Docker-in-Docker, uv, pnpm
- [ ] Post-create: `uv sync`, `pnpm install`, подсказка `cp .env.example .env`
- [ ] `.github/workflows/ci.yml` по шаблону methodology (backend: lint, format, mypy, pytest)
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | CI workflow валиден | `gh workflow view` или push в ветку |
| 2 | devcontainer.json валиден | Codespaces / Dev Containers extension |

**Пользователь проверяет:**

- Codespaces: `make dev` работает без ручной установки uv/pnpm

### Артефакты

- `.devcontainer/devcontainer.json`, `.github/workflows/ci.yml`

### Документы

- 📋 [План задачи](tasks/05-cloud-ci/plan.md)
- 📝 [Summary](tasks/05-cloud-ci/summary.md)

---

## Задача 06: compose-secrets-hardening ✅

### Цель

Вынести секреты Langfuse из `docker-compose.yml` в `.env`, усилить dev-безопасность compose.

> 💡 **Скиллы:** `docker-expert`.

### Состав работ

- [ ] Секреты через `${VAR}` из `.env`
- [ ] Bind `127.0.0.1:3001`, healthcheck Langfuse, pin `2.95.11`
- [ ] Обновить `.env.example`, `Makefile`, `devops/README.md`
- [ ] Самопроверка по критериям DoD

### Критерии готовности (DoD)

**Агент проверяет:**

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Нет plaintext-секретов в compose | просмотр `docker-compose.yml` |
| 2 | `docker compose config` валиден | `make up` dry-run |
| 3 | Langfuse healthy на :3001 | `curl /api/public/health` |

**Пользователь проверяет:**

- `cp .env.example .env` + `make up` работает без ручного редактирования compose

### Артефакты

- `devops/docker-compose.yml`, `.env.example`, `Makefile`, `devops/README.md`

### Документы

- 📋 [План задачи](tasks/06-compose-secrets-hardening/plan.md)
- 📝 [Summary](tasks/06-compose-secrets-hardening/summary.md)

---

## Итог (заполняется после закрытия)

Каркас monorepo и dev-стек готовы: `make dev` поднимает backend (`/health`), frontend-заглушку и Langfuse UI. CI и devcontainer на месте. Секреты Langfuse вынесены в `.env` (task 06).

**Отклонения:** добавлена задача 06; Langfuse v2 вместо v3; Codespaces не проверялся в приёмке.

**Дальше:** [sprint-02-mcp-tools-rag](../sprint-02-mcp-tools-rag/README.md).

📝 [Summary спринта](summary.md)
