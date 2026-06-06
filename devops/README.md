# DevOps — локальная инфраструктура

## Langfuse (self-hosted)

MVP использует Langfuse v2 (`2.95.11`) в Docker Compose для локальной observability.

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

Переменные compose:

| Переменная | Назначение |
|------------|------------|
| `LANGFUSE_POSTGRES_PASSWORD` | Пароль Postgres (langfuse-db) |
| `LANGFUSE_NEXTAUTH_SECRET` | NextAuth secret |
| `LANGFUSE_SALT` | Langfuse salt |
| `LANGFUSE_ENCRYPTION_KEY` | 64 hex-символа |
| `LANGFUSE_NEXTAUTH_URL` | URL UI (default `http://localhost:3001`) |

### Запуск

Из корня репозитория:

```bash
make up
```

Или напрямую:

```bash
docker compose --env-file .env -f devops/docker-compose.yml up -d
```

UI: http://127.0.0.1:3001 (bind только на localhost)

Healthcheck: `curl http://127.0.0.1:3001/api/public/health`

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

### Troubleshooting: P1000 (неверный пароль Postgres)

Ошибка `Authentication failed ... credentials for postgres are not valid` — **пароль в `.env` не совпадает с тем, что записан в Docker volume** при первом запуске. Postgres меняет пароль только при инициализации пустого volume.

**Вариант A** — сбросить dev-данные Langfuse (обычно достаточно):

```bash
docker compose --env-file .env -f devops/docker-compose.yml down -v
make up
```

**Вариант B** — вернуть в `.env` тот же `LANGFUSE_POSTGRES_PASSWORD`, с которым volume создавался изначально (часто `postgres` из `.env.example`).

> После смены `LANGFUSE_POSTGRES_PASSWORD` всегда либо `down -v`, либо совпадение с уже существующим volume.

## Альтернатива: Langfuse Cloud

В `.env` укажите облачный хост и ключи — compose для Langfuse не обязателен:

```env
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Безопасность (dev)

- Postgres **не** проброшен на host
- Langfuse UI слушает только `127.0.0.1:3001`
- Секреты в `.env` (в `.gitignore`), не в `docker-compose.yml`
