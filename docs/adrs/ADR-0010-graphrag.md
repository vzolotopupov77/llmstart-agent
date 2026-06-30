# ADR-0010 — Neo4j как графовая БД для GraphRAG-слоя

> **Статус:** ✅ Accepted  
> **Дата:** 2026-06-28  
> **Автор:** sprint-09 / agent  
> **Область:** RAG-слой, хранилища данных  
> **Supersedes:** —  
> **Связанные ADR:** [ADR-0009 — Qdrant](ADR-0009-vector-db.md)

---

## 1. Контекст

### 1.1 Текущая ситуация

Sprint-08 перевёл RAG на **Qdrant v1.18.2** (dense + sparse hybrid search). Хранилище хорошо покрывает **single-hop** запросы: поиск факта о конкретном курсе, FAQ.

Corpus analysis (Task 01, `analysis.md`) зафиксировал классы вопросов, которые flat vector RAG **не решает**:

| Класс | Пример | Почему Qdrant промахнётся |
|-------|--------|--------------------------|
| **multi-hop** | «Что нужно пройти перед deep-agents?» | Требует обхода RECOMMENDED_BEFORE × 3 прыжка; flat RAG вернёт описание курса без цепочки |
| **multi-hop** | «Какие темы охватывает комбо целиком?» | `Combo→INCLUDES→Course→COVERS→Theme` — 2 прыжка × 4 курса разбросаны по разным чанкам |
| **global** | «В каких курсах встречается тема MCP?» | MCP упоминается в трёх файлах; embedding-поиск вернёт топ-1/2, не полный список |
| **global** | «Какие курсы подходят для менеджеров без кода?» | Агрегат по TARGETS(Audience=non-dev); Qdrant не агрегирует граф аудиторий |

Baseline-прогон (Task 02) подтвердил просадку на multi-hop и global сегментах.

### 1.2 Требования sprint-09

- Граф каталога (курсы, комбо, темы, аудитории) строится рядом с Qdrant; вектор **не переносится** в Neo4j.
- Маршрутизация по типу вопроса: single-hop → Qdrant, multi-hop → граф, global → структурный агрегат.
- Версии образа и SDK фиксируются явно; `latest` запрещён.
- Entity resolution обязателен; deprecated `LLMGraphTransformer` не использовать.
- `text2cypher` за 4 guardrails.

---

## 2. Рассмотренные варианты

### Вариант A. Только Qdrant — metadata-фильтры

Суть: расширить payload (добавить список тем, аудиторий, prerequisite IDs в metadata каждого чанка) и фильтровать на стороне Qdrant.

**Плюсы:**
- Нет новой зависимости.
- Простота реализации.

**Минусы:**
- Обход произвольной глубины (`RECOMMENDED_BEFORE*`) невозможен — payload stateless.
- Пересечение множеств тем двух курсов требует клиентской логики; не масштабируется.
- Global-агрегаты (COUNT, SUM по каталогу) — на клиенте, хрупко.
- Дублирование структурных данных в чанки → нарушает DRY; изменение схемы требует полной переиндексации.

**Вердикт:** ❌ Отклонён — не решает структурные запросы глубиной > 1.

---

### Вариант B. Amazon Neptune / ArangoDB / TigerGraph

Суть: облачная или альтернативная графовая СУБД вместо Neo4j.

**Плюсы:**
- Neptune: managed, без ops.
- ArangoDB: multi-model (документы + граф).

**Минусы:**
- Neptune: нет Community-версии; нет self-host; стоимость в dev.
- ArangoDB / TigerGraph: другой query language (AQL / GSQL), нет зрелой интеграции с `neo4j-graphrag` Python SDK.
- Экосистема GraphRAG (neo4j-graphrag, langchain-neo4j, LLMGraphTransformer-replacement, Text2Cypher) ориентирована на Neo4j + Cypher.
- Sprint-ограничение: community summaries не делаем (оверкилл для малого каталога) → алгоритмическая мощь TigerGraph/Neptune не нужна.

**Вердикт:** ❌ Отклонён — нет self-host в dev, слабая интеграция с Python GraphRAG-экосистемой.

---

### Вариант C. Neo4j Community ← **принят**

Суть: Neo4j как выделенный контейнер рядом с Qdrant; Cypher для traversal; Python SDK `neo4j-graphrag`.

**Плюсы:**
- Нативный граф, Cypher — стандарт для структурных traversal-запросов.
- `neo4j-graphrag` (официальный Neo4j SDK): `VectorCypherRetriever`, `Text2CypherRetriever`, `SimpleKGPipeline` — все нужные паттерны из коробки.
- Community-версия: self-host без лицензии; аналогично тому, как Qdrant развёрнут в compose.
- `APOC`-плагин: `apoc.text.levenshteinSimilarity` для entity resolution в QA-запросах.
- `langchain-neo4j` как опциональный fallback для `GraphCypherQAChain` (text2cypher альтернатива).

**Минусы:**
- Новый сервис в compose (~512 MB RAM).
- Требует `make graph-index` при первом запуске (аналогично `make index` для Qdrant).
- APOC-плагин увеличивает размер образа.

**Вердикт:** ✅ Принят.

---

## 3. Решение

**Принимаем: вариант C — Neo4j Community в docker-compose рядом с Qdrant; основной Python SDK — `neo4j-graphrag`.**

### 3.1 Принципы

- Neo4j хранит **структуру и связи** каталога; Qdrant хранит **семантические chunks**; связь — по `id` (URL-slug).
- Версии образа и пакетов фиксируются; `latest` запрещён.
- Entity resolution выполняется до записи (`MERGE` по нормализованному `id`).
- `text2cypher` только через отдельные RO-credentials (`NEO4J_RO_*`) + 3 дополнительных guardrail.
- `LLMGraphTransformer` (langchain-experimental) не использовать — брать `SimpleKGPipeline` из `neo4j-graphrag`.

### 3.2 Зафиксированные версии

| Компонент | Версия | Источник / заметка |
|-----------|--------|--------------------|
| Docker-образ | `neo4j:2026.04.0-community` | [Docker Hub neo4j](https://hub.docker.com/_/neo4j/tags) — верифицирован в Task 04 |
| Python-драйвер | `neo4j==6.2.0` | [PyPI neo4j](https://pypi.org/project/neo4j/) — driver v6; `6.3.0` на PyPI отсутствует (2026-06-28) |
| `neo4j-graphrag` | `neo4j-graphrag==1.16.0` | [PyPI neo4j-graphrag](https://pypi.org/project/neo4j-graphrag/) |
| `langchain-neo4j` | `langchain-neo4j==0.4.0` | [PyPI langchain-neo4j](https://pypi.org/project/langchain-neo4j/) — опционально, для `GraphCypherQAChain` |

> **Правило pin:** при апгрейде образа Neo4j проверять совместимость `neo4j` (Python driver) через changelog; major-версия драйвера должна совпадать с major-версией сервера.

### 3.3 Схема LPG

Полная схема — в [`docs/sprints/sprint-09-graphrag/schema.md`](../sprints/sprint-09-graphrag/schema.md).

#### Узлы

| Метка | Ключ нормализации | Статус |
|-------|-------------------|--------|
| `Course` | `id` (URL-slug) | **Активен** |
| `Combo` | `id` | **Активен** |
| `Theme` | `id` (нормализованный slug) | **Активен** |
| `Audience` | `id` | **Активен** |
| `Format` | `id` | **Активен** |
| `Level` | `id` | **Активен** |
| `Module` | `id` (`{courseId}--module-{N}`) | **Деферред** — вводить при ≥ 10 курсах |

#### Рёбра с направлениями

```
(earlier:Course)-[:RECOMMENDED_BEFORE {mandatory, source}]->(later:Course)
(:Combo)-[:INCLUDES {stepOrder}]->(:Course)
(:Course)-[:HAS_MODULE]->(:Module)            -- деферред
(:Course)-[:COVERS {depth}]->(:Theme)
(:Theme)-[:REQUIRES]->(:Theme)               -- prereq_theme
(:Course)-[:TARGETS]->(:Audience)
(:Course)-[:AVAILABLE_AS]->(:Format)
(:Course)-[:AT_LEVEL]->(:Level)
```

### 3.4 Конвенции именования

| Элемент | Конвенция | Пример |
|---------|-----------|--------|
| Метки узлов | `PascalCase`, ед. число | `Course`, `Theme`, `Audience` |
| Типы рёбер | `SCREAMING_SNAKE_CASE`, глагольная фраза | `RECOMMENDED_BEFORE`, `COVERS`, `TARGETS` |
| Свойства | `camelCase` | `priceRub`, `stepOrder`, `discountPct` |
| Ключи нормализации | `id` (URL-slug) | `"vibe-coding"`, `"rag-basic"` |
| Имена constraints | `snake_case`, описательные | `course_id_unique`, `theme_id_unique` |

> **id vs slug:** `id` — каноничный URL-slug (как в `llmstart.ru/vibe-coding/`), не database-internal `elementId(n)`. Ключ синхронизации с Qdrant payload.

### 3.5 Маршрутизация по классу вопросов

| Класс | Retriever | Инструмент агента |
|-------|-----------|-------------------|
| **single-hop** | `QdrantRetriever` | `vector_search` |
| **multi-hop** | `VectorCypherRetriever` (якорь в Qdrant → Cypher-обход) | `graph_search` |
| **global** | Прямой Cypher-агрегат (без vector) | `global_catalog` |
| **text2cypher** | `Text2CypherRetriever` (RO-credentials `NEO4J_RO_*`) | `text2cypher_tool` |

> **Правило:** single-hop граф не использует — это защищает от регрессии метрики.

### 3.6 Boundary rule (граф vs Qdrant)

| Данные | Хранилище |
|--------|-----------|
| Структурные связи (RECOMMENDED_BEFORE, INCLUDES, COVERS, REQUIRES, TARGETS) | **Neo4j** |
| Метаданные для фильтрации (priceRub, level, format, segment) | **Neo4j** (свойства узлов) |
| Полные описания программ, тексты модулей, FAQ | **Qdrant** (chunks) |
| Лиды, транзакции, персональные данные | `data/leads.txt` — **вне обоих хранилищ** |

**Связь:** `Neo4j Course.id == Qdrant payload["course_id"]`.

### 3.7 Локальная инфраструктура (Task 04)

| Аспект | Решение |
|--------|---------|
| Compose-сервис | `neo4j` в `devops/docker-compose.yml`, сеть `langfuse_net` |
| Порты (host) | `127.0.0.1:7474` (Browser/HTTP), `127.0.0.1:7687` (Bolt) |
| Persistence | Named volumes `neo4j_data`, `neo4j_logs` |
| Плагины | `NEO4J_PLUGINS=["apoc"]` |
| Env (приложение) | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_RO_USER`, `NEO4J_RO_PASSWORD` — см. `.env.example` |
| Make-цели | `graph-up`, `graph-down`, `graph-status`, `graph-shell`, `graph-init-ro` |
| Smoke-проверка | `make graph-status` → `driver.verify_connectivity()` → `Connection OK` |
| Healthcheck контейнера | `cypher-shell … "RETURN 1 AS ok"` через Bolt — DB реально доступна |

> **Healthcheck:** HTTP `GET /db/neo4j/available` на Neo4j **2026.04** возвращает **404** (даже с Basic auth). Используем Bolt + `cypher-shell`, не HTTP-endpoint.

> **Клиент:** Bolt URI `bolt://localhost:7687` (не gRPC).

---

## 4. Последствия

### 4.1 Позитивные

- Multi-hop вопросы разрешаются через Cypher traversal — ожидаемый рост метрики на сегменте.
- Global-агрегаты через структурный Cypher без community summaries.
- Entity resolution на уровне MERGE → нет дублей в графе.
- `text2cypher` за 4 guardrails — безопасен для read-only операций.
- Retriever-ветки управляются конфигом (`RETRIEVER_BRANCH`), без правки бизнес-логики.

### 4.2 Негативные и митигация

| Риск | Митигация |
|------|-----------|
| Новый сервис в compose (~512 MB RAM, порты 7474/7687) | Документировать в `devops/README.md`; за счёт удаления `ChromaRetriever` net-change ≈ +1 сервис |
| Пустой граф при первом `make up` | `IndexNotReadyError` + сообщение «run make graph-index» |
| APOC-плагин увеличивает образ | Принять — нужен для entity resolution QA-запросов |
| Version skew драйвер vs сервер | Pin обеих версий; проверять changelog при апгрейде; при появлении `neo4j==6.3.0` на PyPI — сверить с changelog |
| RBAC `reader` недоступен на Community | `text2cypher_ro` — отдельный пользователь; guardrails 2–4 (regex, LIMIT, tool scope) обязательны на Python-слое |
| Регрессия single-hop при включении графа | Граф не включается для single-hop (routing rule в системном промпте) |

### 4.3 Нейтральные

- Qdrant и embeddings-провайдер не меняются.
- Langfuse-трейсинг работает через существующий контур (новые инструменты регистрируются аналогично).
- Eval-контур (`evals/`) расширяется датасетами multi-hop/global без изменения самого контура.

---

## 5. Guardrails для text2cypher

Все 4 обязательны — ни один нельзя пропустить:

1. **Read-only credentials в БД** — пользователь `text2cypher_ro` создаётся в Task 04 (`make graph-init-ro`); text2cypher подключается под `NEO4J_RO_*`, не под admin. На **Community Edition** `GRANT ROLE reader` недоступен (Enterprise-only) — отдельные creds + guardrails 2–4.
2. **Regex-фильтр на write-операции** — блокировать `CREATE`, `MERGE`, `DELETE`, `SET`, `REMOVE` до отправки в Neo4j (Python-слой).
3. **Таймаут и LIMIT** — добавлять `LIMIT 25` если не задан; таймаут запроса ≤ 5 с.
4. **Узкое описание инструмента** — агент вызывает `text2cypher_tool` только на агрегатные/структурные вопросы, не на semantic.

---

## 6. План внедрения

- [x] ADR-0010 принят (этот документ)
- [x] Task 04: Neo4j в `devops/docker-compose.yml`, `.env.example`, make `graph-*`, smoke, RO-user `text2cypher_ro`
- [ ] Task 05: `scripts/seed.cypher` + `scripts/graph_indexer.py` + entity resolution
- [ ] Task 06: `GraphRetriever`, `GlobalRetriever`, `VectorCypherRetriever`, мультиязычный реранкер
- [ ] Task 07: `Text2CypherTool` + 4 guardrails + тесты
- [ ] Task 08: routing-правила в системном промпте + финальный eval

---

## 7. Открытые вопросы

| Вопрос | Когда решать |
|--------|-------------|
| `aidd-program.md` — дубль fullstack или отдельная версия? | Task 05 — зафиксировать в summary |
| `Format` и `Level` как узлы vs свойства | Task 06 — если traversal не нужен, вернуть как свойства |
| gRPC vs Bolt для Python-клиента | ✅ Task 04 — Bolt (`bolt://localhost:7687`) |
| Мультиязычный реранкер: `cross-encoder/msmarco-MiniLM-L-12-v3` vs аналог | Task 06 — проверить поддержку русского языка |

---

## 8. Ссылки

- [Sprint 09 README](../sprints/sprint-09-graphrag/README.md)
- [LPG-схема](../sprints/sprint-09-graphrag/schema.md)
- [ADR-0009 — Qdrant](ADR-0009-vector-db.md)
- [neo4j-graphrag PyPI](https://pypi.org/project/neo4j-graphrag/)
- [Neo4j Docker Hub](https://hub.docker.com/_/neo4j/tags)
- [neo4j Python driver PyPI](https://pypi.org/project/neo4j/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)

---

## 9. История изменений

| Дата | Изменение | Автор |
|------|-----------|-------|
| 2026-06-28 | Первая версия, статус Accepted | sprint-09 / Task 03 |
| 2026-06-28 | Task 04: driver `6.2.0`, healthcheck Bolt+cypher-shell, Community RBAC, §3.7 infra | sprint-09 / Task 04 |
