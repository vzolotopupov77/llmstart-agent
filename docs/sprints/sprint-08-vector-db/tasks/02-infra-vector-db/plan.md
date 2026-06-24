# Plan: 02-infra-vector-db

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-22

## Цель

Добавить Qdrant в docker-compose; `make up` поднимает его с health check.

## Состав работ

- Добавить сервис `qdrant` в `devops/docker-compose.yml`: образ `qdrant/qdrant:v1.18.2`, порты 6333/6334, health check, named volume
- Добавить `qdrant_data` в раздел `volumes:`
- Обновить `.env.example`: `RETRIEVER_BACKEND`, `QDRANT_URL`, `QDRANT_COLLECTION`
- Обновить `devops/README.md`: раздел «Qdrant (Vector DB)», строка в таблице образов

## DoD

- [ → ✅] `make up` поднимает стек; health check qdrant `healthy`
- [ → ✅] `docker compose down && make up` — данные не теряются (named volume)
- [ → ✅] `.env.example` содержит все новые переменные с комментариями

## Артефакты

- `devops/docker-compose.yml` (обновлён)
- `.env.example` (обновлён)
- `devops/README.md` (обновлён)

## Scope

**In:** инфраструктура compose и env-переменные.  
**Out:** `qdrant-client` в Python-зависимостях (Task 04), `make index` (Task 03).
