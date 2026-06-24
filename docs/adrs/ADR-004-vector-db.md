# ADR-004 — Vector DB для RAG-слоя

> **Статус:** ✅ Accepted  
> **Дата:** 2026-06-22  
> **Автор:** sprint-08 / agent  
> **Область:** продукт llmstart-agent  
> **Supersedes:** —

---

## 1. Контекст

### 1.1 Текущая ситуация

RAG-слой реализован в `mcp_server` на **embedded ChromaDB 1.5.9** (`chromadb.PersistentClient`):

- Индекс хранится в `DATA_DIR/.chroma`
- Коллекция `knowledge_base`, cosine HNSW
- Источники: `data/b2b/*.md`, `data/b2c/*.md`
- Поиск: `collection.query(..., where={"segment": segment})` в `mcp_server/rag/retriever.py`
- Индексация: `make reindex` → `mcp_server/rag/indexer.py`

Отдельного Chroma-сервиса в `devops/docker-compose.yml` нет — только файловый embedded-клиент.

### 1.2 Что породило необходимость решения

Sprint-08 требует:

1. **Параметрический retriever** — переключение между бэкендами через конфиг без правки бизнес-логики
2. **Benchmark** — сравнимые прогоны `make bench` по Qdrant, ChromaDB, pgvector
3. **Production-паттерны** — health check, named volume, явные версии образа и SDK

Embedded ChromaDB не удовлетворяет этим требованиям:

- Нет REST/gRPC API — нельзя поднять как отдельный сервис в compose
- Multi-process unsafe — backend и mcp_server могут обращаться к одному индексу из разных процессов
- Нет health check и named volume из коробки
- Фильтрация `segment` работает как client-side post-filter, а не server-side payload filter

### 1.3 Силы, действующие на решение

| Сила | Вес | Следствие |
|------|-----|-----------|
| Фильтрация по сегменту B2B/B2C | Высокий | Нужен native payload/metadata filter на стороне сервера |
| Параметрический bench (3 бэкенда) | Высокий | Единый retriever-интерфейс + конфиг per-backend |
| Docker self-host в dev | Высокий | Один контейнер, health check, named volume |
| Явные версии (не `latest`) | Средний | Pin образа и SDK; проверка совместимости API |
| Минимальная сложность инфраструктуры | Средний | Не добавлять PG только ради векторов, если есть purpose-built альтернатива |

---

## 2. Рассмотренные варианты

### Сравнительная таблица

| Критерий | ChromaDB 1.5.9 | pgvector 0.8.x | Qdrant v1.18.2 |
|----------|---------------|----------------|----------------|
| Режим развёртывания | embedded / server (отдельный compose) | PostgreSQL extension | одиночный контейнер |
| Native metadata filter | client-side post-filter | SQL `WHERE` | payload filter (server-side) |
| Python SDK | `chromadb` 1.5.9 | `asyncpg` + raw SQL | `qdrant-client` 1.18.0 |
| gRPC | нет | нет | да (порт 6334) |
| REST API | да (server mode) | через PG | да (порт 6333) |
| Health check | нет в embedded | через PG | `/healthz` |
| Named volume | файловая система | PG data dir | `/qdrant/storage` |
| Multi-process safe | нет (embedded) | да | да |
| Лицензия | Apache 2.0 | PostgreSQL | Apache 2.0 |
| Production-готовность (dev scope) | низкая (embedded) | высокая | высокая |

### Вариант A. ChromaDB (текущий)

Суть: оставить embedded ChromaDB или перейти на Chroma server mode.

**Плюсы:**
- Уже интегрирован в кодовую базу
- Минимальные изменения при сохранении embedded-режима

**Минусы:**
- Embedded не поддерживает multi-process доступ
- Server mode добавляет отдельный compose-сервис без явного преимущества над Qdrant
- Фильтрация `segment` — post-filter, не server-side
- Нет gRPC; менее зрелый bench-контур для сравнения с pgvector

**Вердикт:** ❌ Отклонён — embedded не масштабируется; server mode не даёт преимуществ перед Qdrant при большей сложности bench.

### Вариант B. pgvector

Суть: расширение PostgreSQL для хранения и поиска векторов.

**Плюсы:**
- Единая СУБД с будущим persistence (v1.0)
- Зрелая экосистема, SQL-фильтрация

**Минусы:**
- Не purpose-built vector DB — нужны raw SQL / ORM-обёртки для vector ops
- Требует отдельный PG-инстанс или extension в существующем Postgres
- Сложнее реализовать единообразный retriever-интерфейс без дублирования логики
- Overkill для текущего scope (4 markdown-файла, ~20 чанков)

**Вердикт:** ❌ Отклонён — избыточная инфраструктура для sprint-08; рассмотреть повторно при v1.0 persistence.

### Вариант C. Qdrant

Суть: purpose-built vector DB, self-hosted через Docker, Python SDK `qdrant-client`.

**Плюсы:**
- Один контейнер, health check, named volume
- Server-side payload filter по `segment`
- REST + gRPC API; зрелый Python SDK
- Хорошо документирован для bench-сценариев
- Совместим с параметрическим retriever через env-конфиг

**Минусы:**
- Новая зависимость в compose
- Требует `make index` при первом запуске
- SDK 1.18.0 vs server 1.18.2 — minor version skew (см. совместимость ниже)

**Вердикт:** ✅ Принят.

---

## 3. Решение

**Принимаем: вариант C — Qdrant v1.18.2.**

### 3.1 Принципы

- Конкретная БД выбирается через `RETRIEVER_BACKEND` в `.env`, не хардкодом
- Версии образа и SDK фиксируются явно; `latest` запрещён
- Фильтрация `segment=b2b|b2c` — server-side payload filter
- Индексация идемпотентна: upsert по детерминированному `id`

### 3.2 Зафиксированные версии

| Компонент | Версия | Источник |
|-----------|--------|----------|
| Docker-образ | `qdrant/qdrant:v1.18.2` | [Docker Hub](https://hub.docker.com/r/qdrant/qdrant/tags) |
| Python SDK | `qdrant-client==1.18.0` | [PyPI](https://pypi.org/project/qdrant-client/) |

#### Проверка совместимости API

| Проверка | Результат |
|----------|-----------|
| SDK 1.18.0 ↔ server 1.18.2 | ✅ Совместимы — 1.18.2 patch-релиз, REST/gRPC контракт не меняется |
| Мажорная версия SDK = мажорная версия server | ✅ 1.x = 1.x |
| Breaking changes между 1.18.0 и 1.18.2 | ❌ Нет (changelog: bugfixes, perf) |
| Python >= 3.10 (SDK requirement) | ✅ Проект на Python 3.12+ |

**Правило pin:** при апгрейде server — проверять [qdrant-client releases](https://github.com/qdrant/qdrant-client/releases) на совместимость; minor SDK может опережать patch server на 1–2 версии без breaking changes.

### 3.3 Детали реализации

**Compose-сервис** (Task 02):

```yaml
qdrant:
  image: qdrant/qdrant:v1.18.2
  ports:
    - "6333:6333"   # REST
    - "6334:6334"   # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
    interval: 10s
    timeout: 5s
    retries: 3
```

**Коллекция:**

- Имя: `knowledge_base`
- Distance: `Cosine`
- Vector size: определяется моделью `EMBEDDING_MODEL` (1536 для `text-embedding-3-small`)

**Payload schema:**

```json
{
  "source": "b2c/faq-b2c.md",
  "segment": "b2c"
}
```

**Фильтрация по сегменту:**

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

client.search(
    collection_name="knowledge_base",
    query_vector=embedding,
    query_filter=Filter(
        must=[FieldCondition(key="segment", match=MatchValue(value=segment))]
    ),
    limit=top_k,
)
```

**Env-переменные** (`.env.example`, Task 02):

```bash
RETRIEVER_BACKEND=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=knowledge_base
```

**Retriever-интерфейс** (Task 04):

```
mcp_server/retriever/
├── base.py       # BaseRetriever (Protocol/ABC)
├── qdrant.py     # QdrantRetriever
├── chroma.py     # ChromaRetriever (для bench)
├── pgvector.py   # PgVectorRetriever (для bench, stub)
└── factory.py    # create_retriever(RETRIEVER_BACKEND)
```

### 3.4 Что изменится в процессах

| Было | Станет |
|------|--------|
| `make reindex` → embedded Chroma | `make index` → upsert в Qdrant |
| `DATA_DIR/.chroma` | `qdrant_data` named volume |
| Прямой import `chromadb` в retriever | `BaseRetriever` + factory |
| Нет health check | `curl /healthz` в compose |

---

## 4. Последствия

### 4.1 Позитивные

- Server-side фильтрация `segment` — меньше лишних результатов, предсказуемый bench
- Multi-process safe: backend и mcp_server обращаются к одному Qdrant через REST
- Health check и named volume — production-паттерны в dev-стеке
- Параметрический bench: `make bench` / `make bench RETRIEVER_BACKEND=qdrant`
- Явные версии — воспроизводимые прогоны

### 4.2 Негативные (и митигация)

| Риск | Митигация |
|------|----------|
| Новый сервис в compose (+ RAM, + порт) | Qdrant лёгкий (~256 MB); документировать в `devops/README.md` |
| Пустой индекс при первом запуске | `IndexNotReadyError` + сообщение «run make index» |
| Version skew SDK vs server | Pin обеих версий; проверять changelog при апгрейде |
| ChromaDB удаляется из prod-path | Оставить `ChromaRetriever` только для bench-сравнения |

### 4.3 Нейтральные

- Embeddings-провайдер (`EMBEDDING_MODEL`) не меняется
- Формат chunk metadata (`source`, `segment`) сохраняется
- Eval-датасет и метрики bench не зависят от выбора БД

---

## 5. План внедрения

- [x] ADR-004 принят (этот документ)
- [ ] Task 02: Qdrant в `devops/docker-compose.yml`, `.env.example`
- [ ] Task 03: `scripts/index.py` + `make index`
- [ ] Task 04: `BaseRetriever` + `QdrantRetriever` + factory
- [ ] Task 05: `make bench` + `evals/reports/vector-bench-{timestamp}.md`

---

## 6. Открытые вопросы

| Вопрос | Когда решать |
|--------|-------------|
| gRPC vs REST для Python-клиента | Task 04 — REST по умолчанию (проще debug) |
| pgvector retriever: stub или полная реализация | Task 05 — stub достаточен для bench-конфига |
| Миграция существующего `.chroma` индекса | Не требуется — полный reindex через `make index` |

---

## 7. Ссылки

- [Sprint 08 README](../sprints/sprint-08-vector-db/README.md)
- [Qdrant Installation](https://qdrant.tech/documentation/installation/)
- [qdrant-client PyPI](https://pypi.org/project/qdrant-client/)
- [Qdrant Filtering](https://qdrant.tech/documentation/concepts/filtering/)
- Текущий retriever: `mcp_server/mcp_server/rag/retriever.py`

---

## 8. История изменений

| Дата | Изменение | Автор |
|------|-----------|-------|
| 2026-06-22 | Первая версия, статус Accepted | sprint-08 |
