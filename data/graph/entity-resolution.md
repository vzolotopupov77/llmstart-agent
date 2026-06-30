# Entity Resolution — граф каталога курсов

> Task 05 · Sprint 09 GraphRAG  
> Обновлено: 2026-06-28

Документ фиксирует принятые решения по нестыковкам данных и entity resolution после seed + авто-извлечения.

---

## 1. Нестыковки данных (из analysis.md)

### 1.1 Дубль fullstack-программы

| Атрибут | `ai-driven-fullstack.md` | `aidd-program.md` |
|---------|--------------------------|-------------------|
| Название | AI-driven Fullstack разработка | Fullstack AI-driven разработка |
| Цена | 39 990 ₽ | не указана |
| Занятий | 10 | 12 |
| Slug файла | `ai-driven-fullstack` | `aidd-program` |

**Решение:** один узел `Course {id: "fullstack-aidd"}`. Свойства из `ai-driven-fullstack.md`.  
Файл `aidd-program.md` маппится на тот же `course_id` в `graph_indexer.py` (`FILE_TO_COURSE`).  
При extraction COVERS создаются от `fullstack-aidd`, не от отдельного Course-узла.

### 1.2 Расхождение суммы комбо

| Источник | Значение |
|----------|----------|
| Таблица в `ai-agents-combo.md` | 134 960 ₽ (ошибка) |
| Арифметика по файлам курсов | **139 960 ₽** (14 990 + 39 990 + 39 990 + 44 990) |

**Решение:** `Combo.discountPct = 57`, цены из отдельных файлов курсов.

### 1.3 Slug-алиасы курсов

| catalog.json / файл | Канонический `Course.id` |
|---------------------|--------------------------|
| `vibe-coding-intensive` / `ai-coding-intensive-cursor.md` | `vibe-coding` |
| `ai-coding-agents-base.md` | `agents` |
| `ai-driven-fullstack` / `aidd-program.md` | `fullstack-aidd` |
| `deep-agents-advanced.md` | `deep-agents` |

Spurious Course-узлы, созданные pipeline, удаляются — допустимы только 4 seed id.

### 1.4 consultation из catalog.json

**Решение:** не включать как `Course` — нет `real_data`-источника.

---

## 2. Entity resolution по темам (из части Г)

Полная таблица решений по 29 seed-темам. Auto-дубликаты сливаются в канонический узел через Phase 3 (`apoc.refactor.mergeNodes`); aliases dup-узлов добавляются в `Theme.aliases`.

| theme_id | canonical_id | действие | aliases добавлены |
|----------|--------------|----------|-------------------|
| a2a-a2ui | a2a-a2ui | merge | да (auto-варианты из extraction) |
| agent-memory | agent-memory | merge | да |
| ai-driven-methodology | ai-driven-methodology | merge | да |
| cicd | cicd | merge | да |
| context-engineering | context-engineering | merge | да |
| dataset-management | dataset-management | merge | да |
| deep-agents-skills | deep-agents-skills | merge | да |
| docker-devops | docker-devops | merge | да |
| evaluation | evaluation | merge | да |
| fastapi-backend | fastapi-backend | merge | да |
| frontend-dev | frontend-dev | merge | да |
| graph-db | graph-db | merge | да |
| graphrag | graphrag | merge | да |
| hitl | hitl | merge | да |
| langchain-langgraph | langchain-langgraph | merge | да |
| llm-api | llm-api | merge | да |
| mcp | mcp | merge | да |
| multi-agent | multi-agent | merge | да |
| multimodal-rag | multimodal-rag | merge | да |
| multimodality | multimodality | merge | да |
| observability | observability | merge | да |
| postgresql | postgresql | merge | да |
| prompt-management | prompt-management | merge | да |
| rag-advanced | rag-advanced | merge | да |
| rag-basic | rag-basic | merge | да |
| react-agent | react-agent | merge | да |
| security-guardrails | security-guardrails | merge | да |
| tool-calling | tool-calling | keep | да (Phase 8: `THEME_ALIAS_PATCHES` — Tools, Tool Use, …) |
| vector-db | vector-db | merge | да |

Источник решений: `data/graph/extraction-report.md` §«Решения». Strict mode: 503 chunk-level Theme без alias-match удалены (drop).

### 2.1 Алиасы → один канонический узел (примеры)

| Алиасы (примеры) | Канонический `Theme.id` | Действие |
|------------------|-------------------------|----------|
| RAG, RAG-система, RAG pipeline, Retrieval-Augmented Generation | `rag-basic` | merge |
| Advanced RAG, Self-RAG, Agentic RAG | `rag-advanced` | merge |
| GraphRAG, граф + RAG | `graphrag` | merge |
| Neo4j, графовые БД | `graph-db` | merge (имя vs id — через alias index) |
| AI-driven методология, AIDD | `ai-driven-methodology` | merge |

Реализация: `build_theme_alias_index()` + `THEME_ALIAS_OVERRIDES` в `scripts/graph_common.py`; merge через `apoc.refactor.mergeNodes`.

### 2.2 prompt vs context engineering

| Алиас | Узел | Примечание |
|-------|------|------------|
| промпт-инжиниринг, prompt engineering | `llm-api` | В seed `llm-api.aliases` |
| context engineering, контекст-инжиниринг | `context-engineering` | Отдельный узел, не merge с llm-api |

### 2.3 Strict mode (`GRAPH_EXTRACT_STRICT=true`)

Auto-темы без совпадения в seed alias index **удаляются** (не создают шум в графе).  
При `false` — создаются с `source: "auto"` и slug из name.

---

## 3. Пайплайн resolution (graph_indexer.py)

```
SimpleKGPipeline (per .md file)
    → Phase 2: COVERS from Document→Chunk←Theme per FILE_TO_COURSE
    → Phase 3: merge auto Theme → seed canonical (apoc.refactor.mergeNodes)
    → Phase 4: delete Course nodes ∉ {vibe-coding, fullstack-aidd, agents, deep-agents}
    → Phase 5: remove lexical layer (Document/Chunk)
    → Phase 6: finalize REQUIRES — удалить LLM-рёбра, восстановить 12 seed-only
    → Phase 7: finalize catalog (strict mode)
    → Phase 8: dedupe COVERS, THEME_ALIAS_PATCHES, invariant checks
```

### 3.1 REQUIRES — только seed (до Task 06)

SimpleKGPipeline извлекает `Theme-[:REQUIRES]->Theme`, но LLM даёт дубли, self-loops и семантический шум (~79 лишних рёбер на прогон).

**Решение:** Phase 6 `_finalize_seed_requires()`:
1. Удаляет **все** `Theme-[:REQUIRES]->Theme`
2. Восстанавливает **12** authoritative пар из `SEED_THEME_REQUIRES` (`graph_common.py` = `seed.cypher`)
3. Помечает `r.source = 'seed'`

Auto-REQUIRES **не попадают** в production-граф до отдельного решения в Task 06 (GraphRAG retrieval).

---

## 4. Финальный счётчик (после seed, до/после extract)

| Метка | Seed | После extract |
|-------|------|---------------|
| Course | 4 | 4 (без spurious) |
| Combo | 1 | 1 |
| Theme | 29 | 29 (+ merged aliases, без дублей) |
| Audience | 5 | 5 |
| Format | 6 | 6 |
| Level | 3 | 3 |
| Document/Chunk | 0 | 0 (удалены Phase 5) |

### Extraction vs seed (2026-06-28)

| Метрика | Значение |
|---------|----------|
| Auto extract ops | 724 (221 merge + 503 drop) |
| Exact recall | 48% (14/29) |
| Semantic recall | 97% (28/29) |
| Proliferation | ~25× chunk-узлов на seed-тему |
| Не сопоставлено | `tool-calling` (seed сохранён) |
| REQUIRES | 12 (seed-only после Phase 6) |
| COVERS | 48 (seed + post-process) |


> Document/Chunk узлы создаются SimpleKGPipeline для трассировки extraction; не участвуют в GraphRAG retrieval (boundary rule ADR-0010).

---

## 5. Проверка

```bash
make graph-qa      # орфаны=0, similarity-дубли=0, pctWithCovers=100%
make graph-compare # diff + keyword-recall → data/graph/extraction-report.md
```
