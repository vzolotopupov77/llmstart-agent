# Журнал экспериментов (E-26)

> Одна строка = один эксперимент. Полный протокол — `exp-NNN-*.md` рядом.  
> Вспомогательные прогоны (smoke, failed retry) — в комментариях блока, не отдельной строкой.

---

## Sprint eval-01 — e2e baseline

| Дата | Эксперимент (протокол) | Гипотеза (кратко) | Датасет@версия | answer_correctness: было → стало | Guard просели? | Решение |
|------|------------------------|-------------------|----------------|----------------------------------|----------------|---------|
| 2026-06-14 | [exp-001-baseline-e2e-qa](exp-001-baseline-e2e-qa.md) | первый замер baseline sprint-01 | e2e-qa@v001 | — → 0.135 | — | ❌ superseded (битый judge) |
| 2026-06-15 | [exp-002-rebaseline-fixed-judge](exp-002-rebaseline-fixed-judge.md) | fix evaluators → достоверный baseline | e2e-qa@v001 | 0.135 → **0.527** | нет | ✅ baseline `…083100Z` |
| 2026-06-15 | [exp-003-candidate-rag-first-prompt](exp-003-candidate-rag-first-prompt.md) | RAG-first prompt v2 ↑ retrieval/correctness | e2e-qa@v001 | 0.527 → **0.631** | нет (↑) | 🔁 итерация #1, candidate зафиксирован |
| 2026-06-15 | [exp-004-candidate-generation-keypoints-v3](exp-004-candidate-generation-keypoints-v3.md) | prompt v3 ↑ key_points synthesis / mock-pay | e2e-qa@v001 | 0.631 → **0.615** | нет (↑ faith/task) | ❌ отклонён; iter #1 остаётся winning |
| 2026-06-15 | [exp-005-candidate-rag-first-prompt-v002](exp-005-candidate-rag-first-prompt-v002.md) | winning candidate rebaseline на sharpened v002 | e2e-qa@v002 | v001 0.631 → **0.662**¹ | нет | ✅ v002 baseline `…151141Z` |

¹ v001 vs v002 — разные criteria (E-16); Δ qualitative, не compare.

<!-- Вспомогательные runs (не эксперименты):
- 20260614T182021Z — smoke/partial baseline
- 20260615T094214Z — failed candidate (backend not restarted), см. exp-003
- 20260615T100746Z, 20260615T100916Z, 20260615T105250Z — smoke 1-item (sprint-eval-02 Task 05)
- 20260615T150903Z — failed v002 rebaseline (backend), см. exp-005
-->

---

## Sprint-08 — vector-db

| Дата | Run (суффикс) | Конфиг / retriever | Датасет@версия | answer_correctness | faithfulness | task_completion | Решение |
|------|---------------|--------------------|----------------|--------------------|--------------|-----------------|----|
| 2026-06-23 | `…20260623T143257Z` | vector-db-baseline / qdrant v1.18.2 | e2e-qa@v002 | 0.465 | 0.780 | 0.512 | ⚠️ error_rate 3.8% — дымовой прогон |
| 2026-06-24 | `…20260624T070642Z` | vector-db-baseline / qdrant v1.18.2 | e2e-qa@v002 | **0.588** | **0.873** | **0.585** | ✅ baseline зафиксирован |

<!-- Вспомогательные runs:
- 20260624T053801Z, 20260624T062728Z — failed (error_rate 1.0, backend down)
-->

---

## Sprint-09 — graphrag

| Дата | Эксперимент (протокол) | Гипотеза | Датасет@версия | answer_correctness | entity_recall | faithfulness | Решение |
|------|------------------------|----------|----------------|--------------------|---------------|--------------|---------|
| 2026-06-26 | [exp-006-graphrag-baseline](graphrag-baseline.md) | Qdrant-hybrid без графа: multi-hop ниже single-hop | multi-hop@v001 | **0.500** | **0.701** | **0.810** | ⚠️ superseded (MH-06/11 слабые) |
| 2026-06-26 | [exp-006-graphrag-baseline](graphrag-baseline.md) | global — ожидаем сильную просадку (−70%) | global@v001 | **0.200** | **0.292** | **0.767** | ✅ baseline зафиксирован |
| 2026-06-26 | [exp-006-graphrag-baseline](graphrag-baseline.md) | re-run с усиленным датасетом (MH-06/11 → 3+ узлов) | multi-hop@v002 | **0.383** | **0.618** | **0.749** | ✅ baseline v002 зафиксирован |
| 2026-06-29 | `graphrag-graph--multi-hop--f6c0db35--20260629T104727Z` | `graphrag-graph` | `graphrag/multi-hop/v002` | done |
| 2026-06-29 | `graphrag-graph--global--f6c0db35--20260629T110059Z` | `graphrag-graph` | `graphrag/global/v001` | done |
| 2026-06-29 | `graphrag-global-branch--global--f6c0db35--20260629T122642Z` | `graphrag-global-branch` | `graphrag/global/v001` | done |
| 2026-06-29 | `candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--f6c0db35--20260629T131340Z` | `candidate-rag-first-prompt-e2e-qa-v002` | `e2e/e2e-qa/v002` | done |
| 2026-06-29 | `graphrag-routing--multi-hop--f6c0db35--20260629T185053Z` | `graphrag-routing` | `graphrag/multi-hop/v002` | done |
| 2026-06-29 | `graphrag-routing--global--f6c0db35--20260629T185609Z` | `graphrag-routing` | `graphrag/global/v001` | done |
| 2026-06-29 | `graphrag-routing--e2e-qa--f6c0db35--20260629T185853Z` | `graphrag-routing` | `e2e/e2e-qa/v002` | done |
| 2026-06-29 | `graphrag-routing--e2e-qa--f6c0db35--20260629T195236Z` | `graphrag-routing` | `e2e/e2e-qa/v002` | done |
| 2026-06-29 | `graphrag-routing--e2e-qa--f6c0db35--20260629T200843Z` | `graphrag-routing` | `e2e/e2e-qa/v002` | done |
| 2026-06-29 | `graphrag-routing--e2e-qa--f6c0db35--20260629T202437Z` | `graphrag-routing` | `e2e/e2e-qa/v002` | done |
| 2026-06-29 | `graphrag-routing--e2e-qa--f6c0db35--20260629T203859Z` | `graphrag-routing` | `e2e/e2e-qa/v002` | done |
| 2026-06-30 | `graphrag-routing--e2e-regression--f6c0db35--20260630T080854Z` | `graphrag-routing` | `e2e/e2e-regression/v001` | done |
| 2026-06-30 | `graphrag-routing-v5--e2e-regression--f6c0db35--20260630T081402Z` | `graphrag-routing-v5` | `e2e/e2e-regression/v001` | done |
| 2026-06-30 | `graphrag-routing-v5--e2e-qa--f6c0db35--20260630T081949Z` | `graphrag-routing-v5` | `e2e/e2e-qa/v002` | done |
| 2026-06-30 | `graphrag-routing-v5--multi-hop--f6c0db35--20260630T084141Z` | `graphrag-routing-v5` | `graphrag/multi-hop/v002` | done |
| 2026-06-30 | `graphrag-routing-v5--global--f6c0db35--20260630T084838Z` | `graphrag-routing-v5` | `graphrag/global/v001` | done |
