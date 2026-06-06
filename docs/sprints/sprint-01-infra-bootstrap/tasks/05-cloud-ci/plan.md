# Task 05: cloud-ci

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** chore  
> **Ветка:** `chore/infra-3-cloud-ci`  
> **Spec:** без spec — см. `.methodology/ci/github-actions/default.yml.template`

---

## Цель

Devcontainer для Codespaces / VS Code и GitHub Actions CI для backend — репозиторий готов к облачной разработке и автопроверкам на PR.

---

## Состав работ

- [ ] `.devcontainer/devcontainer.json`: Python 3.12, Node 20, Docker-in-Docker, features uv + pnpm
- [ ] `postCreateCommand`: `cd backend && uv sync`; `cd frontend && pnpm install`; echo hint про `.env`
- [ ] `postStartCommand`: опционально `make up` для Langfuse
- [ ] `.github/workflows/ci.yml` по шаблону methodology: backend job (ruff, format, mypy, pytest)
- [ ] Frontend CI job — только если `frontend/` уже с lint (минимум: `pnpm lint` или skip с комментарием до sprint-05)
- [ ] Самопроверка по критериям DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | CI workflow синтаксически валиден, backend job зелёный | push / `gh run list` |
| 2 | devcontainer.json парсится Dev Containers extension | Открыть в Codespaces |
| 3 | В Codespaces `make dev` работает после post-create | Ручная проверка |
| 4 | Backend tests в CI без секретов (mock env) | CI log |

---

## Артефакты

- `.devcontainer/devcontainer.json`
- `.github/workflows/ci.yml`

---

## Scope

**Трогаем:** `.devcontainer/**`, `.github/workflows/ci.yml`.

**НЕ трогаем:**
- Deploy workflow — post-MVP
- Bot / mcp_server CI jobs — добавятся в соответствующих спринтах
- Secrets в GitHub (OPENAI_KEY) — не нужны для health-тестов

---

## Риски и допущения

- Допущение: CI backend не вызывает OpenRouter — тесты изолированы.
- Риск: Docker-in-Docker в Codespaces — использовать встроенный Docker или host socket по документации GitHub.
- Митигация: `make up` в postStart опционален, не блокирует dev без Docker.

---

## Открытые вопросы

- [ ] Frontend CI: включить базовый `pnpm build` или отложить до sprint-05 — решение: включить lint+build заглушки в этой задаче.
