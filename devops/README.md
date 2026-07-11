# DevOps — локальная инфраструктура

## Langfuse v3 (self-hosted)

Локальная observability: **Langfuse v3** (`langfuse-web` **3.185.0**) в Docker Compose.

Стек: `langfuse-web`, `langfuse-worker`, Postgres, ClickHouse, Redis, MinIO. UI на **:3001**.

### Подготовка

Секреты compose **не хранятся в git** — только в корневом `.env`:

```bash
cp .env.example .env
```

Для production сгенерируйте новые значения:

```bash
openssl rand -hex 32   # LANGFUSE_ENCRYPTION_KEY
openssl rand -base64 32  # LANGFUSE_NEXTAUTH_SECRET, LANGFUSE_SALT
```

Переменные compose (см. `.env.example`):

| Переменная | Назначение |
|------------|------------|
| `LANGFUSE_POSTGRES_PASSWORD` | Пароль Postgres (`langfuse-db`) |
| `LANGFUSE_NEXTAUTH_SECRET` | NextAuth secret |
| `LANGFUSE_SALT` | Langfuse salt |
| `LANGFUSE_ENCRYPTION_KEY` | 64 hex-символа |
| `LANGFUSE_NEXTAUTH_URL` | URL UI (default `http://localhost:3001`) |
| `LANGFUSE_CLICKHOUSE_USER` / `LANGFUSE_CLICKHOUSE_PASSWORD` | ClickHouse |
| `LANGFUSE_REDIS_AUTH` | Redis password |
| `LANGFUSE_MINIO_ROOT_USER` / `LANGFUSE_MINIO_ROOT_PASSWORD` | MinIO (S3 blob store) |
| `LANGFUSE_S3_EVENT_UPLOAD_BUCKET` | Bucket для событий (default `langfuse`) |

Backend SDK (отдельно от compose):

| Переменная | Назначение |
|------------|------------|
| `LANGFUSE_PUBLIC_KEY` | Public key проекта |
| `LANGFUSE_SECRET_KEY` | Secret key проекта |
| `LANGFUSE_HOST` | `http://localhost:3001` |

### Запуск

Из корня репозитория:

```bash
make up      # см. также make help
```

Или напрямую:

```bash
docker compose --env-file .env -f devops/docker-compose.yml up -d
```

Первый старт занимает **2–3 минуты** (миграции Postgres/ClickHouse). Дождитесь `healthy` у `langfuse-web`:

```bash
docker compose --env-file .env -f devops/docker-compose.yml ps
```

UI: http://127.0.0.1:3001 (bind только на localhost)

Healthcheck:

```bash
curl http://127.0.0.1:3001/api/public/health
```

OTLP endpoint (для SDK v3+): `POST /api/public/otel/v1/traces` — на v3 отвечает **не 404** (в отличие от v2).

### Первый вход

1. Откройте http://localhost:3001
2. Создайте аккаунт (локальный dev-инстанс)
3. Создайте проект и скопируйте ключи в `.env`:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3001
```

### Остановка

```bash
make down
```

### Upgrade v2 → v3 (dev, clean start)

Рекомендуемый путь при апгрейде с Langfuse **v2.95.11**: **чистый старт** (dev-данные не критичны).

> **Внимание:** шаги ниже **удаляют все данные** Langfuse (трейсы, проекты, datasets в UI).

1. Остановить стек и удалить volumes:

```bash
make down
docker compose --env-file .env -f devops/docker-compose.yml down --remove-orphans -v
```

2. Обновить `.env` — добавить новые переменные из `.env.example` (ClickHouse, Redis, MinIO).

3. Поднять v3:

```bash
make up
```

4. Дождаться `langfuse-web` → `healthy` (~2–3 мин).

5. UI → новый аккаунт → новый проект → обновить `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` в `.env`.

6. Перезапустить backend (`make dev-backend`), чтобы подхватить новые ключи.

Старые API keys от v2 **невалидны** после clean start.

### Проверка trace за turn

См. [backend/README.md](../backend/README.md#langfuse) — runbook E2E после `make up` + `LANGFUSE_*` + `OPENAI_API_KEY`.

### Eval-датасеты в Langfuse

После `make up` и настройки API keys можно загрузить валидационный датасет из репозитория:

```bash
make upload-langfuse-dataset
# полная перезагрузка items
make reload-langfuse-dataset
```

Default: датасет `llmstart-agent-v1` из `datasets/b2c/v2/dataset.jsonl`. Переменные и другие цели — `make help`.

### Troubleshooting

#### Dataset Runs без items / метрик в UI

**Симптом:** в Langfuse Dataset → Runs run есть, но items/scores пустые; `dataset_run_items.list()` → 0.

**Частая причина:** рассинхрон `langfuse-web` и `langfuse-worker` (разные версии образов) или неприменённые миграции Postgres.

```bash
# мягкий путь: pull + recreate (данные сохраняются)
make up
# дождаться healthy langfuse-web и "All migrations have been successfully applied" в логах
make eval-validate   # включает check_langfuse_contracts
```

Если не помогло — проверить worker logs (`dataset-run-item-upsert` / Prisma errors). Крайний случай: `down -v` + `make up` + `make eval-sync` (потеря локальных traces/datasets).

#### P1000 (неверный пароль Postgres)

Пароль в `.env` не совпадает с тем, что записан в Docker volume при первом запуске.

```bash
docker compose --env-file .env -f devops/docker-compose.yml down -v
make up
```

#### Orphan container `devops-langfuse-1` (v2)

После апгрейда остался контейнер v2:

```bash
docker compose --env-file .env -f devops/docker-compose.yml down --remove-orphans
make up
```

#### `make up` зависает на Starting / контейнеры в Created

Docker Desktop (WSL2) иногда «залипает» — контейнеры создаются, но не стартуют, даже `docker run hello-world` висит.

```bash
wsl --shutdown
docker desktop start
make up
```

Если не помогло — Docker Desktop → Troubleshoot → Restart.

#### `make up` падает на pull (TLS handshake timeout)

Образы Langfuse уже есть локально — `make up` больше не тянет их принудительно. Для явного обновления:

```bash
make up PULL=1
```

#### Qdrant unhealthy

В образе `qdrant/qdrant` нет `curl`/`wget`. После обновления compose:

```bash
docker compose --env-file .env -f devops/docker-compose.yml up -d --force-recreate qdrant
```

#### `make up` падает на ClickHouse unhealthy

- Подождите 30–60 с после первого старта.
- Если не помогло — сброс volumes ClickHouse: `down -v` и `make up`.
- На слабых машинах (Codespaces) v3 требует больше RAM, чем v2 (~4 CPU / 8+ GiB рекомендуется).

#### Отсутствуют новые env при `make up`

Ошибка `LANGFUSE_MINIO_ROOT_PASSWORD is required` — скопируйте секцию Langfuse v3 из `.env.example` в `.env`.

#### Трейсы не в UI

1. Проверьте `LANGFUSE_*` keys в `.env` (после clean start — новые).
2. `curl http://127.0.0.1:3001/api/public/health` → 200.
3. Backend логи: `Langfuse client initialized`.
4. Подождите ~30 с — ingestion асинхронный (ClickHouse).

## Qdrant (Vector DB)

RAG-слой (sprint-08). Поднимается вместе со стеком через `make up`.

Порты (только localhost): REST `:6333`, gRPC `:6334`.

### Проверка сервиса

```bash
# health endpoint
curl http://127.0.0.1:6333/healthz
# → OK

# версия и статус
curl http://127.0.0.1:6333/
```

```bash
# compose status
docker compose --env-file .env -f devops/docker-compose.yml ps qdrant
```

Ожидание: статус `healthy`.

### Первый запуск

После `make up` индекс пуст — наполнить через:

```bash
make index
```

### Persistence

Данные хранятся в named volume `qdrant_data`. При `make down` данные **сохраняются**.
Полный сброс (при смене модели или коллекции):

```bash
docker compose --env-file .env -f devops/docker-compose.yml down -v
make up
make index
```

## Neo4j (Graph DB)

GraphRAG-слой (sprint-09). Поднимается вместе со стеком через `make up` или отдельно через `make graph-up`.

Порты (только localhost): Browser **:7474**, Bolt **:7687**.

Образ: `neo4j:2026.04.0-community` (ADR-0010), плагин APOC включён.

### Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `NEO4J_URI` | Bolt URI для Python-клиента (default `bolt://localhost:7687`) |
| `NEO4J_USER` | Admin-пользователь (default `neo4j`) |
| `NEO4J_PASSWORD` | Пароль admin (compose: `NEO4J_AUTH`) |
| `NEO4J_RO_USER` | Read-only пользователь для text2cypher (default `text2cypher_ro`) |
| `NEO4J_RO_PASSWORD` | Пароль RO-пользователя |

Dev-дефолты — в `.env.example`. Скопируйте секцию Neo4j в `.env` перед первым запуском.

### Make-цели

| Цель | Назначение |
|------|------------|
| `make graph-up` | Поднять только Neo4j |
| `make graph-down` | Остановить Neo4j (данные в volume сохраняются) |
| `make graph-status` | Статус контейнера + smoke (`Connection OK`) |
| `make graph-shell` | Интерактивный cypher-shell (admin, без ручного `docker exec`) |
| `make graph-init-ro` | Создать RO-пользователя `text2cypher_ro` (один раз после первого `graph-up`) |

### Первый запуск

```bash
# 1. Убедитесь, что в .env есть секция Neo4j (см. .env.example)
make graph-up
# 2. Дождитесь healthy (~30–60 с)
docker compose --env-file .env -f devops/docker-compose.yml ps neo4j
# 3. RO-пользователь для text2cypher (Task 07)
make graph-init-ro
# 4. Проверка
make graph-status
# → Connection OK
```

Browser: http://127.0.0.1:7474 — логин `NEO4J_USER` / `NEO4J_PASSWORD`.

Healthcheck в compose: `cypher-shell RETURN 1` через Bolt (endpoint `/db/neo4j/available` на 2026.04 возвращает 404).

Проверка HTTP (без auth):

```bash
curl http://127.0.0.1:7474/
```

### Read-only пользователь (text2cypher)

Guardrail #1 из ADR-0010: NL→Cypher выполняется под отдельным пользователем (`NEO4J_RO_*`), не под admin.

> **Community Edition:** роль `reader` (`GRANT ROLE`) доступна только в Enterprise. На Community создаётся отдельный пользователь; write-блокировка обеспечивается guardrails 2–4 в Task 07 (regex, LIMIT, tool scope).

Создание (idempotent):

```bash
make graph-init-ro
```

Реализация: Python-скрипт `mcp_server/scripts/neo4j_init_ro.py` (admin credentials из `.env`).

```cypher
CREATE USER text2cypher_ro IF NOT EXISTS
  SET PASSWORD 'your-ro-password' CHANGE NOT REQUIRED;
GRANT ROLE reader TO text2cypher_ro;
```

Справочный файл: [devops/neo4j/init-text2cypher-ro.cypher](neo4j/init-text2cypher-ro.cypher).

Проверка RO (через `make graph-shell` от admin или отдельную сессию):

```bash
docker compose --env-file .env -f devops/docker-compose.yml exec neo4j \
  cypher-shell -u text2cypher_ro -p "$NEO4J_RO_PASSWORD" -a bolt://localhost:7687 \
  "RETURN 1 AS ok;"
```

Write-запрос от RO должен быть отклонён:

```cypher
CREATE (n:Test {id: 'x'});
-- Expected: permission denied
```

### Persistence

Данные хранятся в named volumes `neo4j_data` и `neo4j_logs`. При `make graph-down` данные **сохраняются**.

Полный сброс:

```bash
docker compose --env-file .env -f devops/docker-compose.yml down -v
make graph-up
make graph-init-ro
```

Граф пуст до `make graph-index` (Task 05).

## Альтернатива: Langfuse Cloud

В `.env` укажите облачный хост и ключи — compose для Langfuse не обязателен:

```env
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Безопасность (dev)

- Postgres, ClickHouse, Redis, MinIO **не** проброшены на host
- Langfuse UI слушает только `127.0.0.1:3001`
- Секреты в `.env` (в `.gitignore`), не в `docker-compose.yml`

## Образы (pin)

| Сервис | Образ |
|--------|-------|
| langfuse-web | `langfuse/langfuse:3.185.0` |
| langfuse-worker | `langfuse/langfuse-worker:3.185.0` (тег должен совпадать с web) |
| clickhouse | `clickhouse/clickhouse-server:24.8` |
| redis | `redis:7.4.2-alpine` |
| minio | `minio/minio:RELEASE.2024-11-07T00-52-20Z` |
| postgres | `postgres:15` |
| qdrant | `qdrant/qdrant:v1.18.2` |
| neo4j | `neo4j:2026.04.0-community` |
| pgvector | `pgvector/pgvector:pg17` |
