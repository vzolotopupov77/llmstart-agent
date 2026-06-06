# Task 01: monorepo-scaffold

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** chore  
> **Ветка:** `chore/infra-1-monorepo-scaffold`  
> **Spec:** без spec — см. [vision.md §6](../../../../concept/vision.md#6-структура-проекта)

---

## Цель

Создать каркас monorepo с каталогами всех компонентов MVP, корневым README и `.gitignore` — фундамент для последующих задач спринта.

---

## Состав работ

- [ ] Создать директории: `backend/`, `frontend/`, `bot/`, `mcp_server/`, `data/`, `devops/`
- [ ] Создать `data/b2b/`, `data/b2c/` с `.gitkeep`; пустой `data/leads.txt`; `data/.chroma/` в `.gitignore`
- [ ] Написать корневой `README.md`: назначение проекта, структура каталогов, prerequisites (Docker, uv, pnpm, make)
- [ ] Обновить `.gitignore`: `.env`, `node_modules/`, `__pycache__/`, `.venv/`, `data/.chroma/`, `.next/`, OS-артефакты
- [ ] Самопроверка по критериям DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Каталоги `backend/`, `frontend/`, `bot/`, `mcp_server/`, `data/`, `devops/` существуют | `ls` корня репо |
| 2 | `data/b2b/`, `data/b2c/`, `data/leads.txt` на месте | `test -f data/leads.txt` |
| 3 | `.env` в `.gitignore`, `.env.example` не игнорируется | `git check-ignore -v .env` |
| 4 | README описывает структуру и ссылается на `docs/` | Ручной просмотр |

---

## Артефакты

- `README.md` — quick start (без `make dev` до задачи 04; placeholder «см. sprint-01»)
- `.gitignore` — секреты и артефакты сборки
- `data/b2b/.gitkeep`, `data/b2c/.gitkeep`, `data/leads.txt`

---

## Scope

**Трогаем:** только файлы из списка «Артефакты» + создание пустых директорий.

**НЕ трогаем:**
- `backend/`, `frontend/` — код сервисов (задачи 02, 04)
- `devops/` — docker-compose (задача 03)
- `docs/roadmap.md` — обновление статуса только после закрытия спринта

---

## Риски и допущения

- Допущение: monorepo без git submodules — все компоненты в одном репозитории.
- Риск: дублирование README с `docs/README.md` — корневой README краткий, детали в `docs/`.

---

## Открытые вопросы

- [ ] Нет блокирующих — структура зафиксирована в vision §6.
