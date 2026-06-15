# Эксперимент: baseline e2e-qa (sprint-eval-01)

> **Дата:** 2026-06-14 · **Автор:** eval-agent · **Статус:** ✅ завершён (superseded)
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)
> **Задача/спринт:** [sprint-eval-01 Task 05](../../../docs/sprints/eval/sprint-eval-01-vertical-slice/tasks/05-baseline-run/plan.md)

---

## Гипотеза / вопрос

Первый end-to-end замер агента на `e2e/e2e-qa/v001` (26 items): зафиксировать baseline scores и таксономию провалов для eval-fix loop.

## Конфигурация

| Параметр | Значение |
|---|---|
| Ран (канонический) | `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` |
| config_id | `baseline-react-chroma` |
| Промпт | `agent-system-prompt-v1` |
| Датасет | `e2e/e2e-qa` **v001** |
| git_sha | `476018c9` |
| Judge | `google/gemini-2.5-flash-lite` |

Ссылки: [analyze report](baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.md) · [JSON](runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json)

## Результаты

| Метрика | Роль | Порог | Значение |
|---|---|---|---|
| avg_answer_correctness | **главная** (E-18) | ≥ 0.75 | **0.135** 🔴 |
| avg_faithfulness | guard | ≥ 0.85 | 0.608 🔴 |
| avg_task_completion | guard | ≥ 0.80 | 0.438 🔴 |
| error_rate | guard | ≤ 0.05 | 0.000 ✅ |
| segment_match_rate | guard | 100% | 0.654 🔴 |

## Наблюдения / находки

- Низкий `avg_answer_correctness` (0.135) оказался артефактом бага GEval/task_completion (фиксированный текст «payment link» на все items) — см. [exp-002](exp-002-rebaseline-fixed-judge.md).
- Таксономия провалов всё же полезна для гипотез Task 04 (retrieval без KB).

## Решение

**❌ Superseded** — baseline не использовать для eval-fix; заменён re-baseline после Task 01 (exp-002).

Обоснование: метрики недостоверны из-за evaluator bug; run сохранён как исторический артефакт sprint-eval-01.

## Следующие шаги

- [x] Починить evaluators (sprint-eval-02 Task 01)
- [x] Re-baseline (exp-002)
