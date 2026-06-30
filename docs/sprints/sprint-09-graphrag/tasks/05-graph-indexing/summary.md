# Summary: Task 05 — graph-indexing

> **План:** [plan.md](./plan.md)  
> **Дата закрытия:** 2026-06-28

---

## Что реализовано

### Часть А — ручной seed

- `scripts/seed.cypher` — constraints, 48 узлов (29 Theme, 4 Course, …), 80 рёбер seed-слоя, MERGE-идемпотентность.
- `make graph-seed`, `make graph-index` в Makefile.

### Часть Б — инспекция

- `scripts/graph-qa.cypher` — 12 контрольных запросов (орфаны, дубли, COVERS, prerequisite, similarity, REQUIRES hygiene).
- `mcp_server/scripts/neo4j_qa.py`, `make graph-inspect`, `make graph-qa`.
- `data/graph/browser-guide.md` — Browser + starter queries.

### Часть В — ресёрч + авто-извлечение

- `docs/research/text-to-graph-tools.md` — 7 инструментов, выбор SimpleKGPipeline (не LLMGraphTransformer).
- `scripts/graph_indexer.py` — SimpleKGPipeline (`neo4j-graphrag`), strict schema Theme-only + post-process COVERS.
- `scripts/graph_common.py` — alias index, `FILE_TO_COURSE`, `SEED_THEME_REQUIRES`.
- `make graph-extract`, env: `GRAPH_EXTRACT_MODEL`, `GRAPH_EXTRACT_STRICT`.

### Часть Г — сравнение

- `scripts/graph_compare.py`, `make graph-compare`.
- `data/graph/extraction-report.md`, `data/graph/extraction-stats.json`.

### Часть Д — entity resolution + финализация

- `data/graph/entity-resolution.md` — нестыковки данных + таблица resolution по 29 seed-темам (§2).
- Phase 3: `apoc.refactor.mergeNodes` — 28 merge + 503 strict drop; aliases dup-узлов в canonical.
- Phase 6: `_finalize_seed_requires()` — LLM REQUIRES удалены, восстановлены 12 seed-пар.
- Phase 8: dedupe `COVERS`, `THEME_ALIAS_PATCHES` (`tool-calling`), invariant checks (orphans/loops).
- `THEME_ALIAS_PATCHES` в `graph_common.py` — Tools, Tool Use, function tools для `tool-calling`.

---

## Метрики extraction (финальный прогон)

| Метрика | Значение |
|---------|----------|
| Manual seed | 29 тем |
| Auto extract ops | 724 (221 merge + 503 drop) |
| Exact recall | 48% (14/29) |
| Semantic recall | 97% (28/29) |
| Не сопоставлено | `tool-calling` (keep + alias patch Phase 8) |
| REQUIRES после Phase 6 | 12 (seed-only) |
| COVERS | 48 |
| Corpus alias recall | 71% |

---

## Отклонения от плана

| План | Факт | Причина |
|------|------|---------|
| LLM извлекает Course + COVERS | Theme-only extraction; COVERS post-process | Constraint conflicts с seed Course |
| Phase 6 normalize REQUIRES endpoints | Seed-only wipe + restore 12 пар | LLM: 91 ребро с дублями/self-loops/шумом |
| graph-qa: 7 запросов | 12 запросов | +similarity, degree, COVERS %, REQUIRES QA |
| Keyword recall >100% в отчёте | Proliferation ~25× + corpus alias recall | Chunk-level дубли искажали метрику |

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Authoritative seed для Theme/Course | Ручной seed — source of truth |
| Strict mode: drop auto Theme без alias | Без шума в каталоге |
| REQUIRES только из seed (12) до Task 06 | LLM prerequisites ненадёжны |
| `aidd-program.md` → `fullstack-aidd` | Один Course-узел на fullstack |
| Combo 59 990 ₽, discountPct 57 | Арифметика по файлам курсов (139 960 ₽) |

---

## Итог DoD (части А–Д)

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `make graph-index` exit 0 | ✅ (пользователь) |
| 2 | Идемпотентность | ✅ (пользователь) |
| 3 | Орфаны 0 | ✅ `make graph-qa` |
| 4 | Дубли тем 0 | ✅ |
| 5 | Prerequisite-цепочка 3 пути | ✅ |
| 6 | `entity-resolution.md` + таблица 29 тем | ✅ |
| 7 | `extraction-report.md` | ✅ |
| 8 | `browser-guide.md` | ✅ |
| 9 | REQUIRES: 12, self-loops 0, dupes 0 | ✅ Phase 6 |
| 10 | Phase 8: dedupe COVERS, alias patches, invariants | ✅ |

**Согласование:** части А–Г — 2026-06-28; часть Д — 2026-06-28 («ок»).

---

## Что дальше

- **Task 06:** graph/global/hybrid retrieval; при необходимости — расширение REQUIRES из программ с human review.
- **`tool-calling`:** aliases дополнены Phase 8; при следующем extract — перепроверить semantic recall.
- **Task 07:** text2cypher guardrails.

---

## Ссылки

- [extraction-report.md](../../../../../data/graph/extraction-report.md)
- [entity-resolution.md](../../../../../data/graph/entity-resolution.md)
- [browser-guide.md](../../../../../data/graph/browser-guide.md)
- [text-to-graph-tools.md](../../../../../docs/research/text-to-graph-tools.md)
- [ADR-0010 — GraphRAG](../../../../adrs/ADR-0010-graphrag.md)
