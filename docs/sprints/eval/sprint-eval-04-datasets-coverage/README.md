# Sprint eval-04: datasets-coverage

> **Версия roadmap:** v0.2 (roadmap-eval)
> **Roadmap:** [../../../roadmap-eval.md](../../../roadmap-eval.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../.methodology/eval/eval-methodology.md)
> **Статус:** 📋 Planned
> **Открыт:** — · **Закрыт:** —

---

## Цель спринта

Расширить покрытие eval-контура: component-датасеты по [dataset-map.md](../../../eval/dataset-map.md), включая `behavior/funnel-to-lead` через user simulation (E-23). Закрыть оставшиеся KR v0.2, не покрытые eval-03.

**Вход из [eval-03](../sprint-eval-03-eval-fix-iteration-2/README.md) (закрыт 2026-06-15):**

| Роль | Config / run | Датасет | `avg_answer_correctness` |
|------|----------------|---------|--------------------------|
| **Compare baseline (актуальный)** | `candidate-rag-first-prompt-e2e-qa-v002` · `…151141Z` | `e2e/e2e-qa` **v002** | **0.662** — [exp-005](../../../../evals/reports/exp-005-candidate-rag-first-prompt-v002.md) |
| Winning agent (история v001) | `candidate-rag-first-prompt` · `…094647Z` | v001 | 0.631 — [exp-003](../../../../evals/reports/exp-003-candidate-rag-first-prompt.md) |
| Таксономия провалов (К-3) | — | v001 analyze | [error-analysis](../../../../evals/reports/error-analysis-e2e-qa-v001-2026-06-15.md) |

**P0 из eval-03:** tool-fix `e2e-qa-0017` (`confirm_payment`), generation (11 items), retrieval (5 items) → целевые component-датасеты.

**Правило compare (E-16):** новые эксперименты на `e2e-qa` — только **v002** vs `…151141Z`; v001↔v002 не смешивать.

---

## DoD спринта

| # | Критерий | Способ проверки | ✅ |
|---|----------|-----------------|---|
| 1 | Манифесты v001 + sync для датасетов этапов 2–6 dataset-map | Langfuse + integrity-тесты | |
| 2 | `behavior/funnel-to-lead` + `scenarios.yaml`, user simulation (E-23) | прогон + scores | |
| 3 | Baseline-прогон хотя бы по 2 component-датасетам | JSON в `reports/runs/` | |
| 4 | Items из таксономии eval-03, не вошедшие в v002, размещены в целевых датасетах (К-4) | dataset-map coverage | |
| 5 | KR v0.2 `funnel-to-lead` закрыт | exp-report или sprint summary | |

---

## Датасеты (порядок dataset-map)

| Этап | Датасет | Группа |
|---|---|---|
| 2 | `rag/rag-retrieval` | rag |
| 3 | `behavior/segment-routing` | behavior |
| 4 | `edge/edge-cases` | edge |
| 5 | `behavior/tool-trajectory` | behavior |
| 6 | `rag/b2b-rag` | rag |
| 7 | `behavior/funnel-to-lead` + `scenarios.yaml` | behavior (E-23) |

---

## Задачи

*(детализация plan.md — при открытии спринта)*

| # | Задача (черновик) | Статус | Plan | Summary |
|---|--------|--------|------|---------|
| 01 | `rag/rag-retrieval` v001 — манифест + sync | 📋 | — | — |
| 02 | `behavior/segment-routing` + `edge/edge-cases` v001 | 📋 | — | — |
| 03 | `behavior/tool-trajectory` + `rag/b2b-rag` v001 | 📋 | — | — |
| 04 | `behavior/funnel-to-lead` + `scenarios.yaml` (E-23) | 📋 | — | — |
| 05 | Baseline-прогоны component + закрытие спринта | 📋 | — | — |

> **Порядок:** 01 → 02 → 03 → 04 → 05. Этапы по [dataset-map](../../../eval/dataset-map.md) §«Порядок внедрения».

---

## Ограничения

- Эталоны — human review gate (E-13) до sync.
- Пороги из [metrics-map.md](../../../eval/metrics-map.md) не менять подгонкой (E-20).
- North-star 0.75 — только для `e2e-qa`; component-датасеты — диагностика слоёв.

---

## Итог

*(заполняется после закрытия спринта)*
