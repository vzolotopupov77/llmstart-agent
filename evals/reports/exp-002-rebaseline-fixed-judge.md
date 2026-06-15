# Эксперимент: re-baseline после fix evaluators

> **Дата:** 2026-06-15 · **Автор:** eval-agent · **Статус:** ✅ завершён
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)
> **Задача/спринт:** [sprint-eval-02 Task 02](../../../docs/sprints/eval/sprint-eval-02-eval-fix-loop/tasks/02-rebaseline/plan.md)

---

## Гипотеза / вопрос

После fix GEval/task_completion (per-item `answer_key_points`) пересчитать baseline на том же agent+config+dataset: получим **достоверную** точку отсчёта для eval-fix loop (E-22), а не артефакт битого судьи.

## Конфигурация

| Параметр | Old (broken judge) | New (fixed evaluators) |
|---|---|---|
| Ран | `…20260614T182238Z` | `…20260615T083100Z` |
| config_id | `baseline-react-chroma` | `baseline-react-chroma` (тот же) |
| **Отличие (E-7)** | evaluators v0 | evaluators v1 (Task 01) |
| Промпт | `agent-system-prompt-v1` | `agent-system-prompt-v1` |
| Датасет | `e2e/e2e-qa` **v001** | `e2e/e2e-qa` **v001** |
| git_sha | `476018c9` | `476018c9` |

Ссылки: [compare old vs new](compare--baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z--vs--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md) · [analyze](baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.md) · [JSON](runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json)

## Результаты

| Метрика | Роль | Порог | Old | New | Δ |
|---|---|---|---|---|---|
| avg_answer_correctness | **главная** (E-18) | ≥ 0.75 | 0.135 | **0.527** | +0.392 |
| avg_faithfulness | guard | ≥ 0.85 | 0.608 | 0.644 | +0.037 |
| avg_task_completion | guard | ≥ 0.80 | 0.438 | 0.573 | +0.135 |
| error_rate | guard | ≤ 0.05 | 0.000 | 0.000 | — |
| segment_match_rate | guard | 100% | 0.654 | 0.654 | — |

**Items:** 26/26, error_rate=0. Скачок correctness — в основном fix судьи, не улучшение агента (compare warning: один config/git/judge).

## Наблюдения / находки

- Реальное качество агента ≈ **0.53** (🔴 vs порог 0.75) — канонический baseline для candidate-экспериментов.
- Таксономия: retrieval **9** · generation **10** · behavior **1** · unknown **6**.
- Топ провал: item #2 — timezone/SF (retrieval, агент без RAG tool) → гипотеза Task 04.

## Решение

**✅ Baseline зафиксирован** — канонический run: `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z`.

Обоснование: evaluators достоверны (Task 01 DoD); error_rate=0; old baseline (exp-001) superseded.

## Следующие шаги

- [x] compare_runs formalized (Task 03)
- [x] Candidate vs этот baseline (exp-003)
