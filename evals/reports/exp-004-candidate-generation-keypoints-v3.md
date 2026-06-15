# Эксперимент: candidate generation/key_points prompt (v3) vs iter #1

> **Дата:** 2026-06-15 · **Автор:** eval-agent · **Статус:** ✅ завершён
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)
> **Задача/спринт:** [sprint-eval-03 Task 03](../../../docs/sprints/eval/sprint-eval-03-eval-fix-iteration-2/tasks/03-candidate-config/plan.md)

---

## Гипотеза / вопрос

После v2 (RAG-first) агент ищет в KB, но не синтезирует ответ по `answer_key_points` и путает интенсивы (#3, #21). **v3 prompt** добавит правила синтеза фактов из retrieval, disambiguation `vibe-coding-intensive` и усиленную воронку mock-payment → рост `avg_answer_correctness` и `avg_task_completion` (E-7: только `prompt.name` v2→v3).

## Конфигурация

| Параметр | Iter #1 (A) | Candidate #2 (B) |
|---|---|---|
| Ран | `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` | `candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z` |
| config_id | `candidate-rag-first-prompt` | `candidate-generation-keypoints-v3` |
| **Отличие (ровно одно, E-7)** | — | `prompt.name`: v2 → **v3** |
| Промпт | `agent-system-prompt-v2` | `agent-system-prompt-v3` |
| Retrieval | `chroma-embedded` | `chroma-embedded` |
| Датасет | `e2e/e2e-qa` **v001** | `e2e/e2e-qa` **v001** |
| git_sha | `476018c9` | `476018c9` |
| Judge | `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` |

Ссылки: [compare](compare--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z--vs--candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.md) · [analyze B](candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.md) · [JSON A](runs/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.json) · [JSON B](runs/candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.json)

## Результаты

| Метрика | Роль | Порог | Iter #1 (A) | Candidate #2 (B) | Δ |
|---|---|---|---|---|---|
| avg_answer_correctness | **главная** (E-18) | ≥ 0.75 | 0.631 | **0.615** | **-0.015** |
| avg_faithfulness | guard | ≥ 0.85 | 0.840 | 0.863 | +0.023 |
| avg_task_completion | guard | ≥ 0.80 | 0.612 | 0.631 | +0.019 |
| error_rate | guard | ≤ 0.05 | 0.000 | 0.000 | — |
| segment_match_rate | guard | 100% | 0.846 | 0.846 | — |

**Items (answer_correctness):** улучшились Δ≥0.05: **12** · регрессии Δ≤−0.05: **11** · стабильны: 3.

**Целевые items (гипотеза):**
- #3 (intensive schedule): 0.20 → **0.80** ✅
- #9 (mock payment): 0.00 → **0.60** ↑ (не полный pass)
- #21: не в top improved/regressed (стабилен или малый Δ)
- #2, #23: остаются generation-провалами в analyze B

**Крупные регрессии:** #10 (1.00→0.20), #22 (1.00→0.20), #24 (0.80→0.20), #12 (1.00→0.40), #16 (0.60→0.00).

## Наблюдения / находки

- Гипотеза **частично подтвердилась** на целевых items (#3, #9), но **главная метрика просела** из-за 11 регрессий — trade-off «больше фактов из KB» ломает простые FAQ-сценарии (#10, #22).
- Guard-метрики ↑: faithfulness 0.863 🟢 (впервые выше порога 0.85), task_completion +0.019.
- Agent output изменён в **26/26** items; score-only улучшений **0**.
- Langfuse linked: 26/26 items.

## Решение

**❌ Отклонить candidate #2 как winning config**

- Главная метрика **-0.015** vs iter #1 — не принимаем v3 в production и не заменяем `candidate-rag-first-prompt`.
- Итерация #2 eval-fix loop **зафиксирована** (E-22 → 2/2): измеримая дельта, compare, exp-report.
- **Winning config остаётся** `candidate-rag-first-prompt` (0.631).

Обоснование: compare рекомендует принять только при росте главной; guard улучшились, но north-star 0.75 не достигнут и главная ↓.

## Следующие шаги

- [ ] Task 04: rebaseline winning candidate на v002
- [ ] Разбор регрессий #10, #22 — возможно избыточные KB-факты в v3 prompt
