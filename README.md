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
| Langfuse UI | http://localhost:3001 |

## Структура проекта

```
llmstart-agent/
├── backend/           # Agent Core (FastAPI, ReAct, MCP-клиент)
├── frontend/          # Next.js веб-виджет
├── bot/               # Telegram-бот (aiogram)
├── mcp_server/        # MCP-сервер инструментов (RAG, каталог, лиды)
├── data/              # База знаний, каталог, leads.txt
├── devops/            # docker-compose, Langfuse
└── docs/              # Концепт, roadmap, спринты
```

## Команды (make)

| Команда | Описание |
|---------|----------|
| `make dev` | Langfuse + backend :8003 + frontend :3002 + Telegram-бот |
| `make dev-bot` | Только Telegram-бот (backend должен быть запущен) |
| `make up` / `make down` | Docker Compose (Langfuse) |
| `make lint` / `make format` | Качество кода |
| `make test` / `make ci` | Тесты и полный CI-цикл |
| `make test-mcp` | Тесты MCP-сервера |
| `make test-bot` | Тесты Telegram-бота |
| `make reindex` | Переиндексация RAG (Chroma в `data/.chroma/`) |

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

Текущий спринт: [sprint-06-telegram-funnel](docs/sprints/sprint-06-telegram-funnel/README.md).
