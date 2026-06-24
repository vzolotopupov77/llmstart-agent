# Summary: 04-semantic-retriever

> **Sprint:** 08 vector-db  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-23

## Что сделано

### mcp_server/mcp_server/retriever/

Новый пакет с абстракцией retriever:

- `base.py` — `BaseRetriever` (Protocol), `KnowledgeChunk`, `IndexNotReadyError`
- `qdrant.py` — `QdrantRetriever`: `query_points` + payload filter по `segment`
- `chroma.py` — `ChromaRetriever`: обёртка над `rag/retriever.py`
- `factory.py` — `get_retriever(backend=...)` по `RETRIEVER_BACKEND`

### Обновлённые файлы

- `config.py` — `RETRIEVER_BACKEND` (default `qdrant`)
- `tools/search_knowledge_base.py` — через `BaseRetriever`, DI через `retriever=`; SDK не импортируется
- `server.py` — убран `ensure_index` при старте; сервер не трогает индекс
- `rag/retriever.py` — типы (`KnowledgeChunk`, `IndexNotReadyError`) перенесены в `retriever/base.py`
- `tests/conftest.py` + `tests/mocks.py` — `MockRetriever`, `mock_retriever` fixture
- `tests/test_retriever.py` — тесты фабрики (qdrant/chroma/unknown backend)
- `tests/test_rag.py` — tool-тест через mock retriever

### Исправления по итогам RAG review

Обнаружены и устранены три проблемы в `qdrant_indexer.py` (Task 03 scope, исправлено в Task 04):

| Проблема | Исправление |
|----------|-------------|
| Нет payload index для `segment` — full scan при каждом поиске | `create_payload_index("segment", KEYWORD)` в `_ensure_collection` |
| PDF чанкился через heading-split — режет текст в непредсказуемых местах | Отдельный путь в `_chunk_text`: PDF/TXT → только `_window_text` |
| Пустые строки из PDF-страниц → `No embedding data received` от OpenRouter | Фильтр `if c.text.strip()` после chunking |

Также добавлен `OPENAI_TIMEOUT_SECONDS` (default 120 с) в `config.py` и `embeddings.py` — для нестабильных сетевых условий.

## Принятые решения

| Решение | Причина |
|---------|---------|
| `Protocol` вместо ABC | Структурная типизация — не требует явного `extends`, проще мокировать |
| `lru_cache` на `_cached_retriever` | Один инстанс на процесс; сбрасывается в тестах через `cache_clear()` |
| `ChromaRetriever` оставлен | Нужен для Task 05 bench |
| `ensure_index` убран из `server.py` | Qdrant индексируется отдельно через `make index`; в stdio-сервере нет смысла трогать индекс |

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `QdrantClient.search` → `AttributeError` | Метод переименован в `query_points` в qdrant-client 1.14+ |
| mypy: `tests/conftest.py` найден дважды | Добавлен `tests/__init__.py` |
| `No embedding data received` при `make index` | Пустые PDF-чанки фильтруются до эмбеддинга |

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `BaseRetriever` определён; Qdrant/Chroma изолированы | ✅ |
| 2 | `RETRIEVER_BACKEND` переключает реализацию | ✅ |
| 3 | `search_knowledge_base` не импортирует SDK напрямую | ✅ |
| 4 | `make test-mcp` зелёный | ✅ 22 passed |
| 5 | `make test-backend` зелёный | ✅ 51 passed, 3 skipped |
| 6 | `make index` завершается без ошибок | ✅ |

## Что дальше

- Task 05: baseline-eval — прогнать bench по Qdrant/Chroma/pgvector
- v0.2 backlog: hybrid search (dense + BM25), структурный чанкинг PDF
