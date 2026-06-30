# Task 05: graph-indexing — Plan

> **Sprint:** [../../README.md](../../README.md)  
> **Тип:** feat  
> **Ветка:** `feat/graphrag-05-graph-indexing`  
> **Spec:** [schema.md](../../schema.md), [ADR-0010](../../../../adrs/ADR-0010-graphrag.md), [analysis.md](../../analysis.md)

---

## Цель

Наполнить граф знаний каталога курсов и верифицировать качество через пять последовательных итераций: ручной seed → инспекция → авто-извлечение тем → сравнение → entity resolution и финализация.

## Части задачи

| Часть | Название | Ключевые артефакты | Статус |
|-------|----------|--------------------|--------|
| **А** | Ручной seed | `scripts/seed.cypher` | ✅ Done |
| **Б** | Инспекция и отчётность | `scripts/graph-qa.cypher`, `data/graph/browser-guide.md`, `make graph-inspect`, `make graph-qa` | ✅ Done |
| **В** | Ресёрч + авто-извлечение тем | `docs/research/text-to-graph-tools.md`, `scripts/graph_indexer.py` | ✅ Done |
| **Г** | Сравнение ручного и авто | `make graph-compare`, `data/graph/extraction-report.md` | ✅ Done |
| **Д** | Entity resolution и финализация | `data/graph/entity-resolution.md`, финальный граф | ✅ Done |

Каждая часть стартует после явного «ок» на предыдущую.

---

## Источники данных

| Файл | Что берём |
|------|-----------|
| `data/real_data/b2c/programs/ai-coding-intensive-cursor.md` | vibe-coding: цена, формат, темы, аудитории |
| `data/real_data/b2c/programs/ai-driven-fullstack.md` | fullstack-aidd: цена, формат, темы, аудитории |
| `data/real_data/b2c/programs/aidd-program.md` | алиас fullstack-aidd — один узел (см. entity resolution §5.1 analysis.md) |
| `data/real_data/b2c/programs/ai-coding-agents-base.md` | agents: цена, формат, темы, аудитории |
| `data/real_data/b2c/programs/deep-agents-advanced.md` | deep-agents: цена, формат, темы, аудитории |
| `data/real_data/b2c/programs/ai-agents-combo.md` | комбо: цена, состав ступеней |
| `data/real_data/b2b/corporate-training.md` | B2B аудитория `team` — только как Audience-узел |

**Не входит в seed:**
- `data/leads.txt`, `data/payments.json` — вне скоупа графа
- `data/real_data/b2b/*.pdf` — вне скоупа
- `consultation` из `catalog.json` — нет real_data-источника

---

## Инвентарь узлов для seed.cypher

### Узлы `Level` (3 шт.)

| id | name | sortOrder |
|----|------|-----------|
| `intensive` | Интенсив | 1 |
| `intermediate` | Средний | 2 |
| `advanced` | Продвинутый | 3 |

### Узлы `Format` (6 шт.)

| id | name | durationDaysMin | durationDaysMax |
|----|------|-----------------|-----------------|
| `self-paced` | Видеокурс (запись) | null | null |
| `hybrid` | Гибрид (live + запись) | null | null |
| `live` | Online live | null | null |
| `workshop` | Воркшоп / интенсив | 3 | 5 |
| `corporate` | Корпоративная программа | null | null |
| `mentoring` | Менторинг | null | null |

### Узлы `Audience` (5 шт.)

| id | role | segment |
|----|------|---------|
| `non-dev` | non-dev | b2c |
| `dev` | dev | b2c |
| `executive` | executive | b2c |
| `team` | team | b2b |
| `ai-engineer` | ai-engineer | b2c |

### Узлы `Theme` (29 шт.)

Канонический `id` определён по `analysis.md §5.5`. `aliases` заполняются на этапе Б (авто-извлечение), здесь — пустой список или минимальные алиасы.

| id | name | aliases (основные) |
|----|------|--------------------|
| `ai-driven-methodology` | AI-driven методология | ["AI-driven подход", "AIDD"] |
| `llm-api` | LLM API и промпт-инжиниринг | ["LLM API", "промпт-инжиниринг", "prompt engineering"] |
| `react-agent` | ReAct паттерн | ["ReAct", "ReAct паттерн", "Reasoning+Acting"] |
| `multimodality` | Мультимодальность | ["голос", "изображения", "мультимодальные возможности"] |
| `rag-basic` | RAG (базовый pipeline) | ["RAG", "RAG-система", "RAG pipeline", "Retrieval-Augmented Generation"] |
| `rag-advanced` | Advanced RAG | ["Self-RAG", "Agentic RAG", "Hybrid Search", "Query Transformation", "Advanced RAG"] |
| `vector-db` | Векторные базы данных | ["ChromaDB", "Qdrant", "векторные БД", "embedding"] |
| `langchain-langgraph` | LangChain / LangGraph | ["LangChain", "LangGraph", "LangSmith"] |
| `tool-calling` | Tool calling | ["tool calling", "инструменты агента", "function calling"] |
| `agent-memory` | Память агента | ["краткосрочная память", "долгосрочная память", "memory"] |
| `hitl` | Human-in-the-loop | ["HITL", "human-in-the-loop"] |
| `multi-agent` | Мультиагентные системы | ["мультиагентные паттерны", "multi-agent", "Network", "Supervisor", "Hierarchical"] |
| `evaluation` | Evaluation / Evals | ["RAGAS", "DeepEval", "LLM-as-Judge", "evals", "оценка качества"] |
| `security-guardrails` | Безопасность / guardrails | ["guardrails", "LLMGuard", "Giskard", "adversarial prompting", "jailbreaking"] |
| `mcp` | Model Context Protocol | ["MCP", "Model Context Protocol"] |
| `observability` | Observability | ["LangSmith", "LangFuse", "мониторинг", "трейсинг", "Prometheus", "Grafana"] |
| `fastapi-backend` | FastAPI / Backend API | ["FastAPI", "Backend API", "REST API", "API-сервис"] |
| `postgresql` | PostgreSQL / ORM | ["PostgreSQL", "ORM", "база данных", "Alembic", "SQLAlchemy"] |
| `frontend-dev` | Frontend разработка | ["React", "Next.js", "веб-интерфейс", "SPA"] |
| `docker-devops` | Docker / DevOps | ["Docker", "контейнеризация", "DevOps", "docker-compose"] |
| `cicd` | CI/CD | ["CI/CD", "GitHub Actions", "pipeline"] |
| `graph-db` | Графовые базы данных | ["Neo4j", "графовые БД", "граф знаний", "Knowledge Graph"] |
| `graphrag` | GraphRAG | ["граф + RAG", "GraphRAG", "гибридный поиск граф+вектор"] |
| `multimodal-rag` | Мультимодальный RAG | ["мультимодальный RAG", "Vision API", "визуально-насыщенные документы"] |
| `context-engineering` | Context Engineering | ["управление контекстом", "Deep Context Engineering", "dynamic context"] |
| `deep-agents-skills` | Deep Agents (planning/skills/subagents) | ["planning", "skills", "subagents", "task decomposition", "checkpoint/resume"] |
| `dataset-management` | Датасет-менеджмент | ["annotation queues", "валидационные датасеты", "data-driven подход"] |
| `prompt-management` | Prompt Management | ["версионирование промптов", "A/B тесты промптов", "Prompt Playground"] |
| `a2a-a2ui` | A2A / A2UI протоколы | ["Agent-to-Agent", "Agent-to-UI", "A2A", "A2UI"] |

### Узлы `Course` (4 шт.)

Источник цен: **только `real_data/*.md`**, не `catalog.json`.

| id | title | priceRub | level | format | durationWeeks | lessonsCount | segment |
|----|-------|----------|-------|--------|---------------|--------------|---------|
| `vibe-coding` | Интенсив AI-кодинг ИИ-агентов в Cursor | 14990 | intensive | self-paced | null | 4 | b2c |
| `fullstack-aidd` | AI-driven Fullstack разработка | 39990 | intermediate | self-paced | 6 | 10 | b2c |
| `agents` | AI-driven разработка ИИ-агентов | 39990 | intermediate | hybrid | 6 | 11 | both |
| `deep-agents` | Deep Agents: продвинутая разработка ИИ-агентов | 44990 | advanced | live | 8 | 12 | b2c |

> **Entity resolution:** `aidd-program.md` — тот же курс, что `fullstack-aidd`. Один `Course`-узел. Число занятий берём из `ai-driven-fullstack.md` (10), расхождение с `aidd-program.md` (12) зафиксировано в `analysis.md §5.1`.

### Узлы `Combo` (1 шт.)

| id | title | priceRub | discountPct | descriptionShort |
|----|-------|----------|-------------|-----------------|
| `ai-agents-combo` | Комбо «ИИ-агенты»: траектория от 0 до эксперта | 59990 | 57 | Единая траектория по AI-driven разработке: от AI-кодинга до production-ready мультиагентных систем |

> **Расчёт скидки:** фактическая сумма курсов = 14990 + 39990 + 39990 + 44990 = **139 960 ₽** (значение «134 960 ₽» в таблице файла — редакционная ошибка). discountPct = round(1 − 59990/139960, 2) = **0.57** (57%).

---

## Инвентарь рёбер для seed.cypher

### `AT_LEVEL` — Course → Level (4 рёбра)

| Курс | Уровень |
|------|---------|
| vibe-coding | intensive |
| fullstack-aidd | intermediate |
| agents | intermediate |
| deep-agents | advanced |

### `AVAILABLE_AS` — Course → Format (7 рёбер)

| Курс | Формат |
|------|--------|
| vibe-coding | self-paced |
| fullstack-aidd | self-paced |
| agents | hybrid |
| agents | workshop |
| agents | corporate |
| agents | mentoring |
| deep-agents | live |

### `TARGETS` — Course → Audience (8 рёбер)

| Курс | Аудитория |
|------|-----------|
| vibe-coding | non-dev |
| vibe-coding | executive |
| vibe-coding | dev |
| fullstack-aidd | dev |
| agents | dev |
| agents | ai-engineer |
| deep-agents | dev |
| deep-agents | ai-engineer |

### `INCLUDES` — Combo → Course (4 рёбра)

| Комбо | Курс | stepOrder |
|-------|------|-----------|
| ai-agents-combo | vibe-coding | 1 |
| ai-agents-combo | fullstack-aidd | 2 |
| ai-agents-combo | agents | 3 |
| ai-agents-combo | deep-agents | 4 |

### `RECOMMENDED_BEFORE` — Course → Course (3 рёбра)

| Курс (ранний) | Курс (поздний) | mandatory | source |
|---------------|----------------|-----------|--------|
| vibe-coding | fullstack-aidd | false | explicit |
| fullstack-aidd | agents | false | explicit |
| agents | deep-agents | true | explicit |

> Источник: `ai-agents-combo.md` — «последовательный маршрут, каждая ступень опирается на предыдущую»; `mandatory: true` для `agents→deep-agents` — требование явно указано («ИТ-специалисты с базовыми знаниями LLM и агентов» в `deep-agents-advanced.md`).

### `COVERS` — Course → Theme (42 рёбра)

Параметр `depth`: `intro` = обзорно, `core` = основная тема, `advanced` = углублённо.

#### vibe-coding (4 рёбра)

| Тема | depth | Обоснование |
|------|-------|-------------|
| ai-driven-methodology | core | Модуль 1 целиком посвящён AI-driven подходу |
| llm-api | intro | LLM используются в практиках, основы не разбираются отдельно |
| react-agent | core | Модуль 4: Автономные ИИ-агенты (ReAct) |
| multimodality | core | Модуль 3: мультимодальный ИИ-продукт, голос, изображения |

#### fullstack-aidd (9 рёбер)

| Тема | depth | Обоснование |
|------|-------|-------------|
| ai-driven-methodology | core | Темы 2–3 про AI-driven разработку с Cursor |
| llm-api | intro | Тема 1: Основы LLM, обзорно |
| fastapi-backend | core | Тема 4: Разработка Backend API-сервиса |
| postgresql | core | Тема 5: Проектирование и интеграция базы данных |
| frontend-dev | core | Тема 6: Frontend-разработка |
| docker-devops | core | Тема 8: DevOps, Dockerfile, docker-compose |
| cicd | core | Тема 9: CI/CD, GitHub Actions |
| observability | core | Тема 10: Production-ready, логирование, метрики, дашборды |
| mcp | intro | aidd-program.md: MCP для взаимодействия с браузером |

#### agents (15 рёбер)

| Тема | depth | Обоснование |
|------|-------|-------------|
| ai-driven-methodology | intro | Тема 2: AI-driven разработка с Cursor, вводно |
| llm-api | core | Тема 1: Основы LLM и API — центральная тема |
| rag-basic | core | Тема 4: RAG с LangChain от теории к практике |
| rag-advanced | core | Тема 6: Advanced RAG |
| vector-db | core | Тема 4: векторные БД и embedding модели |
| langchain-langgraph | core | Тема 7: Агенты с LangChain и LangGraph |
| tool-calling | core | Тема 7: tool calling |
| agent-memory | core | Тема 7: память агента |
| hitl | intro | Тема 9: Human-in-the-loop как элемент безопасности |
| multi-agent | intro | Тема 11: Переход к мультиагентным системам |
| evaluation | core | Тема 10: Оценка качества агентов (RAGAS, DeepEval, LLM-as-Judge) |
| security-guardrails | core | Тема 9: Безопасность агентных систем |
| mcp | core | Тема 8: Model Context Protocol |
| observability | core | Тема 5: Мониторинг и оценка качества RAG (LangSmith/LangFuse) |
| multimodality | intro | Тема 3: Мультимодальные возможности и локальный LLM |

#### deep-agents (14 рёбер)

| Тема | depth | Обоснование |
|------|-------|-------------|
| ai-driven-methodology | intro | Темы 1–2: проектирование агента и AI-кодинг |
| graph-db | core | Тема 5: Графовые базы данных и GraphRAG |
| graphrag | core | Тема 5: GraphRAG — центральная тема |
| vector-db | intro | Тема 4: Векторные БД (вводно, опирается на agents) |
| multimodal-rag | core | Тема 6: Мультимодальный RAG |
| context-engineering | advanced | Тема 7: Продвинутый context-engineering |
| deep-agents-skills | advanced | Тема 8: Deep Agents: planning и делегирование |
| dataset-management | core | Тема 3: Датасет-менеджмент |
| prompt-management | core | Тема 10: Prompt Management |
| a2a-a2ui | core | Тема 12: Масштабирование агентных систем, A2A/A2UI |
| multi-agent | advanced | Тема 11: Мультиагентные паттерны (продвинутый уровень) |
| evaluation | advanced | Тема 9: Evaluation и Red teaming (продвинутый) |
| security-guardrails | advanced | Тема 9: Red teaming, adversarial attacks |
| langchain-langgraph | intro | Упоминается как базовый стек; основное — в `agents` |

### `REQUIRES` — Theme → Theme (12 рёбер)

Направление: `(A)-[:REQUIRES]->(B)` = «для изучения A нужна B».

| Тема (требует) | Тема (базовая) | Обоснование |
|----------------|----------------|-------------|
| graphrag | rag-basic | GraphRAG — расширение RAG-паттерна |
| graphrag | vector-db | Векторный поиск — одна из ног GraphRAG |
| graphrag | graph-db | Обход графа — вторая нога GraphRAG |
| rag-advanced | rag-basic | Advanced RAG строится на базовом pipeline |
| multimodal-rag | rag-basic | Мультимодальный RAG = RAG + Vision-модели |
| multimodal-rag | multimodality | Требует понимания мультимодальности |
| multi-agent | langchain-langgraph | Реализация через LangGraph |
| multi-agent | tool-calling | Агенты взаимодействуют через инструменты |
| deep-agents-skills | multi-agent | Deep Agents — продвинутые паттерны над мультиагентами |
| hitl | react-agent | HITL = прерывание ReAct-цикла |
| context-engineering | mcp | Внешние источники контекста интегрируются через MCP |
| evaluation | observability | Метрики строятся поверх трейсов (LangSmith/LangFuse) |

---

## Порядок MERGE-операций в seed.cypher

```
1. Constraints (идемпотентно, IF NOT EXISTS):
   Course, Combo, Theme, Audience, Format, Level — UNIQUE на id

2. Indexes:
   course_price_idx ON (c:Course.priceRub)
   course_level_idx ON (c:Course.level)
   theme_name_ft    FULLTEXT ON [t.name, t.id]

3. Узлы Level     (3 MERGE)
4. Узлы Format    (6 MERGE)
5. Узлы Audience  (5 MERGE)
6. Узлы Theme     (29 MERGE)
7. Узлы Course    (4 MERGE)
8. Узлы Combo     (1 MERGE)

9.  Рёбра AT_LEVEL           (4)
10. Рёбра AVAILABLE_AS       (7)
11. Рёбра TARGETS            (8)
12. Рёбра INCLUDES           (4)
13. Рёбра RECOMMENDED_BEFORE (3)
14. Рёбра COVERS             (42)
15. Рёбра REQUIRES           (12)
```

**Итого:** 48 узлов, 80 рёбер.

---

## Entity resolution — решения при seed

| Проблема (из analysis.md) | Решение в seed.cypher |
|---------------------------|----------------------|
| Два файла для fullstack: `ai-driven-fullstack.md` и `aidd-program.md` | Один `MERGE` по `id: "fullstack-aidd"`; свойства из `ai-driven-fullstack.md`. `aidd-program.md` — алиас |
| Сумма курсов комбо 134 960 ₽ vs 139 960 ₽ | Цена берётся из отдельных файлов: 14990+39990+39990+44990=139960. `discountPct: 57` |
| Slug-алиасы: `vibe-coding-intensive` → `vibe-coding` | Каноничный `id` = URL-slug; алиасы не создают отдельных узлов |
| `consultation` из catalog.json | Не включать: нет real_data-источника |
| Тема «контекст-инжиниринг» / «промпт-инжиниринг» | Два отдельных узла: `context-engineering` и `llm-api` (включает prompt engineering) |

---

## Часть А: Ручной seed — состав работ

- [ ] Написать `scripts/seed.cypher`:
  - Constraints + indexes (раздел 1–2)
  - MERGE-узлы в порядке: Level → Format → Audience → Theme → Course → Combo
  - MERGE-рёбра в порядке: AT_LEVEL → AVAILABLE_AS → TARGETS → INCLUDES → RECOMMENDED_BEFORE → COVERS → REQUIRES
  - Все операции через `MERGE` (не `CREATE`) — идемпотентность
- [ ] Запустить: `make graph-index` (цель добавить в Makefile)
- [ ] Добавить в `Makefile` цель `graph-index`: `cypher-shell < scripts/seed.cypher`
- [ ] Проверить в Neo4j Browser: `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100`
- [ ] Написать `scripts/graph-qa.cypher`:
  - Орфанные узлы: `MATCH (n) WHERE NOT (n)--() RETURN n`
  - Дубли тем (toLower)
  - Распределение степеней
  - Покрытие тем по курсам
- [ ] Самопроверка по DoD

---

## Часть А: Критерии готовности (DoD)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | seed.cypher исполняется без ошибок | `make graph-index` → exit 0 |
| 2 | Повторный запуск идемпотентен | `make graph-index` → дважды → количество узлов не меняется |
| 3 | 48 узлов в графе | `MATCH (n) RETURN count(n)` → 48 |
| 4 | 80 рёбер в графе | `MATCH ()-[r]->() RETURN count(r)` → 80 |
| 5 | Prerequisite-цепочка воспроизводима | `MATCH p=()-[:RECOMMENDED_BEFORE*]->() RETURN p` → 3 пути |
| 6 | Граф видим в Neo4j Browser | `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100` → связный граф |
| 7 | graph-qa.cypher: орфанных узлов 0 | Все узлы имеют хотя бы одно ребро |
| 8 | Нестыковки задокументированы | entity resolution решения зафиксированы в summary |

---

## Артефакты (все части)

| Файл | Часть | Описание |
|------|-------|----------|
| `scripts/seed.cypher` | А | Constraints + indexes + MERGE-узлы + MERGE-рёбра |
| `scripts/graph-qa.cypher` | А/Б | 7 контрольных Cypher-запросов |
| `data/graph/browser-guide.md` | Б | Инструкция Neo4j Browser: логин, starter queries, CLI |
| `Makefile` (graph-inspect, graph-qa, graph-seed, graph-extract, graph-index, graph-compare) | А–Д | Make-цели пайплайна |
| `docs/research/text-to-graph-tools.md` | В | Сравнительная таблица 7 инструментов text-to-graph |
| `scripts/graph_indexer.py` | В | Авто-извлечение тем через SimpleKGPipeline |
| `scripts/graph_compare.py` | Г | Diff seed vs auto + keyword-recall |
| `data/graph/extraction-report.md` | Г | Финальный отчёт: diff, keyword-recall, решения |
| `data/graph/entity-resolution.md` | Д | Все нестыковки и принятые решения |

---

## Scope

**Трогаем:** файлы из таблицы «Артефакты», этот `plan.md`.

**НЕ трогаем:**
- backend/bot/frontend
- Tasks 06–08
- `data/leads.txt`, `data/payments.json`

---

## Риски и допущения

| Риск | Митигация |
|------|-----------|
| `cypher-shell` не доступен вне контейнера | Запускать через `make graph-shell` или `docker exec` |
| Темы с `aliases: []` — авто-извлечение не совпадёт | Часть Б (SimpleKGPipeline) дополнит; seed задаёт канонический `id` |
| `durationWeeks: null` у vibe-coding | Интенсив без фиксированного графика; оставить null |
| 57% vs 56% в файле комбо | 57% корректно по арифметике; 56% — ошибка в таблице |

---

## Часть Б: Инспекция и отчётность

**Цель:** убедиться, что ручной seed корректен — нет орфанов, дублей, нарушений схемы — зафиксировать baseline-состояние графа и создать инструкции для работы с Browser.

### Состав работ

#### Б-1. `scripts/graph-qa.cypher` — 7 контрольных запросов

```cypher
// 1. Орфанные узлы (без рёбер) — ожидаем 0
MATCH (n) WHERE NOT (n)--()
RETURN labels(n)[0] AS label, n.id AS id, n.name AS name;

// 2. Дубли тем по toLower(name) — ожидаем 0
MATCH (t1:Theme), (t2:Theme)
WHERE elementId(t1) < elementId(t2)
  AND toLower(t1.name) = toLower(t2.name)
RETURN t1.id AS dup1, t2.id AS dup2;

// 3. Покрытие тем по курсам (Course → Theme)
MATCH (c:Course)-[:COVERS]->(t:Theme)
RETURN c.id AS course, count(t) AS themeCnt,
       collect(t.id) AS themeIds
ORDER BY themeCnt DESC;

// 4. Входящая степень тем (популярность)
MATCH (t:Theme)
OPTIONAL MATCH ()-[r]->(t)
RETURN t.id AS theme, count(r) AS inDegree
ORDER BY inDegree DESC;

// 5. Prerequisite-цепочки (полные пути)
MATCH p = ()-[:RECOMMENDED_BEFORE*]->()
WHERE NOT ()-[:RECOMMENDED_BEFORE]->(startNode(p))
RETURN [n IN nodes(p) | n.id] AS chain, length(p) AS hops
ORDER BY hops DESC;

// 6. Курсы без аудитории (TARGETS) — ожидаем 0
MATCH (c:Course)
WHERE NOT (c)-[:TARGETS]->()
RETURN c.id AS courseWithoutAudience;

// 7. Итоговые счётчики по меткам и типам рёбер
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC;
MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC;
```

#### Б-2. Make-цели

```makefile
# Статистика: узлы/рёбра по типам, orphans, COVERS-покрытие
graph-inspect:
	docker exec neo4j cypher-shell \
	  -u $(NEO4J_USER) -p $(NEO4J_PASSWORD) \
	  "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC; \
	   MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC; \
	   MATCH (n) WHERE NOT (n)--() RETURN 'ORPHAN' AS status, labels(n)[0], n.id; \
	   MATCH (c:Course)-[:COVERS]->(t:Theme) \
	     RETURN c.id, count(t) AS themes ORDER BY themes DESC;"

# 7 контрольных Cypher-запросов из graph-qa.cypher
graph-qa:
	docker exec -i neo4j cypher-shell \
	  -u $(NEO4J_USER) -p $(NEO4J_PASSWORD) \
	  < scripts/graph-qa.cypher
```

- [ ] Написать `scripts/graph-qa.cypher` (запросы Б-1 выше)
- [ ] Добавить `graph-inspect` и `graph-qa` в `Makefile`
- [ ] Прогнать `make graph-inspect` и `make graph-qa` после seed; результаты внести в `summary.md` часть Б

#### Б-3. `data/graph/browser-guide.md` — инструкция Neo4j Browser

Создать файл `data/graph/browser-guide.md` со структурой:

```
# Neo4j Browser — быстрый старт для графа каталога

## Доступ
- URL: http://localhost:7474
- Login: neo4j / <NEO4J_PASSWORD из .env>
- Bolt: bolt://localhost:7687

## CLI-команды
make graph-shell   # интерактивный cypher-shell в контейнере
make graph-inspect # статистика узлов/рёбер
make graph-qa      # 7 контрольных запросов

## Starter queries

### Весь граф (первые 100 рёбер)
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100

### Prerequisite-цепочки
MATCH p=()-[:RECOMMENDED_BEFORE*]->() RETURN p

### Все темы курса
MATCH (c:Course {id: "agents"})-[:COVERS]->(t:Theme)
RETURN t.id, t.name, t.aliases

### Что нужно пройти перед deep-agents
MATCH p=(start:Course)-[:RECOMMENDED_BEFORE*]->(target:Course {id: "deep-agents"})
WHERE NOT ()-[:RECOMMENDED_BEFORE]->(start)
RETURN [n IN nodes(p) | n.id] AS prerequisiteChain

### Все темы комбо
MATCH (cb:Combo {id:"ai-agents-combo"})-[:INCLUDES]->(c:Course)-[:COVERS]->(t:Theme)
RETURN DISTINCT t.id, t.name ORDER BY t.name

### Курсы для аудитории non-dev
MATCH (c:Course)-[:TARGETS]->(a:Audience {role:"non-dev"})
RETURN c.id, c.title, c.priceRub
```

- [ ] Создать `data/graph/browser-guide.md`

### Критерии готовности части Б

| # | Критерий |
|---|----------|
| 1 | Орфанных узлов 0 (`make graph-qa`) |
| 2 | Дублей тем 0 |
| 3 | Prerequisite-цепочка: 3 пути от vibe-coding до deep-agents |
| 4 | Каждый `Course` связан с ≥1 `Theme` через `COVERS` |
| 5 | `data/graph/browser-guide.md` создан |
| 6 | `make graph-inspect` и `make graph-qa` работают без ошибок |

---

## Часть В: Ресёрч + авто-извлечение тем

**Цель:** выбрать инструмент для text-to-graph extraction на основании сравнительного ресёрча, реализовать `graph_indexer.py` строго по схеме.

### В-1. Ресёрч: сравнение инструментов text-to-graph

Создать `docs/research/text-to-graph-tools.md` — таблица сравнения:

| Критерий | LLMGraphTransformer | SimpleKGPipeline | GLiNER | Relik | spaCy NER | LlamaIndex SchemaLLMPathExtractor | MS GraphRAG |
|----------|---------------------|------------------|--------|-------|-----------|-----------------------------------|-------------|
| **Тип** | LLM prompt | LLM prompt | zero-shot NER | zero-shot RE | rule/ML NER | LLM prompt | LLM pipeline |
| **Schema-constrained** | ❌ (freestyle) | ✅ (allowed_nodes/rels) | ⚠️ частично | ⚠️ частично | ❌ | ✅ | ❌ |
| **Язык** | en/ru | en/ru | en/ru/мультиязычный | en/ru | зависит от модели | en/ru | en |
| **Зависимость** | `langchain-experimental` ⚠️ | `neo4j-graphrag` ✅ | `gliner` | `relik` | `spacy` | `llama-index` | `graphrag` |
| **Требует LLM** | ✅ да | ✅ да | ❌ нет | ❌ нет | ❌ нет | ✅ да | ✅ да |
| **Community summaries** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Leiden) |
| **Используется в проекте** | ❌ ЗАПРЕЩЁН | ✅ рекомендован | исследовать | исследовать | исследовать | альтернатива | ❌ оверкилл |
| **Вывод** | запрещён ADR-0010 | **выбор по умолчанию** | возможная оптимизация | возможная оптимизация | fallback | если SimpleKGP не подойдёт | не нужен |

**Секции документа:**
- Краткое описание каждого инструмента (2–3 строки)
- Таблица сравнения
- Обоснование выбора для этого проекта
- Ссылки на документацию

- [ ] Создать `docs/research/text-to-graph-tools.md`

### В-2. Реализация `scripts/graph_indexer.py`

**Ограничения:**
- Использовать **только** `neo4j-graphrag SimpleKGPipeline` (или `LlamaIndex SchemaLLMPathExtractor` как fallback).
- **Запрещено:** `LLMGraphTransformer` из `langchain-experimental`.
- Извлекать только узлы `Theme`, рёбра `COVERS` (Course→Theme) и `REQUIRES` (Theme→Theme).
- Все записи через `MERGE` — идемпотентность.
- Проставлять `source: "auto"` на новых узлах (отличие от `source: "seed"`).

- [ ] Реализовать `scripts/graph_indexer.py`:
  - Загрузить тексты из `data/real_data/b2c/programs/*.md`
  - Настроить pipeline со строгой схемой:
    ```python
    allowed_nodes = ["Theme"]
    allowed_relationships = [
        ("Course", "COVERS", "Theme"),
        ("Theme", "REQUIRES", "Theme"),
    ]
    ```
  - Нормализация: `toLower` → `strip` → slug → совпадение с существующими `Theme.aliases`
  - Запись через `execute_write` + `MERGE {id: $slug} ON CREATE SET source = "auto"`
  - Логировать: новые Theme-узлы, новые рёбра, пропущенные (уже в seed)

- [ ] Добавить в `Makefile`:
  ```makefile
  graph-extract:
      uv run python scripts/graph_indexer.py

  graph-index: graph-seed graph-extract
  ```

### Критерии готовности части В

| # | Критерий |
|---|----------|
| 1 | `docs/research/text-to-graph-tools.md` создан, все 7 инструментов разобраны |
| 2 | `graph_indexer.py` завершается без ошибок |
| 3 | Повторный запуск идемпотентен |
| 4 | Нет узлов типов вне схемы (только `Theme`) |
| 5 | Новые узлы помечены `source: "auto"` |

---

## Часть Г: Сравнение ручного seed и авто-извлечения

**Цель:** выявить расхождения между seed-темами и авто-извлечёнными, измерить keyword-recall, принять решение по каждому расхождению; сохранить финальный отчёт.

### Состав работ

#### Г-1. `make graph-compare` — diff + keyword-recall

```makefile
graph-compare:
    uv run python scripts/graph_compare.py \
        --output data/graph/extraction-report.md
```

`scripts/graph_compare.py` должен:

1. **Diff seed vs auto** — Cypher-запросы:
   ```cypher
   // Авто-темы без совпадения с seed
   MATCH (t:Theme {source: "auto"})
   WHERE NOT EXISTS {
     MATCH (s:Theme {source: "seed"})
     WHERE s.id = t.id OR t.id IN s.aliases
   }
   RETURN t.id, t.name, [(c)-[:COVERS]->(t) | c.id] AS coveredBy;

   // Seed-темы без авто-подтверждения
   MATCH (t:Theme {source: "seed"})
   WHERE NOT EXISTS {
     MATCH (a:Theme {source: "auto"})
     WHERE a.id = t.id OR t.id IN a.aliases
   }
   RETURN t.id, t.name;
   ```

2. **Keyword-recall** — для каждой seed-темы проверить, упоминается ли хотя бы один её alias в тексте исходных `.md`-файлов:
   ```python
   # pseudo-code
   for theme in seed_themes:
       keywords = [theme.id] + theme.aliases
       hits = [kw for kw in keywords if kw.lower() in source_text.lower()]
       recall = len(hits) / len(keywords)
   ```
   Результат: таблица `theme_id | aliases_total | aliases_found | keyword_recall`.

3. Сохранить `data/graph/extraction-report.md`:
   ```markdown
   # Graph Extraction Report
   Generated: <timestamp>

   ## Summary
   | Metric | Value |
   |--------|-------|
   | Seed themes | 29 |
   | Auto themes (new) | N |
   | Auto themes (merged) | M |
   | Avg keyword recall | 0.XX |

   ## Diff: авто-темы без seed-совпадения
   | theme_id | name | coveredBy |

   ## Diff: seed-темы без авто-подтверждения
   | theme_id | name |

   ## Keyword recall по seed-темам
   | theme_id | aliases_total | aliases_found | recall |

   ## Решения
   | theme_id | action (merge/keep/drop) | комментарий |
   ```

- [ ] Написать `scripts/graph_compare.py`
- [ ] Добавить `graph-compare` в `Makefile`
- [ ] Прогнать `make graph-compare` → проверить `data/graph/extraction-report.md`
- [ ] Заполнить раздел «Решения» в отчёте вручную

### Критерии готовности части Г

| # | Критерий |
|---|----------|
| 1 | `make graph-compare` завершается без ошибок |
| 2 | `data/graph/extraction-report.md` создан со всеми разделами |
| 3 | Keyword recall рассчитан для всех 29 seed-тем |
| 4 | По каждому расхождению принято явное решение: merge / keep / drop |

---

## Часть Д: Entity resolution и финализация

**Цель:** свести алиасы тем к каноническим узлам, устранить дубли, задокументировать все нестыковки в `data/graph/entity-resolution.md`; сделать `make graph-index` единым идемпотентным входом.

### Состав работ

#### Д-1. Алиас-мержинг (по решениям из части Г)

```cypher
// Шаблон: слияние авто-темы в seed-узел
MATCH (dup:Theme {id: $dupId}), (canon:Theme {id: $canonId})
MATCH (dup)<-[r:COVERS]-(c:Course)
MERGE (c)-[:COVERS {depth: r.depth}]->(canon)
WITH dup, canon
SET canon.aliases = canon.aliases + dup.aliases
DETACH DELETE dup;
```

- [x] Применить мержинг для всех пар `drop` из отчёта части Г
- [x] Дополнить `Theme.aliases` всеми найденными авто-вариантами (решения `merge`)

#### Д-2. `data/graph/entity-resolution.md`

Создать файл со структурой:

```markdown
# Entity Resolution — граф каталога курсов

## 1. Нестыковки данных (из analysis.md)

### 1.1 Дубль fullstack-программы
- Файлы: `ai-driven-fullstack.md` и `aidd-program.md`
- Решение: один узел `Course {id: "fullstack-aidd"}`, данные из `ai-driven-fullstack.md`
- Расхождение числа занятий (10 vs 12): задокументировано, использовано 10

### 1.2 Расхождение суммы комбо
- `ai-agents-combo.md` таблица: 134 960 ₽ (ошибка)
- Арифметика по файлам: 14990+39990+39990+44990 = 139 960 ₽
- Решение: `discountPct = 57`, цены из отдельных файлов

### 1.3 Slug-алиасы курсов
| catalog.json slug | Канонический id | Алиас |
|-------------------|-----------------|-------|
| vibe-coding-intensive | vibe-coding | ✅ |
| ai-coding-agents-base | agents | ✅ |
| ai-driven-fullstack | fullstack-aidd | ✅ |
| deep-agents-advanced | deep-agents | ✅ |

### 1.4 consultation из catalog.json
- Решение: не включать как Course — нет real_data-источника

## 2. Entity resolution по темам (из части Г)

| theme_id (dup) | canonical_id | действие | aliases добавлены |
|----------------|--------------|----------|-------------------|
| ... | ... | merge/drop | ... |

## 3. Финальный счётчик после resolution

| Метка | Кол-во |
|-------|--------|
| Course | 4 |
| Combo | 1 |
| Theme | N |
| Audience | 5 |
| Format | 6 |
| Level | 3 |
| **Итого** | **N+19** |
```

- [x] Создать `data/graph/entity-resolution.md` и заполнить по итогам частей А–Г

#### Д-3. Финализация пайплайна

- [x] Финальный прогон `make graph-qa` → орфанов 0, дублей 0
- [x] Обновить `Makefile` — единый вход:
  ```makefile
  graph-seed:
      docker exec -i neo4j cypher-shell \
        -u $(NEO4J_USER) -p $(NEO4J_PASSWORD) < scripts/seed.cypher

  graph-index: graph-seed graph-extract
  ```
- [x] Визуальная проверка в Neo4j Browser: `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100`

### Критерии готовности части Д (финальный DoD Task 05)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | `make graph-index` завершается без ошибок | exit 0 |
| 2 | Повторный запуск идемпотентен | счётчики узлов не меняются |
| 3 | `make graph-qa`: орфанных узлов 0 | запрос 1 |
| 4 | `make graph-qa`: очевидных дублей тем 0 | запрос 2 |
| 5 | Prerequisite-цепочка видна в Browser | `MATCH p=()-[:RECOMMENDED_BEFORE*]->() RETURN p` |
| 6 | `data/graph/entity-resolution.md` создан | все нестыковки задокументированы |
| 7 | `data/graph/extraction-report.md` создан | keyword-recall рассчитан |
| 8 | `data/graph/browser-guide.md` создан | starter queries рабочие |

---

## Открытые вопросы

- [x] ~~Рёбра `TAUGHT_BY` / узел `Expert`~~ — **убраны из схемы**. Данные по экспертам есть только в части файлов; связь не критична для GraphRAG-запросов. Решение: не включать.
- [ ] `deep-agents` → `dev` (`TARGETS`): явно не указано, но аудитория «ИТ-специалисты» включает dev.  
  → Решение: **включить** (`dev`) на основании «Разработчики, ИТ-специалисты, Tech Leads, AI-инженеры» из файла.
