# Summary: Task 01 — Error analysis + таксономия провалов

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-15

---

## Что реализовано

- [`evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md`](../../../../../../evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md) — полный К-3 отчёт: 7 категорий, 14 failing items, decide & act
- [`evals/reports/error-analysis-open-coding.md`](../../../../../../evals/reports/error-analysis-open-coding.md) — generated open-coding table (26 items)
- [`evals/scripts/build_error_analysis.py`](../../../../../../evals/scripts/build_error_analysis.py) — merge baseline/candidate JSON + join manifest по input
- [`evals/tests/test_error_analysis.py`](../../../../../../evals/tests/test_error_analysis.py) — smoke merge/delta

⛔ Таксономия и приоритеты P0–P2 апрувнуты пользователем — 2026-06-15.

---

## Отклонения от плана

- Join manifest↔run **по input**, не по index: порядок items в Langfuse run ≠ порядок YAML (зафиксировано в отчёте §7).
- 7 категорий вместо черновых 8: `RET-EMPTY` не выделен (единичные случаи внутри GEN-NO-DATA).

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Primary label только на candidate run | iter #1 — текущий лучший конфиг для приоритизации fix |
| Task 03 (prompt v3) validated, не model change | generation 10 items при faithfulness≥0.7; v2 уже снял retrieval-skip |
| P0: GEN-NO-DATA + PROD-MAP + BEH-FUNNEL → v3 | 54% items ниже 0.75; наибольшая плотность провалов |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Index YAML ≠ index run JSON | `_run_lookup_keys` + `_manifest_lookup_keys` (multi-turn last user) |
| Heuristic layer ≠ domain category | Две оси в отчёте §6 (e.g. e2e-qa-0017) |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Отчёт, 5 шагов К-3 | ✅ |
| 2 | 5–8 категорий + examples | ✅ 7 категорий |
| 3 | AC<0.75 промаркированы | ✅ 14/14 |
| 4 | Failure rate + baseline→candidate | ✅ §4 отчёта |
| 5 | Decide & act → Task 02/03 | ✅ P0–P2 |
| 6 | Task 03 hypothesis validated | ✅ prompt v3 |
| 7 | ⛔ Апрув таксономии | ✅ 2026-06-15 |
| — | pytest | ✅ 2 passed |

---

## Что дальше

- **Task 02:** `e2e-qa` v002 — items из §5 отчёта (0023, 0005, 0017, 0024 + G4.x)
- **Task 03–04:** candidate v3 + exp-004 после Task 02 (или waiving v002 по согласованию)

---

## Ссылки

- [exp-003 candidate iter #1](../../../../../../evals/reports/exp-003-candidate-rag-first-prompt.md)
- [Compare baseline vs candidate](../../../../../../evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md)
