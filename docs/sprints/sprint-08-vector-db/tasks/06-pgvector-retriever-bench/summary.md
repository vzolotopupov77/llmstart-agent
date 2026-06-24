# Summary: Task 06 — pgvector-retriever-bench

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-24

---

## Что реализовано

- `evals/scripts/judge_client.py` — `SyncOpenRouterJudge` + обновлённый `create_judge_model()`; убран `asyncio.run()` в eval-контуре
- `evals/tests/test_evaluators.py` — 2 новых теста: `test_create_judge_model_returns_sync_judge`, `test_sync_judge_uses_sync_client`
- `devops/docker-compose.yml` — сервис `pgvector` (`pgvector/pgvector:pg17`, порт 5434, health check)
- `.env.example` — `PGVECTOR_HOST/PORT/DB/USER/PASSWORD/TABLE`
- `mcp_server/mcp_server/retriever/pgvector.py` — `PgvectorRetriever`: persistent connection, `connect_timeout=10`, readiness-cache
- `mcp_server/mcp_server/rag/pgvector_indexer.py` — индексатор pgvector; `_ensure_extension` перед `register_vector`
- `mcp_server/mcp_server/retriever/factory.py` — регистрация `"pgvector"`
- `mcp_server/mcp_server/retriever/qdrant.py` — добавлен `prefer_grpc=True`; docstring в `__init__`
- `mcp_server/mcp_server/rag/embeddings.py` — outer retry (3×) с пересозданием httpx-клиента при `APIConnectionError`; `max_retries=3`
- `mcp_server/mcp_server/retriever/chroma.py` — docstring в `__init__`
- `mcp_server/scripts/bench.py` — bench-раннер: `_CachingEmbeddings`, latency loop, precision/recall, JSON-отчёт
- `mcp_server/scripts/bench_all.py` — оркестратор всех трёх бэкендов + вызов `build_summary`
- `mcp_server/scripts/bench_report.py` — агрегатор JSON → markdown-таблица
- `mcp_server/tests/test_retriever.py` — тесты для всех трёх retriever-реализаций
- `evals/configs/vector-db-qdrant.yaml`, `vector-db-chroma.yaml`, `vector-db-pgvector.yaml`
- `evals/reports/vector-bench-20260624T152928Z.md` — финальный сводный отчёт

---

## Отклонения от плана

| Отклонение | Причина |
|------------|---------|
| Bench-скрипты в `mcp_server/scripts/`, а не `evals/scripts/` | Скрипты используют `mcp_server` как библиотеку; размещение рядом упрощает импорты |
| `bench_all.py` вместо shell-цикла в Makefile | Windows PowerShell не поддерживает `for backend in ...` в Makefile |
| `prefer_grpc=True` в `QdrantRetriever` | Обнаружено в ходе bench: sync REST-клиент на Windows вызывает `asyncio.run()` на каждый запрос (~600 мс накладных расходов) |
| Outer retry в `OpenRouterEmbeddings` | OpenRouter периодически рвёт SSL-соединение; встроенных 2-3 retry недостаточно, нужен пересозданный httpx-клиент |
| `connect_timeout=10` + persistent connection в `PgvectorRetriever` | Без таймаута `psycopg.connect()` висел вечно при сетевых проблемах; 72 открытия соединений за latency loop замедляли bench |
| `index_rss_mb` = 0.0 / n/a | `resource.getrusage()` недоступен на Windows; метрика не собрана |

---

## Принятые решения

| Решение | Причина | ADR |
|---------|---------|-----|
| `prefer_grpc=True` в `QdrantRetriever` | Устраняет Windows/asyncio overhead (~2000 мс → ~2.5 мс p50) | — |
| Persistent connection в `PgvectorRetriever` | Один коннект на весь bench run вместо 72; + `connect_timeout` против зависания | — |
| `_CachingEmbeddings` wrapper в bench | Исключает дублирование вызовов к OpenRouter при latency loop (12 queries × 5 runs → 12 уникальных запросов всего) | — |
| Outer retry с пересозданием клиента | OpenRouter SSL drops не восстанавливаются через httpx connection pool; нужен новый `OpenAI(...)` | — |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `psycopg.ProgrammingError: vector type not found` | `CREATE EXTENSION IF NOT EXISTS vector` вызывается до `register_vector(conn)` |
| Qdrant bench p50 = 2050 мс | Перешли на gRPC (`prefer_grpc=True`); gRPC-клиент не использует Python `asyncio.run()` |
| `httpx.ConnectError: SSL UNEXPECTED_EOF` при индексации | Outer retry: при `APIConnectionError` — пауза 5 с, пересоздание `OpenAI` клиента; до 3 попыток |
| `PgvectorRetriever` зависал на latency loop | Добавлен `connect_timeout=10`; коннект переиспользуется через `_get_conn()` |
| Windows Makefile `for` loop не работает | Логика переноса в `bench_all.py`; Makefile вызывает Python-скрипт |
| `pgvector` не может переиндексироваться из-за SSL drops | `BENCH_SKIP_INDEX=1` пропускает повторную индексацию; уже проиндексированные данные сохраняются (`INSERT ON CONFLICT DO UPDATE`) |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `SyncOpenRouterJudge` из `create_judge_model()`; нет `Event loop is closed` | ✅ |
| 2 | `PgvectorRetriever` реализован; `RETRIEVER_BACKEND=pgvector` без правки логики; тесты зелёные | ✅ |
| 3 | `make up` поднимает pgvector; health check зелёный | ✅ |
| 4 | `vector-db-chroma.yaml` и `vector-db-pgvector.yaml` существуют | ✅ |
| 5 | `make bench` без ошибок; JSON-отчёты для 3 бэкендов | ✅ |
| 6 | `vector-bench-20260624T152928Z.md` — 6 метрик по 3 бэкендам | ✅ |
| 7 | `make lint` зелёный | ✅ |
| 8 | `make test-backend` зелёный | ✅ |

---

## Пост-закрытие: фиксы сегментации и унификации корпуса

После закрытия Task 06 обнаружены и устранены два системных дефекта:

### Дефект 1: неправильный segment для `real_data/` (qdrant_indexer.py)

**Проблема.** `_scan_files` присваивал `segment = relative.parts[0]` — т. е. для `data/real_data/b2b/*.pdf` сегмент был `real_data`, а не `b2b`. Retriever при поиске фильтрует только `b2b`/`b2c`, поэтому 20 файлов (13 PDF + 6 md) были проиндексированы, но **недоступны** при retrieval.

**Исправление.** `_scan_files` переписан:
- `_resolve_segment(relative)` — ищет `b2b`/`b2c` на любом уровне пути
- `_is_service_file(relative)` — исключает `leads.txt`, `payments.json`, `b2c/catalog.json`
- файлы без `b2b`/`b2c` в пути (орфаны) пропускаются

Результат: скан `data/` теперь возвращает **24 файла** с правильными сегментами вместо `{b2b:2, b2c:2, real_data:20, default:1}`.

Новые тесты: `mcp_server/tests/test_qdrant_indexer.py` (2 кейса).

### Дефект 2: Chroma indexer использовал другой корпус

**Проблема.** `indexer.py` (`reindex`) сканировал только `b2b_dir()/*.md` и `b2c_dir()/*.md` — 4 файла, 23 чанка. Qdrant/pgvector через `_scan_files` индексировали весь `data/` (204 чанка). Bench строил запросы через `_scan_files`, поэтому на прогоне `170933Z` Chroma показал recall **0.25** (искал по запросам из файлов, которых не индексировал).

**Исправление.** `indexer.py`:
- `_scan_markdown_files()` → `_knowledge_files()` на базе `_scan_files(data_dir())`
- `_collect_chunks` использует `_read_text` + `_chunk_text` — поддержка md/txt/pdf
- чанки без текста отфильтровываются

Результат: Chroma теперь индексирует **202 чанка** (тот же корпус, что Qdrant/pgvector).

### Финальный bench после фиксов: `172450Z`

| Backend | indexed_chunks | p50_latency_ms | precision@k | recall@k |
|---------|----------------|----------------|-------------|----------|
| qdrant | 202 | 3.33 | 0.2448 | 0.9792 |
| chroma | **202** | 4.89 | **0.2448** | **0.9792** |
| pgvector | 202 | 4.29 | 0.2448 | 0.9792 |

Все три бэкенда на едином корпусе, метрики retrieval совпали. Расхождение с прогоном `152928Z` (recall 1.0 → 0.9792) — корпус вырос с 4 md до 24 файлов, bench стал строже.

## Что дальше

- `index_rss_mb` на Windows: заменить `resource.getrusage()` на `psutil` в будущем

---

## Ссылки

- [vector-bench-20260624T172450Z.md](../../../../evals/reports/vector-bench-20260624T172450Z.md) ← финальный (пост-фикс)
- [vector-bench-20260624T152928Z.md](../../../../evals/reports/vector-bench-20260624T152928Z.md) ← до фиксов
- [ADR-004-vector-db.md](../../../../docs/adrs/ADR-004-vector-db.md)
- [Sprint 08 README](../../README.md)
