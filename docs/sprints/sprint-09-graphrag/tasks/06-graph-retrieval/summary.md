# Summary: Task 06 — graph-retrieval

> **План:** [plan.md](./plan.md)  
> **Дата закрытия:** 2026-06-29

---

## Что реализовано

### Retriever branches

- `mcp_server/mcp_server/retriever/neo4j_driver.py` — lifecycle Neo4j driver, `execute_read`.
- `mcp_server/mcp_server/retriever/graph_entities.py` — slug/entity resolution для graph-запросов.
- `mcp_server/mcp_server/retriever/graph.py` — `GraphRetriever`: Qdrant anchor → Cypher 1–2 hop.
- `mcp_server/mcp_server/retriever/global_agg.py` — `GlobalRetriever`: rule-based Cypher-агрегаты (`combo_hours`, `formats`, `catalog_summary`, …).
- `mcp_server/mcp_server/retriever/fusion.py` — RRF (k=60).
- `mcp_server/mcp_server/retriever/reranker.py` — CrossEncoder rerank (optional extra).
- `mcp_server/mcp_server/retriever/hybrid.py` — `HybridRetriever`: vector + graph → RRF → rerank.
- `mcp_server/mcp_server/retriever/factory.py` — `RETRIEVER_BRANCH=vector|graph|global|hybrid`.
- `mcp_server/mcp_server/retriever/base.py` — расширенный `KnowledgeChunk` (`branch`, `graph_template`).

### Конфиг и инфра

- `mcp_server/mcp_server/config.py`, `.env.example` — `RETRIEVER_BRANCH`, Neo4j, RRF, reranker.
- `scripts/seed.cypher` — `academicHours` на Course-узлах (GL-02).
- `Makefile` — `eval-graph-hybrid`, `eval-graph-global`.

### Тесты

- `mcp_server/tests/test_graph_retriever.py` — graph smoke + prerequisite chain.
- `mcp_server/tests/test_global_retriever.py` — global templates, `theme_courses`.
- `mcp_server/tests/test_rrf_rerank.py` — RRF scores, rerank skip без extra.
- `mcp_server/tests/conftest.py`, `test_retriever.py` — изоляция от `.env` (`branch=vector`).

### Eval

- `evals/configs/graphrag-graph.yaml` — hybrid branch.
- `evals/configs/graphrag-global-branch.yaml` — global branch smoke.
- `evals/reports/graphrag-graph.md` — сравнение с baseline по сегментам.

---

## Eval-результаты

| Run | Branch | Dataset | AC | Gate |
|---|---|---|---:|---|
| `graphrag-graph--multi-hop--…104727Z` | hybrid | multi-hop v002 (n=12) | **0.625** | ✅ > 0.383 |
| `graphrag-graph--global--…110059Z` | hybrid | global v001 (n=6) | 0.167 | ❌ (hybrid не вызывает GlobalRetriever) |
| `graphrag-global-branch--global--…122642Z` | global | global v001 (n=6) | **0.333** | ✅ > 0.200 |
| `candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--…131340Z` | hybrid | e2e-qa v002 (n=26, single-hop proxy) | **0.638** | ⚠️ gate 0.642 (−0.004) |

Baseline: [graphrag-baseline.md](../../../../../evals/reports/graphrag-baseline.md) — multi-hop 0.383, global 0.200, single-hop proxy 0.662.

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| `VectorCypherRetriever` из neo4j-graphrag | Custom Cypher + Qdrant anchor | External vectors в Qdrant; проще контролировать templates |
| Reranker всегда включён | Skip без `uv sync --extra reranker` | Optional extra; RRF работает без rerank |
| Global gate через hybrid e2e | Gate только на `RETRIEVER_BRANCH=global` | Hybrid не вызывает GlobalRetriever — routing в Task 08 |
| DoD #6 single-hop ≥ 0.642 | 0.638 | Пограничный miss; routing → Task 08 |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Heuristic global router (`_match_template`) | Без LLM-routing в scope Task 06; fallback = `catalog_summary` |
| RRF k=60, rerank top-10 | Баланс latency/quality; rerank optional |
| Отдельный eval-config для global branch | Изолированная валидация GlobalRetriever без agent routing |
| `sentence-transformers` как optional extra | Не раздуваем базовый образ MCP |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Windows: inline env в Makefile | Отдельные make-цели + `.env` RETRIEVER_BRANCH |
| Dataset path `multi-hop` vs `graphrag/multi-hop` | Fix в `run_utils.py` / `sync_datasets.py` |
| `make test-mcp` падал из `.env` hybrid | `conftest.py`: force `RETRIEVER_BRANCH=vector` |
| GL-04 e2e: `theme_courses` + `theme_id=None` | Задокументирован follow-up в `global_agg.py` |
| GL-02: 304 ч vs rubric 264 ч | Seed `academicHours` ≠ eval rubric — known gap |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Factory branches без правки agent | ✅ unit + smoke |
| 2 | Graph prerequisite chain (deep-agents) | ✅ tests + multi-hop eval 0.625 |
| 3 | Global GL-03 → 3 курса | ✅ unit `test_global_theme_courses`; e2e GL-03=0 (agent → mock catalog) |
| 4 | Hybrid RRF + rerank | ⚠️ RRF ✅; rerank skip без optional extra |
| 5 | multi-hop и global выше baseline | ✅ 0.625 / 0.333 (global branch) |
| 6 | Single-hop proxy ≥ baseline − 0.02 | ⚠️ **0.638** vs gate **0.642** — закрыто с оговоркой |
| 7 | `make test-mcp` зелёный | ✅ 48 passed |
| 8 | GL-01 known gap в отчёте | ✅ `graphrag-graph.md` |

**Согласование:** 2026-06-29 («ок» с оговорками DoD #4, #6).

---

## Что дальше

- **Task 07:** text2cypher + 4 guardrails.
- **Task 08:** agent routing — single-hop → vector, global → global branch; запрет mock catalog на GL-03/GL-06.
- **Follow-up:** fix `global_agg.py` theme router (GL-04); reconcile `academicHours` seed vs rubric; optional `uv sync --extra reranker`.

---

## Ссылки

- [graphrag-graph.md](../../../../../evals/reports/graphrag-graph.md)
- [graphrag-baseline.md](../../../../../evals/reports/graphrag-baseline.md)
- [ADR-0010 — GraphRAG](../../../../adrs/ADR-0010-graphrag.md)
- [Task 05 summary](../05-graph-indexing/summary.md)
