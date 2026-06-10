# DevOps — локальная инфраструктура

## Langfuse v3 (self-hosted)

Локальная observability: **Langfuse v3** (`langfuse-web` **3.125.0**) в Docker Compose.

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
| langfuse-web | `langfuse/langfuse:3.125.0` |
| langfuse-worker | digest-pinned (см. `docker-compose.yml`) |
| clickhouse | `clickhouse/clickhouse-server:24.8` |
| redis | `redis:7.4.2-alpine` |
| minio | `minio/minio:RELEASE.2024-11-07T00-52-20Z` |
| postgres | `postgres:15` |
