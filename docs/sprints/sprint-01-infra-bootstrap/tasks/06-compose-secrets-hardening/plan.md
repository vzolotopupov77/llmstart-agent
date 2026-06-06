# Task 06: compose-secrets-hardening

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** chore  
> **Ветка:** `chore/infra-4-compose-secrets-hardening`  
> **Spec:** без spec — ревью docker-expert по [devops/docker-compose.yml](../../../../../devops/docker-compose.yml)

---

## Цель

Вынести секреты Langfuse compose из git в `.env`, усилить dev-безопасность (bind 127.0.0.1, healthcheck, pin образа).

---

## Состав работ

- [ ] `docker-compose.yml`: `${VAR}` из `.env`, bind `127.0.0.1:3001`, healthcheck `/api/public/health`, pin `langfuse/langfuse:2.95.11`
- [ ] `.env.example`: `LANGFUSE_POSTGRES_PASSWORD`, `LANGFUSE_NEXTAUTH_SECRET`, `LANGFUSE_SALT`, `LANGFUSE_ENCRYPTION_KEY`, `LANGFUSE_NEXTAUTH_URL`
- [ ] `Makefile`: `make up` / `make down` с `--env-file .env`
- [ ] `devops/README.md`: инструкция по генерации секретов (`openssl rand -hex 32`)
- [ ] Самопроверка: `docker compose config`, `make up` (если Docker доступен)
- [ ] (после «ок» пользователя) Создать `summary.md`, обновить sprint README.md

---

## Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | В `docker-compose.yml` нет plaintext-секретов | `grep` по NEXTAUTH_SECRET / ENCRYPTION_KEY |
| 2 | `docker compose --env-file .env -f devops/docker-compose.yml config` валиден | команда из корня |
| 3 | `cp .env.example .env` + `make up` поднимает Langfuse на 127.0.0.1:3001 | `curl http://127.0.0.1:3001/api/public/health` |
| 4 | Healthcheck langfuse в `docker compose ps` → healthy | после ~2 мин старта |

---

## Артефакты

- `devops/docker-compose.yml`
- `.env.example`
- `Makefile`
- `devops/README.md`

---

## Scope

**Трогаем:** только артефакты выше.

**НЕ трогаем:**
- backend, frontend, CI workflow
- Langfuse SDK в backend (sprint-03)

---

## Риски и допущения

- Допущение: dev-дефолты в `.env.example` — только для локалки; в prod — новые секреты.
- Риск: без `.env` compose падает — `make up` проверяет наличие файла.

---

## Открытые вопросы

- [ ] Нет блокирующих.
