# Summary: Task 01 — compose-v3-stack

- Переписан `devops/docker-compose.yml`: 6 сервисов v3
- Образы: `langfuse:3.125.0`, worker digest-pinned, `clickhouse:24.8`, `redis:7.4.2-alpine`, `minio:RELEASE.2024-11-07`, `postgres:15`
- `.env.example`: ClickHouse, Redis, MinIO vars
- Проверено: `make up`, все контейнеры healthy
