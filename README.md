# LLMStart Agent

Публичный AI-ассистент [llmstart.ru](https://llmstart.ru): первая линия продаж и консультаций (B2C/B2B). Единый Agent Core, инструменты в MCP, каналы web и Telegram.

Подробная документация: [`docs/README.md`](docs/README.md).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2
- [uv](https://docs.astral.sh/uv/) (Python 3.12+)
- [pnpm](https://pnpm.io/) (Node 20+)
- [make](https://www.gnu.org/software/make/) (Git Bash / WSL / Linux / macOS)

## Quick start

```bash
cp .env.example .env
# Заполните OPENAI_API_KEY и при необходимости LANGFUSE_* (см. devops/README.md)

make dev
```

После запуска:

| Сервис | URL |
|--------|-----|
| Backend (health / chat) | http://localhost:8003/health , `POST /api/v1/chat` |
| Frontend (виджет) | http://localhost:3002 |
| Telegram-бот | long polling (`make dev-bot`, нужен `TELEGRAM_BOT_TOKEN`) |
| Langfuse UI (v3) | http://localhost:3001 |

## Структура проекта

```
llmstart-agent/
├── backend/           # Agent Core (FastAPI, ReAct, MCP-клиент)
├── frontend/          # Next.js веб-виджет
├── bot/               # Telegram-бот (aiogram)
├── mcp_server/        # MCP-сервер инструментов (RAG, каталог, лиды)
├── data/              # База знаний, каталог, leads.txt
├── datasets/          # Валидационные датасеты, скрипты загрузки в Langfuse
├── evals/             # Eval-контур: конфиги, датасеты, отчёты, скрипты
├── practice/redteam/  # Security-baseline Promptfoo (sprint-11)
├── devops/            # docker-compose, Langfuse v3
└── docs/              # Концепт, roadmap, ADR, спринты
```

## Команды (make)

Полный список: **`make help`** (или просто `make`).

**Dev**

| Команда | Описание |
|---------|----------|
| `make dev` | Весь стек: Langfuse + backend :8003 + frontend :3002 + Telegram-бот |
| `make dev-backend` / `dev-frontend` / `dev-bot` | Отдельные сервисы |
| `make up` / `make down` | Docker Compose (Langfuse v3, Qdrant, …) |

**Качество и тесты**

| Команда | Описание |
|---------|----------|
| `make lint` / `make format` / `make typecheck` | Linters, форматтеры, type checkers |
| `make test` / `make test-backend` / `make test-mcp` | Тесты (pytest / vitest) |
| `make ci` | Полный CI-цикл: lint + typecheck + test |

**Данные и индексация**

| Команда | Описание |
|---------|----------|
| `make index` | Индексация базы знаний в Qdrant (md, txt, pdf) — production |
| `make index BACKEND=pgvector` | Индексация в pgvector |
| `make bench` | Benchmark всех retriever-бэкендов (Qdrant, ChromaDB, pgvector) |
| `make bench RETRIEVER_BACKEND=qdrant` | Benchmark одного бэкенда |
| `make upload-langfuse-dataset` | Загрузка JSONL-датасета в Langfuse (upsert) |
| `make reload-langfuse-dataset` | Полная перезагрузка датасета в Langfuse |

**Eval**

| Команда | Описание |
|---------|----------|
| `make eval-experiment` | Прогон эксперимента по конфигу |
| `make eval-analyze` | Анализ JSON-отчёта → markdown |
| `make eval-compare` | Сравнение двух прогонов |
| `make eval-validate` / `eval-sync` | Проверка контура и синхронизация датасетов |

## MCP-сервер (stdio)

Инструменты агента вынесены в `mcp_server/`: RAG по `data/b2b/` и `data/b2c/`, каталог, мок-оплата, лиды.

```bash
cd mcp_server && uv run python -m mcp_server
```

Подробнее: [`mcp_server/README.md`](mcp_server/README.md).

## Agent Core

ReAct-агент в `backend/`: `POST /api/v1/chat` (JSON + SSE), `GET /api/v1/products`, MCP tools, сессии, Langfuse.

```bash
# JSON (Telegram, простые клиенты)
curl -s -X POST http://localhost:8003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"message":"Привет","channel":"telegram"}'

# SSE (виджет)
curl -N -X POST http://localhost:8003/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message":"Привет","channel":"web"}'

# Каталог B2C
curl -s "http://localhost:8003/api/v1/products"
```

Подробнее: [`backend/README.md`](backend/README.md).

## Telegram-бот

Long polling, тот же Core API, `channel=telegram`, handoff `session_id` с виджета.

```bash
# TELEGRAM_BOT_TOKEN в .env
make dev-bot
```

Подробнее: [`bot/README.md`](bot/README.md).

## Roadmap

| Этап | Статус | Описание |
|------|--------|----------|
| **v0.1 MVP** | ✅ Done | sprint-01…06: агент, RAG, web-виджет, Telegram, воронка |
| **v0.2 Развитие RAG-ассистента** | 🚧 In Progress | GraphRAG ✅, мультимодал ✅; context-engineering — TBD |
| **v0.3 Hardening** | 🚧 In Progress | Red-team baseline ✅ (sprint-11); guardrails/rate limits — TBD |
| **v1.0 Production** | 📋 Planned | Реальные платежи, CRM, Postgres |

Закрытые спринты v0.1–v0.3:

| Sprint | Статус |
|--------|--------|
| [07 langfuse-v3](docs/sprints/sprint-07-langfuse-v3/README.md) | ✅ self-hosted Langfuse v3, трейсы в UI |
| [08 vector-db](docs/sprints/sprint-08-vector-db/README.md) | ✅ Qdrant production, pgvector bench, retriever-абстракция |
| [09 graphrag](docs/sprints/sprint-09-graphrag/README.md) | ✅ Neo4j KG, graph/global/text2cypher retrieval |
| [10 multimodal-rag](docs/sprints/sprint-10-multimodal-rag/README.md) | ✅ 5 методов индексации, вердикт — метод C |
| [11 red-teaming-baseline](docs/sprints/sprint-11-red-teaming-baseline/README.md) | ✅ Promptfoo до/после, фиксы за `SECURITY_ENABLED` · [отчёт](practice/redteam/final-report.md) |

Сводка: [`docs/roadmap.md`](docs/roadmap.md).
