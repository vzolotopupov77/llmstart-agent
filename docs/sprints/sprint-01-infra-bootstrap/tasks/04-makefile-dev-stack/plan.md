# Task 04: makefile-dev-stack

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** feat  
> **Ветка:** `feat/infra-1-makefile-dev`  
> **Spec:** без spec — см. [10-conventions.mdc](../../../../.cursor/rules/methodology/10-conventions.mdc) (Make — единая точка входа)

---

## Цель

Корневой `Makefile` и минимальный frontend-заглушка: `make dev` поднимает Langfuse (compose), backend :8000 и frontend :3000.

---

## Состав работ

- [ ] `Makefile` с целями: `dev`, `dev-backend`, `dev-frontend`, `up`, `down`, `lint`, `format`, `typecheck`, `test`, `test-backend`, `test-frontend`, `ci`
- [ ] `make up` → `docker compose -f devops/docker-compose.yml up -d`
- [ ] `make dev-backend` → uvicorn backend на :8000
- [ ] `make dev-frontend` → Next.js dev на :3000 (заглушка)
- [ ] Scaffold `frontend/`: pnpm, Next.js 16 App Router, Tailwind, одна страница «LLMStart Agent — dev»
- [ ] Обновить корневой `README.md`: quick start `cp .env.example .env && make dev`
- [ ] Самопроверка по критериям DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `make dev` — backend :8000, frontend :3000, Langfuse :3001 | `curl` на три порта |
| 2 | `make ci` — lint + typecheck + test backend | `make ci` |
| 3 | `make lint` / `make format` работают для backend | `make lint` |
| 4 | README quick start актуален | Ручной просмотр |

---

## Артефакты

- `Makefile` — все обязательные цели из conventions
- `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/app/page.tsx`, `frontend/tsconfig.json`, `frontend/tailwind.config.ts`
- `README.md` — обновление quick start

---

## Scope

**Трогаем:** `Makefile`, `frontend/**` (минимальный scaffold), `README.md`.

**НЕ трогаем:**
- Полноценный виджет чата — sprint-05
- `bot/`, `mcp_server/` — sprint-02, sprint-06
- CI workflow — задача 05

---

## Риски и допущения

- Допущение: `make dev` запускает backend и frontend параллельно (фоновые процессы или `make -j`).
- Риск: конфликт портов — документировать в README.
- Frontend — заглушка без вызовов API (достаточно статической страницы).

---

## Открытые вопросы

- [ ] Нет блокирующих.
