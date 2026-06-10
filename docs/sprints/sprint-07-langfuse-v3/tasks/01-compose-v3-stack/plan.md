# Task 01: compose-v3-stack

> **Sprint:** [../../README.md](../../README.md)  
> **Ветка:** `chore/infra-3-langfuse-v3-compose`

## Цель

Заменить Langfuse v2 compose на v3 stack с пинами образов и секретами из `.env`.

## Scope

- `devops/docker-compose.yml`
- `.env.example`

## DoD

| # | Критерий |
|---|----------|
| 1 | `make up` — healthy: web, worker, db, clickhouse, redis, minio |
| 2 | UI `127.0.0.1:3001` |
| 3 | Internal-only storage services |
