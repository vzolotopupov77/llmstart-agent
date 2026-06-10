# MCP Server — LLMStart Tools

MCP-сервер инструментов (stdio): RAG B2B/B2C, каталог продуктов, мок-оплата и лиды.

В монорепо пакет используется двумя способами:

- **Backend agent** — handlers вызываются in-process (`backend/app/mcp_client/sync_tools.py`), общий `DATA_DIR` и Chroma-индекс.
- **Standalone stdio** — `python -m mcp_server` для MCP-клиентов (Cursor, тесты subprocess).

## Tools

| Tool | Описание |
|------|----------|
| `search_knowledge_base` | Поиск по базе знаний (`query`, `segment`: `b2b` \| `b2c`) |
| `list_b2c_products` | 6 продуктов из `data/b2c/catalog.json` |
| `create_payment_link` | Мок-URL `https://pay.mock.llmstart.ru/checkout?...` |
| `confirm_payment` | Подтверждение оплаты (идемпотентно) |
| `save_lead` | Append JSON Lines в `data/leads.txt` |

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `DATA_DIR` | Путь к `data/` (по умолчанию — корень репо `/data`) |
| `OPENAI_API_KEY` | Embeddings через OpenRouter |
| `OPENAI_BASE_URL` | Default: `https://openrouter.ai/api/v1` |
| `EMBEDDING_MODEL` | Default: `openai/text-embedding-3-small` |
| `RAG_TOP_K` | Число чанков при поиске (default: 4) |
| `RAG_CHUNK_SIZE` | Размер чанка при индексации (default: 800) |
| `RAG_CHUNK_OVERLAP` | Перекрытие чанков (default: 100) |

См. корневой `.env.example`. Backend при старте прокидывает `DATA_DIR` и OpenRouter-настройки в окружение handlers.

## Запуск

```bash
# из корня репо — переиндексация Chroma
make reindex

# standalone stdio MCP (нужен OPENAI_API_KEY для авто-индексации при старте)
cd mcp_server && uv run python -m mcp_server
```

При старте сервер вызывает `ensure_index()`: если файлы в `data/b2b/` или `data/b2c/` новее манифеста — выполняется `reindex()`. Без `OPENAI_API_KEY` авто-индексация пропускается (warning в логах).

В обычной разработке MCP tools поднимаются вместе с backend:

```bash
make dev-backend   # ensure_index + agent tools in-process
```

Полный список make-целей: `make help`.

## Данные

```
data/
├── b2b/*.md          # база B2B
├── b2c/*.md          # база B2C
├── b2c/catalog.json  # каталог (6 slug)
├── leads.txt         # лиды (JSON Lines)
├── payments.json     # state мок-оплаты (создаётся tools)
└── .chroma/          # persist Chroma (в .gitignore)
```

## Качество и тесты

```bash
# из корня репо
make lint-mcp
make format-mcp
make typecheck-mcp
make test-mcp

# или локально
cd mcp_server && uv run pytest
```

Unit/integration тесты используют mock embeddings — API-ключ в CI не нужен.

## Пример вызова handler (без MCP)

```python
from mcp_server.tools.search_knowledge_base import handle_search_knowledge_base

chunks = handle_search_knowledge_base("комбо курсов", "b2c")
```
