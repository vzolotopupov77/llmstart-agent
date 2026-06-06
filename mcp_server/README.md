# MCP Server — LLMStart Tools

MCP-сервер инструментов (stdio): RAG B2B/B2C, каталог продуктов, мок-оплата и лиды.

## Tools

| Tool | Описание |
|------|----------|
| `search_knowledge_base` | Поиск по базе знаний (`segment`: `b2b` \| `b2c`) |
| `list_b2c_products` | 6 продуктов из `data/b2c/catalog.json` |
| `create_payment_link` | Мок-URL `https://pay.mock.llmstart.ru/checkout?...` |
| `confirm_payment` | Подтверждение оплаты (идемпотентно) |
| `save_lead` | Append JSON Lines в `data/leads.txt` |

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `DATA_DIR` | Путь к `data/` (по умолчанию — корень репо) |
| `OPENAI_API_KEY` | Embeddings через OpenRouter |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` |
| `EMBEDDING_MODEL` | напр. `openai/text-embedding-3-small` |
| `RAG_TOP_K` | Число чанков при поиске (default: 4) |

См. корневой `.env.example`.

## Запуск

```bash
# из корня репо (нужен OPENAI_API_KEY для авто-индексации при старте)
cd mcp_server && uv run python -m mcp_server

# или
make reindex   # переиндексация Chroma в data/.chroma/
```

При старте сервер вызывает `ensure_index()`: если файлы в `data/b2b/` или `data/b2c/` новее манифеста — выполняется `reindex()`.

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

## Тесты

```bash
make test-mcp
# или
cd mcp_server && uv run pytest
```

Unit/integration тесты используют mock embeddings — API-ключ в CI не нужен.

## Пример вызова handler (без MCP)

```python
from mcp_server.tools.search_knowledge_base import handle_search_knowledge_base

chunks = handle_search_knowledge_base("комбо курсов", "b2c")
```
