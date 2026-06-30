# GraphRAG Graph Retrieval: hybrid + global branch vs baseline

> **Эксперимент:** Task 06 eval  
> **Judge:** google/gemini-2.5-flash-lite  
> **Baseline:** [graphrag-baseline.md](graphrag-baseline.md)

**Runs:**

| Config | Branch | Dataset | Run |
|---|---|---|---|
| `graphrag-graph` | `hybrid` | multi-hop v002 | `graphrag-graph--multi-hop--f6c0db35--20260629T104727Z` |
| `graphrag-graph` | `hybrid` | global v001 | `graphrag-graph--global--f6c0db35--20260629T110059Z` |
| `graphrag-global-branch` | `global` | global v001 | `graphrag-global-branch--global--f6c0db35--20260629T122642Z` |
| `candidate-rag-first-prompt-e2e-qa-v002` | `hybrid` | e2e-qa v002 (single-hop proxy) | `candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--f6c0db35--20260629T131340Z` |

---

## Конфигурация

| Параметр | Baseline | Hybrid | Global branch |
|---|---|---|---|
| Branch | `vector` | `hybrid` | `global` |
| Vector | Qdrant dense | Qdrant dense | — |
| Graph expansion | — | Neo4j anchor + traverse | — |
| Global aggregates | — | — | Neo4j rule-based Cypher |
| Fusion / rerank | — | RRF (k=60) + reranker | — |
| top_k | 5 | 5 | 5 |
| LLM | gpt-4o-mini · T=0.0 | то же | то же |

### Запуск

```bash
# Hybrid (multi-hop + end-to-end global через агента)
# .env: RETRIEVER_BRANCH=hybrid → restart backend
make eval-graph-hybrid DATASET=multi-hop
make eval-graph-hybrid DATASET=global

# Global branch smoke (изолированная валидация GlobalRetriever)
# .env: RETRIEVER_BRANCH=global → restart backend
make eval-graph-global DATASET=global
```

---

## Метрики по сегментам

### Multi-hop (`hybrid`, n=12)

| Метрика | Baseline | Hybrid | Δ | Gate |
|---|---:|---:|---:|---|
| answer_correctness | 0.383 | **0.625** | **+0.242 (+63%)** | ✅ > 0.383 |
| required_entity_recall@5 | 0.618 | **0.669** | +0.051 (+8%) | ✅ |
| faithfulness | 0.749 | 0.594 | −0.155 (−21%) | ⚠️ |

### Global — три прогона (n=6)

| Метрика | Baseline | Hybrid-on-global | Global branch | Gate (> 0.200) |
|---|---:|---:|---:|---|
| answer_correctness | 0.200 | 0.167 | **0.333** | hybrid ❌ · **global ✅** |
| required_entity_recall@5 | 0.292 | 0.347 | **0.389** | ✅ |
| faithfulness | 0.767 | 0.351 | **1.000** | hybrid ⚠️ · global ✅ |

**Timing:** multi-hop ~4.7 мин · hybrid-global ~2.9 мин · global-branch ~3.5 мин · single-hop proxy ~10.6 мин · error_rate 0/44.

### Single-hop proxy (`hybrid`, n=26)

| Метрика | Baseline | Hybrid | Δ | Gate (≥ 0.642) |
|---|---:|---:|---:|---|
| answer_correctness | 0.662 | **0.638** | −0.024 (−3.6%) | ⚠️ **−0.004** от gate |
| faithfulness | 0.749¹ | 0.608 | −0.141 | — |
| task_completion | — | 0.600 | — | — |

¹ baseline faithfulness — exp-005 aggregate; proxy run использует тот же judge и e2e-qa v002.

**Интерпретация:** пограничный miss (−0.004). Hybrid на single-hop не регрессирует катастрофически, но formal gate sprint DoD #3 (baseline ± 0.02) формально не пройден. Ожидаемое улучшение — Task 08 routing (single-hop → vector-only path).

### Target gates (plan Task 06)

| Gate | Статус |
|---|---|
| multi-hop answer_correctness > 0.383 (`hybrid`) | ✅ **0.625** |
| global answer_correctness > 0.200 (`global` branch) | ✅ **0.333** |
| global answer_correctness > 0.200 (`hybrid` e2e) | ❌ 0.167 — ожидаемо без routing |
| single-hop proxy ≥ baseline − 0.02 | ⚠️ **0.638** vs **0.642** — закрыто с оговоркой |

---

## Multi-hop — разбор (`hybrid`)

Graph-ветка даёт `[graph]`-чанки (`themePrereqs`, combo→course, prerequisites). 7/12 вопросов с AC ≥ 0.8.

**Лучшие:** путь к GraphRAG (1.0), Advanced RAG, HITL, GraphRAG prereqs.

**Провалы:** суммарная цена комбо (mock catalog), Observability depth, A2A/Deep Agents prereq chains.

**Faithfulness 0.594:** mock-цены, judge errors, agent over-generation.

---

## Global — hybrid e2e (ограничение)

`HybridRetriever` **не вызывает** `GlobalRetriever` — в retrieval_context нет `[global]`-чанков. Global gate через hybrid не достижим без Task 08 routing.

---

## Global branch smoke — разбор

`RETRIEVER_BRANCH=global` · config `graphrag-global-branch.yaml` · run `…122642Z`

### `[global]`-чанки в retrieval

| ID | Вопрос | AC | `[global]` template | Комментарий |
|---|---|---:|---|---|
| GL-01 | Авторы | 0.0 | `authors-gap` | gap-chunk корректен; Instructor node нет |
| GL-02 | Часы комбо | **0.2** | `combo_hours` | **304 ч** (4 курса из графа); baseline 104 ч |
| GL-03 | Менеджеры | 0.0 | — | агент → `list_b2c_products`, не KB |
| GL-04 | MCP курсы | 0.4 | `catalog_summary`¹ | router fallback; entity recall 1.0 |
| GL-05 | Форматы | **1.0** | `formats` | полное совпадение с эталоном |
| GL-06 | B2C count | 0.4 | — | агент → mock catalog (6 incl. consultation) |

¹ GL-04: heuristic router не сматчил `theme_courses` — отдал полный catalog snapshot.

### Ключевые выводы smoke

- **GlobalRetriever работает:** GL-02 aggregate и GL-05 formats подтверждены end-to-end.
- **Gate 0.333 > 0.200** — global-ветка закрывает sprint-метрику при правильном branch.
- **GL-03/GL-06** — провал agent routing (catalog вместо `search_knowledge_base`), не retriever.
- **GL-02 data gap:** граф суммирует 304 ч (vibe-coding=40 в seed); этalon eval — 264 ч — расхождение seed vs rubric.
- **GL-01** — known gap, не блокер.

---

## Сравнительная таблица реализаций

| Реализация | single-hop | multi-hop | global | Статус |
|---|---:|---:|---:|---|
| **Qdrant-hybrid** (baseline) | 0.662¹ | 0.383 | 0.200 | ✅ |
| **hybrid** branch | **0.638**² | **0.625** | 0.167 | ✅ multi-hop · ⚠️ single-hop |
| **global** branch | — | — | **0.333** | ✅ global smoke |
| `agent_router` | — | — | — | ⏳ Task 08 |

¹ single-hop baseline: прокси exp-005 (`e2e-qa` v002, n=26).

² single-hop hybrid: run `…131340Z`, `RETRIEVER_BRANCH=hybrid`, тот же dataset.

---

## Known gaps

- **GL-01:** Instructor node deferred (Task 05 backlog).
- **GL-02:** `academicHours` в seed ≠ rubric eval (304 vs 264).
- **GL-04 router:** theme query → fallback `catalog_summary`; доработать `_match_template`.
- **Hybrid ≠ Global e2e:** без Task 08 routing global-вопросы идут в vector/graph/mock catalog.
- **Mock catalog:** устаревшие цены, consultation как B2C-курс.

---

## Decision log

1. **Multi-hop gate ✅** — hybrid 0.625 (+63% vs baseline).

2. **Global gate ✅ (global branch smoke)** — 0.333 (+67% vs baseline 0.200). `GlobalRetriever` валидирован: `[global] combo_hours`, `[global] formats`.

3. **Hybrid-on-global ❌ (0.167)** — ожидаемо: без routing global aggregates не активируются.

4. **Task 08 обязателен** для production: global-вопросы → `search_knowledge_base` с `RETRIEVER_BRANCH=global` (или отдельный tool); запретить mock catalog на GL-03/GL-06.

5. **Single-hop proxy ⚠️ (0.638 vs 0.642)** — formal gate miss −0.004; Task 08 routing (vector path для single-hop) — основной путь закрытия sprint DoD #3.

6. **Follow-up в Task 07/08:** fix GL-04 theme router; reconcile `academicHours` seed vs eval rubric.
