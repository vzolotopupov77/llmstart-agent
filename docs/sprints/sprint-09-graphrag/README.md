# Sprint 09: graphrag

> **Версия roadmap:** v0.2  
> **Roadmap:** [../../roadmap.md](../../roadmap.md)  
> **Статус:** ✅ Done  
> **Открыт:** 2026-06-26  
> **Закрыт:** 2026-06-30

---

## Цель спринта

Добавить графовую ногу к существующему Qdrant-hybrid RAG: построить граф знаний каталога курсов в Neo4j, реализовать маршрутизацию по типу вопроса (single-hop → вектор, multi-hop/зависимости → граф, обзор каталога → global aggregation, точные структурные запросы → text2cypher) и подтвердить рост метрик на multi-hop/global-сегментах без регрессии single-hop.

---

## Ограничения

- Вектор остаётся в Qdrant (dense+sparse уже настроены); граф ставим рядом, связь по `id`; вектор в Neo4j не переносим.
- Retriever-интерфейс абстрактный: ветка (`vector` / `graph` / `global` / `hybrid` / `text2cypher`) задаётся конфигом (env или eval-config), архитектура позволяет менять без правки бизнес-логики.
- Версии фиксировать явно (образ Neo4j, `neo4j-graphrag` и/или `langchain-neo4j`).
- Граф включается по классу вопроса; регрессия single-hop запрещена; качество измеряется строго по сегментам (single / multi / global), не средним по всему набору.
- Entity resolution обязателен; авто-извлечение — только строго по схеме; deprecated `LLMGraphTransformer` (`langchain-experimental`) не использовать — брать `neo4j-graphrag SimpleKGPipeline` или `LlamaIndex SchemaLLMPathExtractor`.
- `text2cypher` только за 4 guardrails: read-only роль в БД, regex-фильтр на write-операции, таймауты и `LIMIT`, узкое описание инструмента.
- Реранкер — мультиязычный (контент на русском).
- Community summaries (Leiden) не делаем — на малом каталоге оверкилл; global-ветка через структурный агрегат.
- Перед каждой задачей проверять `.agents/skills/`; для генерации и ревью Cypher подключать `neo4j-cypher-skill`.
- Не затрагивать темы будущих спринтов (мультимодальный RAG, context-engineering и далее).

---



## DoD спринта


| #   | Критерий                                                                             | Способ проверки                                                                  | Результат |
| --- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | --------- |
| 1   | Граф каталога построен и виден в Neo4j Browser (ручной seed + авто-темы, без дублей) | `make graph-index` → Neo4j Browser → `MATCH (n) RETURN count(n)`                 | ✅ Task 05 |
| 2   | Метрика на multi-hop и global выросла относительно baseline                          | Сравнение отчётов по сегментам из Task 06–08                                     | ✅ Task 08: multi-hop **0.525** / **0.542** (v5) · global **0.517** / **0.433** (v5) vs baseline 0.383 / 0.200 |
| 3   | Single-hop не регрессировал                                                          | `answer_correctness[single-hop]` >= baseline − 0.02 (≥ 0.642)                    | ✅ Task 08 fix-loop: **0.665** (prompt v5) |
| 4   | Ветки retrieval переключаются конфигом, без хардкода БД                              | Смена `RETRIEVER_BRANCH` в `.env` → разная ветка без правки кода                 | ✅ Task 06 |
| 5   | `text2cypher` за 4 guardrails; write-запрос блокируется                              | `make test-mcp` → `test_text2cypher_blocks_write` зелёный                        | ✅ Task 07 |
| 6   | Агент маршрутизирует по типу вопроса                                                 | Трейсы в Langfuse: multi-hop → graph-tool, обзор → global-tool                   | ✅ Task 08 (user-check) |
| 7   | Entity resolution выполнен; нестыковки данных задокументированы                      | `graph-qa.cypher` без орфанов и дублей; `entity-resolution.md`                   | ✅ Task 05 |
| 8   | Версии Neo4j и SDK зафиксированы; ADR на месте                                       | `docs/adrs/ADR-0010-graphrag.md` существует, версии не `latest`                  | ✅ ADR-0010 Accepted |


---



## Задачи


| #   | Задача                                          | Статус | Plan                                       | Summary                                          |
| --- | ----------------------------------------------- | ------ | ------------------------------------------ | ------------------------------------------------ |
| 01  | [corpus-analysis](#task-01-corpus-analysis)     | ✅ Done | [plan](tasks/01-corpus-analysis/plan.md)   | [summary](tasks/01-corpus-analysis/summary.md)   |
| 02  | [datasets-baseline](#task-02-datasets-baseline) | ✅ Done | [plan](tasks/02-datasets-baseline/plan.md) | [summary](tasks/02-datasets-baseline/summary.md) |
| 03  | [graph-schema-adr](#task-03-graph-schema-adr)   | ✅ Done | [plan](tasks/03-graph-schema-adr/plan.md)  | [summary](tasks/03-graph-schema-adr/summary.md)  |
| 04  | [neo4j-infra](#task-04-neo4j-infra)             | ✅ Done | [plan](tasks/04-neo4j-infra/plan.md)       | [summary](tasks/04-neo4j-infra/summary.md)       |
| 05  | [graph-indexing](#task-05-graph-indexing)       | ✅ Done | [plan](tasks/05-graph-indexing/plan.md)    | [summary](tasks/05-graph-indexing/summary.md)    |
| 06  | [graph-retrieval](#task-06-graph-retrieval)     | ✅ Done | [plan](tasks/06-graph-retrieval/plan.md)   | [summary](tasks/06-graph-retrieval/summary.md)   |
| 07  | [text2cypher](#task-07-text2cypher)             | ✅ Done | [plan](tasks/07-text2cypher/plan.md)       | [summary](tasks/07-text2cypher/summary.md)       |
| 08  | [agent-routing](#task-08-agent-routing)         | ✅ Done | [plan](tasks/08-agent-routing/plan.md)     | [summary](tasks/08-agent-routing/summary.md)     |


---



## Task 01: corpus-analysis

**Статус:** ✅ Done

**Цель:** прогнать агента-аналитика по каталогу `data/` и получить `analysis.md` с инвентаризацией сущностей, типологией вопросов и черновиком графовой схемы.

> 📌 **Перед началом:** проверить `.agents/skills/` — прочитать `neo4j-modeling-skill` (схема нод и рёбер) и `neo4j-getting-started-skill` (контекст домена).

**Состав работ:**

- [ ] Прочитать все файлы в `data/` (md, txt, json); составить инвентаризацию: список сущностей (курсы, комбо, модули, темы, аудитории, уровни, форматы) с примерами из текста.
- [ ] Выявить явные связи: порядок ступеней (prerequisite-цепочка), вхождение тем в курсы, состав комбо из курсов.
- [ ] Выявить неявные связи: концептуальные зависимости тем (тема A нужна для понимания темы B), пересечение аудиторий.
- [ ] Составить список вопросов, которые плохо покрываются flat RAG: **минимум 6 multi-hop** и **4 global** с обоснованием «почему Qdrant-hybrid промахнётся» (что именно пропустит или смешает).
- [ ] Зафиксировать таксономию из трёх классов с примерами вопросов:
  - **single-hop** — факт о конкретном курсе/теме
  - **multi-hop** — путь через 2+ узла (prerequisite-цепочки, «что нужно пройти перед X»)
  - **global** — агрегат по каталогу («сколько курсов про NLP», «какие курсы есть для менеджеров»)
- [ ] Зафиксировать кандидатов на entity resolution: алиасы одной темы, дубль программы Fullstack в двух файлах, расхождение суммы цен комбо.
- [ ] Черновик графовой схемы (узлы и рёбра) — достаточно текстового описания; детализация — в Task 03.
- [ ] Сохранить `docs/sprints/sprint-09-graphrag/analysis.md`.

**Критерии готовности:**

*Агент проверяет:*

- [ ] `analysis.md` содержит разделы: Инвентаризация, Явные связи, Неявные связи, Таксономия вопросов, Кандидаты entity resolution, Нестыковки данных, Черновик схемы.
- [ ] Список «плохо покрываемых» вопросов: ≥ 6 multi-hop + ≥ 4 global, каждый с обоснованием.
- [ ] Все нестыковки данных явно выделены (дубль Fullstack, расхождение цены комбо).

*Пользователь проверяет:*

- [ ] Таксономия и примеры вопросов понятны и соответствуют реальному каталогу.
- [ ] Нестыковки в данных корректно идентифицированы.

**Артефакты:**

- `[docs/sprints/sprint-09-graphrag/analysis.md](analysis.md)` — инвентаризация сущностей, связи, таксономия вопросов (multi-hop / global / single-hop), черновик схемы, entity resolution и нестыковки данных

---



## Task 02: datasets-baseline

**Цель:** синтезировать сегментные мини-датасеты (multi-hop, global) и прогнать текущий Qdrant-hybrid как baseline для последующего сравнения.

> 📌 **Перед началом:** прочитать `.methodology/eval/eval-methodology.md` и [docs/eval/README.md](../../eval/README.md); проверить `.agents/skills/`.

**Состав работ:**

- [ ] Синтезировать **multi-hop датасет**: 10–12 вопросов с эталонными ответами и списком `required_entities` (конкретные курсы/темы, обязательные в ответе). Охват: prerequisite-цепочки, состав комбо, зависимости тем.
- [ ] Синтезировать **global датасет**: 6 вопросов-агрегатов с эталонными ответами и `required_entities`.
- [ ] Задать сегментную метрику поверх существующего eval-контура:
  - `answer_correctness` отдельно по каждому сегменту (single / multi / global)
  - `required_entity_recall@k` для retrieval
  - `faithfulness` как guard (не ухудшать)
- [ ] Создать `evals/configs/graphrag-baseline.yaml` (retriever: qdrant-hybrid, датасеты multi-hop + global).
- [ ] Прогнать `make -C evals experiment CONFIG=configs/graphrag-baseline.yaml` на текущем Qdrant-hybrid.
- [ ] Сохранить baseline-отчёт `evals/reports/graphrag-baseline.md`: метрики по сегментам, ожидаемые просадки на multi-hop и global.
- [ ] Встроить ссылку на отчёт в [docs/eval/README.md](../../eval/README.md).

**Критерии готовности:**

*Агент проверяет:*

- [ ] Датасеты сохранены в `evals/datasets/` (или согласно структуре eval-контура).
- [ ] `graphrag-baseline.yaml` валиден; `make -C evals experiment` завершается без ошибок.
- [ ] `graphrag-baseline.md` содержит метрики по трём сегментам.

*Пользователь проверяет:*

- [ ] Вопросы multi-hop реально требуют обхода 2+ узлов (не разрешаются одним чанком).
- [ ] Baseline-метрики фиксируют ожидаемую просадку на multi-hop/global.

**Артефакты:**

- `evals/datasets/graphrag-multihop-v001.json`
- `evals/datasets/graphrag-global-v001.json`
- `evals/configs/graphrag-baseline.yaml`
- `evals/reports/graphrag-baseline.md`

---



## Task 03: graph-schema-adr

**Цель:** спроектировать LPG-схему каталога, зафиксировать boundary rule и принять ADR с версиями Neo4j и SDK.

> 📌 **Перед началом:** прочитать `neo4j-modeling-skill` (anti-patterns, direction conventions, intermediate nodes); `neo4j-graphrag-skill` (выбор retriever-паттерна); `neo4j-cypher-skill` (именование).

**Состав работ:**

- [ ] Спроектировать LPG-схему:
  - **Узлы:** `Combo`, `Course`, `Module`, `Theme`, `Audience`, `Format`, `Level`
  - **Рёбра:** `INCLUDES` (Combo→Course), `RECOMMENDED_BEFORE` (Course→Course), `HAS_MODULE` (Course→Module), `COVERS` (Course/Module→Theme), `REQUIRES` (Theme→Theme), `TARGETS` (Course→Audience)
  - Явные направления рёбер (обосновать каждое); свойства узлов (цены, форматы, описания короткие).
- [ ] Сформулировать **boundary rule**: что идёт в граф, что остаётся в Qdrant:
  - Граф: структура и связи (prerequisite, состав, покрытие тем)
  - Свойства узлов: цены, форматы, уровень, короткие поля
  - Qdrant: длинные описания, FAQ, всё, что нужно семантическому поиску; связь по `id`
- [ ] Привязать каждый класс вопросов к маршруту обхода графа (Cypher-паттерн для каждого).
- [ ] Выбрать SDK: `neo4j-graphrag` (рекомендован) и/или `langchain-neo4j`; зафиксировать версии образа Neo4j и Python-пакетов.
- [ ] Зафиксировать конвенции: направления рёбер, именование (UPPER_CASE рёбра, PascalCase узлы), ключи нормализации (`id`, slug).
- [ ] Создать `docs/adrs/ADR-0010-graphrag.md`.

**Критерии готовности:**

*Агент проверяет:*

- [ ] `ADR-0010-graphrag.md` содержит: схему (узлы + рёбра с направлениями), boundary rule, версии Neo4j образа и SDK (не `latest`), конвенции именования.
- [ ] Каждый класс вопросов привязан к конкретному Cypher-маршруту.

*Пользователь проверяет:*

- [ ] Boundary rule понятен: ясно, что ищется вектором, что — графом.
- [ ] Направления рёбер логичны для обхода в сценариях use case.

**Артефакты:**

- `[docs/adrs/ADR-0010-graphrag.md](../../adrs/ADR-0010-graphrag.md)` — решение: Neo4j как граф-БД, версии, конвенции, boundary rule, guardrails text2cypher
- `[docs/sprints/sprint-09-graphrag/schema.md](schema.md)` — LPG-схема: узлы/рёбра с направлениями, Mermaid-диаграмма, boundary rule, Cypher-маршруты по классам вопросов, DDL constraints/indexes

---



## Task 04: neo4j-infra

**Статус:** ✅ Done

**Цель:** добавить Neo4j в docker-compose с APOC, health check, named volume и make-целями; верифицировать подключение из кода приложения.

> 📌 **Перед началом:** прочитать `neo4j-getting-started-skill` (provision, mcp-config); `neo4j-driver-python-skill` (lifecycle, verify_connectivity); `docker-expert` (health check patterns).

**Состав работ:**

- [x] Добавить сервис `neo4j` в `devops/docker-compose.yml`:
  - Образ `neo4j:2026.04.0-community` (ADR-0010)
  - Плагин APOC (`NEO4J_PLUGINS=["apoc"]`)
  - Health check: `cypher-shell RETURN 1` через Bolt (HTTP `/db/neo4j/available` → 404 на 2026.04)
  - Named volumes `neo4j_data` / `neo4j_logs`
  - `NEO4J_AUTH` из env
- [x] RO-пользователь `text2cypher_ro` (`make graph-init-ro`; `GRANT ROLE reader` — Enterprise-only)
- [x] `.env.example`: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_RO_USER`, `NEO4J_RO_PASSWORD`
- [x] Make-цели: `graph-up`, `graph-down`, `graph-status`, `graph-shell`, `graph-init-ro`
- [x] Smoke: `mcp_server/scripts/neo4j_smoke.py` + `tests/test_neo4j_smoke.py`
- [x] Runbook: `devops/README.md`; amend ADR-0010 §3.7

**Критерии готовности:**

*Агент проверяет:*

- [x] `make graph-up` → `docker compose ps neo4j` → `healthy`
- [x] `make test-mcp` зелёный (`test_neo4j_smoke` skip или pass)
- [x] `.env.example` содержит все Neo4j-переменные

*Пользователь проверяет:*

- [x] `make graph-shell` открывает интерактивный Cypher-шелл
- [x] Neo4j Browser на `:7474` доступен
- [x] `make graph-down && make graph-up` — данные в volume сохраняются

**Артефакты:**

- `devops/docker-compose.yml`, `.env.example`, `Makefile`
- `mcp_server/scripts/neo4j_smoke.py`, `neo4j_init_ro.py`, `neo4j_shell.py`
- `mcp_server/tests/test_neo4j_smoke.py`
- `devops/neo4j/init-text2cypher-ro.cypher`, `devops/README.md`
- [summary](tasks/04-neo4j-infra/summary.md)

---



## Task 05: graph-indexing

**Статус:** ✅ Done

**Цель:** наполнить граф тремя путями (ручной seed, авто-извлечение тем по схеме, entity resolution) и верифицировать качество через `graph-qa.cypher`.

> 📌 **Перед началом:** прочитать `neo4j-document-import-skill` (SimpleKGPipeline, entity resolution); `neo4j-cypher-skill` (MERGE, UNWIND batching); `neo4j-driver-python-skill` (execute_write, UNWIND).

**Состав работ:**

- [x] Написать `scripts/seed.cypher` — жёсткая структура вручную:
  - 4 курса-ступени с свойствами (id, title, price, level, format)
  - Комбо с `INCLUDES`-рёбрами
  - Prerequisite-цепочка (`RECOMMENDED_BEFORE`)
  - Аудитории (`TARGETS`)
- [x] Реализовать авто-извлечение тем строго по схеме:
  - `neo4j-graphrag SimpleKGPipeline`
  - Theme + post-process COVERS; REQUIRES seed-only после Phase 6
  - **Не используется** `LLMGraphTransformer`
- [x] Entity resolution:
  - Alias merge → canonical Theme (`graph_common.py`, strict mode)
  - Phase 8: dedupe COVERS, `THEME_ALIAS_PATCHES`, invariant checks
  - Fullstack-дубль, combo-цены → `entity-resolution.md` (таблица 29 тем)
- [x] `scripts/graph-qa.cypher` — 12 контрольных запросов
- [x] `make graph-index`, `graph-extract`, `graph-compare`, `graph-inspect`, `graph-qa`
- [x] `data/graph/extraction-report.md`, `browser-guide.md`, `entity-resolution.md`

**Критерии готовности:**

*Агент + пользователь:*

- [x] `make graph-index` без ошибок; идемпотентен
- [x] `graph-qa`: орфаны 0, дубли 0, REQUIRES 12
- [x] Нестыковки задокументированы → [summary](tasks/05-graph-indexing/summary.md), [entity-resolution.md](../../../data/graph/entity-resolution.md)

*Пользователь:*

- [x] Neo4j Browser — связный граф, prerequisite-цепочки
- [x] Части А–Д согласованы

**Артефакты:**

- `scripts/seed.cypher`, `scripts/graph_indexer.py`, `scripts/graph_compare.py`, `scripts/graph_common.py`
- `scripts/graph-qa.cypher`
- `data/graph/extraction-report.md`, `entity-resolution.md`, `browser-guide.md`
- `docs/research/text-to-graph-tools.md`
- Makefile: `graph-seed`, `graph-extract`, `graph-index`, `graph-compare`, `graph-inspect`, `graph-qa`

**Summary:** [tasks/05-graph-indexing/summary.md](tasks/05-graph-indexing/summary.md)

---



## Task 06: graph-retrieval

**Цель:** реализовать graph-, global- и hybrid-ветки retrieval через абстрактный интерфейс, добавить мультиязычный реранкер и сравнить с baseline по сегментам.

> 📌 **Перед началом:** прочитать `neo4j-graphrag-skill` (VectorCypherRetriever, HybridCypherRetriever); `neo4j-cypher-skill` (traversal patterns); `neo4j-driver-python-skill` (execute_read, RoutingControl).

**Состав работ:**

- [x] Реализовать `GraphRetriever` (extends `BaseRetriever`):
  - **graph-ветка:** vector-anchor (Qdrant) → Cypher-обход 1–2 шага → контекст из рёбер и соседних узлов
  - Custom Cypher + Qdrant anchor (external vectors; см. summary)
- [x] Реализовать **global-ветку**: структурный агрегат по каталогу — Cypher без community summaries; возвращает список курсов/тем с метаданными.
- [x] Добавить ветки в фабрику retriever'ов; `RETRIEVER_BRANCH` в env управляет выбором без правки кода.
- [x] Добавить **мультиязычный reranker** (optional extra `[reranker]`; без extra — skip с warning).
- [x] Реализовать слияние Qdrant-hybrid + graph через RRF (Reciprocal Rank Fusion).
- [x] Написать `evals/configs/graphrag-graph.yaml`; прогнать eval (`make eval-graph-hybrid`, `make eval-graph-global`).
- [x] Сохранить отчёт `evals/reports/graphrag-graph.md` с сравнением baseline vs graph по трём сегментам.

**Критерии готовности:**

*Агент проверяет:*

- [x] Смена `RETRIEVER_BRANCH=graph` / `vector` / `global` / `hybrid` работает без правки бизнес-логики.
- [x] `graphrag-graph.md` содержит сравнение по сегментам: multi-hop и global выше baseline; single-hop ⚠️ 0.638 vs gate 0.642.
- [x] `make test-mcp` зелёный (48 passed).

*Пользователь проверяет:*

- [ ] На вопросе «что нужно пройти перед курсом X» — граф возвращает prerequisite-цепочку, вектор — нет.
- [ ] На вопросе «сколько курсов про тему Y» — global-ветка даёт верный агрегат.

**Артефакты:**

- `mcp_server/retriever/graph.py` (GraphRetriever)
- `mcp_server/retriever/global_agg.py` (GlobalRetriever)
- `mcp_server/retriever/factory.py` (обновлён)
- `evals/configs/graphrag-graph.yaml`
- `evals/reports/graphrag-graph.md`

---



## Task 07: text2cypher

**Статус:** ✅ Done

**Цель:** добавить инструмент NL→Cypher за четырьмя guardrails и верифицировать, что write-запрос блокируется.

> 📌 **Перед началом:** прочитать `neo4j-cypher-skill` (syntax, schema-guardrail reference); `neo4j-graphrag-skill` (Text2CypherRetriever); `sharp-edges` (опасные API-паттерны).

**Состав работ:**

- [x] Реализовать `Text2CypherTool` через `Text2CypherRetriever` из `neo4j-graphrag`:
  - Подключить к read-only пользователю `text2cypher_ro` (создан в Task 04)
  - Передать в промпт `enhanced_schema` (автогенерация через `neo4j-graphrag`) и few-shot примеры (5 пар NL→Cypher)
- [x] 4 обязательных guardrail:
  1. **Read-only роль в БД** — `text2cypher_ro` без прав WRITE
  2. **Regex-фильтр на write-операции** — блокировать `CREATE`, `MERGE`, `DELETE`, `SET`, `REMOVE` до отправки в Neo4j
  3. **Таймаут и LIMIT** — добавлять `LIMIT 25` если не задан; таймаут запроса ≤ 5 с
  4. **Узкое описание инструмента** — агент вызывает только на агрегатные/структурные вопросы, не на semantic
- [x] Написать `tests/test_text2cypher_guardrails.py`:
  - `test_text2cypher_blocks_write` — write-запрос отклоняется с явной ошибкой
  - `test_text2cypher_adds_limit` — к запросу без LIMIT добавляется LIMIT
- [x] Верификация на примерах (handler smoke; routing — Task 08):
  - «Сколько курсов…» / «Какие курсы в комбо…» / «тема MCP» → `text2cypher_tool`
  - «Расскажи про курс Z» → routing в Task 08
- [x] Задокументировать примеры вызовов в summary.

**Критерии готовности:**

*Агент проверяет:*

- [x] `make test-mcp` зелёный; `test_text2cypher_blocks_write` и `test_text2cypher_adds_limit` pass.
- [x] Write blocked на Python-слое (Community RO без RBAC — regex + EXPLAIN).

*Пользователь проверяет:*

- [x] Smoke NL→Cypher на живом Neo4j (`handle_text2cypher`).
- [x] Docstring tool понятен (когда вызывать / когда нет).
- [ ] Langfuse-трейс и «расскажи про X» не вызывает tool — **Task 08**.

**Артефакты:**

- `mcp_server/mcp_server/tools/text2cypher.py`
- `mcp_server/mcp_server/retriever/text2cypher.py`
- `mcp_server/mcp_server/text2cypher/guardrails.py`, `schema.py`
- `mcp_server/tests/test_text2cypher_guardrails.py`
- `scripts/few_shot_examples.json`

**Summary:** [tasks/07-text2cypher/summary.md](tasks/07-text2cypher/summary.md)

---



## Task 08: agent-routing

**Статус:** ✅ Done

**Цель:** зарегистрировать все ветки у агента, добавить правила маршрутизации в системный промпт и провести финальный end-to-end прогон по всем сегментам.

> 📌 **Перед началом:** прочитать `neo4j-graphrag-skill` (ToolsRetriever); проверить `.agents/skills/`.

**Состав работ:**

- [x] Зарегистрировать у агента инструменты: `vector_search`, `graph_search`, `global_catalog`, `text2cypher_tool`.
- [x] Добавить в системный промпт явные правила маршрутизации (v4 + v5 fix-loop).
- [x] Прогнать eval по всем трём сегментам с routing-конфигом (`graphrag-routing`, `graphrag-routing-v5`).
- [x] Сохранить финальный отчёт `evals/reports/graphrag-final.md` + `graphrag-regression.md`.
- [x] Верифицировать маршрутизацию по трейсам в Langfuse (user-check).
- [x] Обновить `roadmap.md`: статус sprint-09 → ✅ Done.
- [x] Обновить этот README: статус + раздел «Итог».

**Summary:** [tasks/08-agent-routing/summary.md](tasks/08-agent-routing/summary.md)

---



## Итог

Sprint-09 закрыт **2026-06-30**. GraphRAG-слой добавлен поверх Qdrant: Neo4j-граф каталога, ветки retrieval (vector / graph / global / text2cypher), agent tool-per-branch routing.

### Метрики (финал Task 08, git `f6c0db35`)

| Сегмент | Baseline | Routing (v5) | Gate |
|---------|----------:|-------------:|------|
| multi-hop | 0.383 | **0.542** | ✅ |
| global | 0.200 | **0.433** | ✅ |
| single-hop (e2e-qa) | 0.662 | **0.665** | ✅ (≥ 0.642) |

Отчёты: [graphrag-final.md](../../../evals/reports/graphrag-final.md) · [graphrag-regression.md](../../../evals/reports/graphrag-regression.md).

### Ключевые артефакты

- ADR: [ADR-0010-graphrag.md](../../adrs/ADR-0010-graphrag.md)
- Eval configs: `graphrag-routing.yaml`, `graphrag-routing-v5.yaml`
- Prompts: `agent-system-prompt-v4` (routing), `v5` (generation fixes)
- Infra: Neo4j в docker-compose, `make graph-seed`, text2cypher RO user

### Backlog (не блокирует спринт)

- Prod cutover: default prompt v5, Neo4j в deploy pipeline
- Prompt v5.1: рассрочка (0022), интенсив (0005), agents↔deep-agents (0018/0019)
- Reranker eval с optional extra; RRF fusion в `graph_search`
- GL-01 Instructor node (data gap)

