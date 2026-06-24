# Summary: 02-infra-vector-db

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-22

## Что сделано

### devops/docker-compose.yml

Добавлен сервис `qdrant`:
- Образ: `qdrant/qdrant:v1.18.2`
- Порты: `127.0.0.1:6333` (REST), `127.0.0.1:6334` (gRPC)
- Health check: `curl -fsS http://127.0.0.1:6333/healthz`
- Named volume: `qdrant_data:/qdrant/storage`

### .env.example

Добавлена секция:
```bash
RETRIEVER_BACKEND=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=knowledge_base
```

### devops/README.md

- Раздел «Qdrant (Vector DB)»: проверка, первый запуск, persistence, полный сброс
- Таблица образов: строка `qdrant/qdrant:v1.18.2`

## Решения

- Порты привязаны к `127.0.0.1` (тот же паттерн, что у `langfuse-web`) — не проброшены публично
- Использована существующая сеть `langfuse_net` — dev-стек единый
- `make up` пропускает pull при запуске с локальными образами через `docker compose up -d` напрямую

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make up` поднимает стек; health check `healthy` | ✅ |
| 2 | Named volume — данные сохраняются после `down && up` | ✅ |
| 3 | `.env.example` содержит новые переменные | ✅ |
