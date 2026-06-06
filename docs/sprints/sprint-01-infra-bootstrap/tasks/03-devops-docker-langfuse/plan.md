# Task 03: devops-docker-langfuse

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** chore  
> **Ветка:** `chore/infra-2-docker-langfuse`  
> **Spec:** без spec — см. [integrations.md §4](../../../../concept/integrations.md#4-langfuse-observability)

---

## Цель

Docker Compose в `devops/` с self-hosted Langfuse и Postgres для локальной observability (UI на :3001).

---

## Состав работ

- [ ] `devops/docker-compose.yml`: сервисы `langfuse-db` (Postgres 15), `langfuse` (официальный образ)
- [ ] Проброс порта `3001:3000` для Langfuse UI
- [ ] Health checks: Postgres ready → Langfuse start
- [ ] Volumes для персистентности Postgres (dev)
- [ ] `devops/README.md`: переменные env, `docker compose up`, первый вход в UI
- [ ] Согласовать `.env.example`: `LANGFUSE_HOST=http://localhost:3001` для self-hosted
- [ ] Самопроверка по критериям DoD
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Compose поднимается без ошибок | `docker compose -f devops/docker-compose.yml up -d` |
| 2 | Langfuse UI отвечает на :3001 | `curl -s -o /dev/null -w "%{http_code}" http://localhost:3001` → 200/302 |
| 3 | Postgres healthy | `docker compose -f devops/docker-compose.yml ps` |
| 4 | `make down` (после задачи 04) останавливает compose | `make down` |

---

## Артефакты

- `devops/docker-compose.yml` — Langfuse + Postgres
- `devops/README.md` — инструкция по infra
- `.env.example` — уточнение `LANGFUSE_HOST` (если нужно)

---

## Scope

**Трогаем:** `devops/**`, `.env.example` (только Langfuse-секция).

**НЕ трогаем:**
- `backend/`, `frontend/`, `bot/` — без Dockerfile сервисов на этом этапе
- Интеграция Langfuse SDK в backend — sprint-03
- Production deploy, TLS, reverse proxy

---

## Риски и допущения

- Допущение: self-hosted Langfuse для dev; Cloud — альтернатива через смену `LANGFUSE_HOST` в `.env`.
- Риск: версии образов Langfuse — зафиксировать теги, не `latest`.
- Митигация: health checks и documented env из [Langfuse self-host docs](https://langfuse.com/docs/deployment/self-host).

---

## Открытые вопросы

- [ ] Langfuse Cloud vs self-hosted: в sprint-01 — self-hosted в compose; Cloud остаётся опцией через env.
