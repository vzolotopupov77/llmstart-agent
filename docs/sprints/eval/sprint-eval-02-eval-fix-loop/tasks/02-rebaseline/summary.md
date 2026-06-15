# Summary: Task 02 — Re-baseline + analyze

> **План:** [plan.md](./plan.md)
> **Дата:** 2026-06-15

---

## Что сделано

- Re-baseline: `make eval-experiment` (26 items, ~12 min)
- Analyze: [`evals/reports/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md`](../../../../../../evals/reports/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md)
- JSON: [`evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json`](../../../../../../evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json)
- `experiments-log.md` обновлён

**Тот же agent + config + dataset v001 + git sha** — отличие только evaluators (Task 01).

---

## Метрики: old vs new

| Run-level | Old (2026-06-14, broken GEval) | New (2026-06-15, fixed) | Δ |
|-----------|-------------------------------:|------------------------:|--:|
| avg_answer_correctness | 0.135 | **0.527** | +0.392 |
| avg_faithfulness | 0.608 | 0.644 | +0.036 |
| avg_task_completion | 0.438 | 0.573 | +0.135 |
| error_rate | 0.0 | 0.0 | — |
| segment_match_rate | 0.654 | 0.654 | — |

**Вывод:** скачок answer_correctness (+292%) — в основном починка судьи, не улучшение агента. Реальное качество агента ≈ **0.53** (🔴 vs порог 0.75) — это baseline для eval-fix loop.

**Item e2e-qa-0025 (сентябрь):** answer_correctness **0.40** (было 0.00), comment про временной барьер / KB — без «payment link».

---

## Таксономия (new)

retrieval 9 · generation 10 · behavior 1 · unknown 6

Топ провал: item #2 — timezone/SF (retrieval, без RAG tool).

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Run JSON 26 items, error_rate=0 | ✅ |
| 2 | Analyze report все разделы | ✅ |
| 3 | Таблица old vs new в summary | ✅ |
| 4 | ⛔ Пользователь видит новые метрики | ✅ 2026-06-15 |

---

## Что дальше

- **Task 03:** `compare_runs.py` — формализовать old vs new
- **Task 04:** candidate-конfig (prompt или retrieval) vs этот baseline
