# Sprint eval-03: eval-fix-iteration-2

> **Версия roadmap:** v0.2 (roadmap-eval)
> **Roadmap:** [../../../roadmap-eval.md](../../../roadmap-eval.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../.methodology/eval/eval-methodology.md)
> **Статус:** ✅ Done
> **Открыт:** 2026-06-15 · **Закрыт:** 2026-06-15

---

## Цель спринта

Закрыть вторую итерацию eval-fix loop (E-22) на `e2e/e2e-qa`: структурный error analysis (К-3), точечные items из таксономии (К-4), candidate #2 с одним параметром (E-7), измеримая дельта vs итерация #1.

**Вход:** [exp-003](../../../../evals/reports/exp-003-candidate-rag-first-prompt.md) — `candidate-rag-first-prompt` **0.631** (+0.104 vs baseline 0.527); регрессии #3, #21 (расписание интенсива); north-star E-18 **0.75** не достигнут.

---

## DoD спринта

| # | Критерий | Способ проверки | ✅ |
|---|----------|-----------------|---|
| 1 | Error analysis: таксономия провалов по baseline + candidate runs (К-3) | `evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md` | ✅ Task 01 |
| 2 | Top-категории таксономии → items или правки в `e2e-qa` v002 (часть К-4; остальное — eval-04) | манифест v002 + `reviewed_by` | ✅ Task 02 |
| 3 | Candidate #2: ровно один параметр vs iter #1 (E-7) | `evals/configs/candidate-*.yaml` | ✅ Task 03 |
| 4 | Прогон + `compare` vs run итерации #1 (`…094647Z`) | compare report + JSON | ✅ Task 03 |
| 5 | E-22 закрыт: 2/2 итерации с зафиксированной дельтой | [experiments-log](../../../../evals/reports/experiments-log.md) exp-004 | ✅ Task 03 |
| 6 | exp-report с решением: принять / отклонить / следующая итерация | `evals/reports/exp-004-*.md` | ✅ Task 03 |

---

## Задачи

| # | Задача | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | Error analysis + таксономия провалов | ✅ | [plan](tasks/01-error-analysis/plan.md) | [summary](tasks/01-error-analysis/summary.md) |
| 02 | `e2e-qa` v002 — items из таксономии | ✅ | [plan](tasks/02-dataset-v002/plan.md) | [summary](tasks/02-dataset-v002/summary.md) |
| 03 | Candidate #2 — prompt v3 (generation/key_points) | ✅ | [plan](tasks/03-candidate-config/plan.md) | [summary](tasks/03-candidate-config/summary.md) |
| 04 | Candidate #1 re-baseline на `e2e-qa` v002 | ✅ | [plan](tasks/04-candidate-v1-v002-rebaseline/plan.md) | [summary](tasks/04-candidate-v1-v002-rebaseline/summary.md) |
| 05 | Закрытие спринта (README, roadmap) | ✅ | [plan](tasks/05-sprint-closure/plan.md) | [summary](tasks/05-sprint-closure/summary.md) |

> **Порядок:** 01 → 02 → 03 → **04** → 05. Task 04 — post-v3 rebaseline winning candidate на sharpened criteria (E-16: отдельный прогон, не compare v001↔v002).

---

## Ограничения

- Главная метрика — `avg_answer_correctness` на `e2e/e2e-qa` (E-18).
- Candidate #2 меняет **один** параметр (E-7): prompt **или** retrieval **или** judge — не комбинацию с iter #1.
- Baseline iter #1 (`candidate-rag-first-prompt`) **не переписываем**; новый конфиг — отдельный файл.
- Compare только на одной версии датасета (E-16); при v002 — отдельный compare-прогон.
- `funnel-to-lead`, component-датасеты — **eval-04**, не этот спринт.

---

## Кандидаты на iter #2 (из exp-003)

| Направление | Гипотеза | Риск |
|---|---|---|
| **Generation** | Точечный prompt для FAQ про расписание/интensive (#3, #21) | Новые регрессии на других items |
| **Retrieval** | Улучшение coverage KB (chunking, query rewrite) | Широкий blast radius; сложнее изолировать E-7 |

**Выбор (Task 03):** prompt v3 — generation/key_points по rec analyze #1+#3. Plan: [tasks/03-candidate-config/plan.md](tasks/03-candidate-config/plan.md).

---

## Итог

**E-22 закрыт (2/2):** iter #1 [exp-003](../../../../evals/reports/exp-003-candidate-rag-first-prompt.md) Δ **+0.104** (0.527→0.631); iter #2 [exp-004](../../../../evals/reports/exp-004-candidate-generation-keypoints-v3.md) Δ **−0.015** (0.631→0.615) — **v3 отклонён**.

| Артефакт | Результат |
|----------|-----------|
| Error analysis (К-3) | 7 категорий, P0–P2 — [report](../../../../evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md) |
| `e2e-qa` v002 (К-4) | 26 items, 7 criteria diff — [changelog](../../../../evals/datasets/e2e/e2e-qa/v002-changelog.md) |
| Winning agent (v001) | `candidate-rag-first-prompt` @ **0.631** |
| v002 baseline | `candidate-rag-first-prompt-e2e-qa-v002` @ **0.662** — [exp-005](../../../../evals/reports/exp-005-candidate-rag-first-prompt-v002.md) |
| North-star E-18 (0.75) | ❌ не достигнут |

**Решения:** v3 не принимаем; compare baseline для eval-04 — **v002** `…151141Z`; v001 iter #1 immutable для истории.

### Передано в eval-04

- Component-датасеты + `funnel-to-lead` (E-23) — [dataset-map](../../../eval/dataset-map.md)
- **P0:** tool-fix `e2e-qa-0017` (`confirm_payment`), generation (11 items), retrieval (5 items)
- Items таксономии, не вошедшие в v002 criteria
- Инфра: compact OTEL metadata (E-30), `load_dataset_context` v002 pin
