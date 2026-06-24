# Summary: 03-indexing-pipeline

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-23

## Что сделано

### mcp_server/mcp_server/rag/qdrant_indexer.py

Qdrant-индексатор:
- Рекурсивный обход `DATA_DIR` — файлы `.md`, `.txt`, `.pdf`; скрытые пути пропускаются
- Чанкинг через `chunk_markdown` (`RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`)
- Эмбеддинги через OpenRouter (`EMBEDDING_MODEL`, `OPENAI_API_KEY`)
- Idempotent upsert в Qdrant по `uuid5(relative_path:chunk_index)`
- Логи: `Processing <file>: N chunks`, итог `Done: X files, Y chunks indexed`

### mcp_server/mcp_server/config.py

Добавлены `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_API_KEY`, `EMBEDDING_DIM`.  
Пустой `DATA_DIR=` трактуется как repo `data/` (дефолт).

### mcp_server/pyproject.toml

Зависимости: `qdrant-client>=1.14.0`, `pypdf>=5.0.0`.

### Makefile

Цель `make index` → `uv run python -m mcp_server.rag.qdrant_indexer`.

## Решения

| Решение | Причина |
|---------|---------|
| Upsert по UUID5, не delete+recreate | Идемпотентность без потери коллекции |
| `OPENAI_API_KEY` обязателен для CLI | MockEmbeddings (384 dim) несовместим с `EMBEDDING_DIM=1536` |
| Относительный `DATA_DIR` — от cwd `mcp_server/` | Документировано: использовать `../data` или абсолютный путь |

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Пустой `DATA_DIR=` → сканировался cwd | Validator: пустая строка → дефолт repo `data/` |
| `DATA_DIR=data/` → `mcp_server/data/` (0 файлов) | Рекомендация: `../data` или убрать переменную |
| Первый прогон индексировал `.venv` | Исправлен DATA_DIR + skip hidden paths |

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make index` завершается с кодом 0 | ✅ (25 files, 204 chunks при полном `data/`) |
| 2 | Повторный `make index` не дублирует | ✅ upsert по стабильному id |
| 3 | Логи: N файлов, M чанков | ✅ |
| 4 | `ruff check .` зелёный | ✅ |
| 5 | `pytest` mcp_server | ✅ 19 passed |

## Что дальше

- Task 04: абстрактный `BaseRetriever` + `QdrantRetriever`, переписать `search_knowledge_base`
