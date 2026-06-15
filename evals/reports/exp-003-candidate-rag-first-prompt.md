# Эксперимент: candidate RAG-first prompt (v2) vs baseline

> **Дата:** 2026-06-15 · **Автор:** eval-agent · **Статус:** ✅ завершён
> **Журнал:** [`experiments-log.md`](experiments-log.md) (E-26)
> **Задача/спринт:** [sprint-eval-02 Task 04](../../../docs/sprints/eval/sprint-eval-02-eval-fix-loop/tasks/04-candidate-config/plan.md)

---

## Гипотеза / вопрос

9 retrieval-провалов в analyze: агент отвечает без `search_knowledge_base`. **v2 prompt** (RAG-first) заставит искать в KB перед фактическими ответами → рост `avg_answer_correctness` и `avg_faithfulness` без смены retrieval backend (E-7: только `prompt.name`).

## Конфигурация

| Параметр | Baseline | Candidate |
|---|---|---|
| Ран | `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` | `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` |
| config_id | `baseline-react-chroma` | `candidate-rag-first-prompt` |
| **Отличие (ровно одно, E-7)** | — | `prompt.name`: v1 → **v2** (RAG-first + mock payment) |
| Промпт | `agent-system-prompt-v1` | `agent-system-prompt-v2` |
| Retrieval | `chroma-embedded` | `chroma-embedded` |
| Датасет | `e2e/e2e-qa` **v001** | `e2e/e2e-qa` **v001** |
| git_sha | `476018c9` | `476018c9` |
| Judge | `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` |

Ссылки: [compare](compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md) · [analyze candidate](candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md) · [JSON baseline](runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json) · [JSON candidate](runs/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.json)

## Результаты

| Метрика | Роль | Порог | Baseline | Candidate | Δ |
|---|---|---|---|---|---|
| avg_answer_correctness | **главная** (E-18) | ≥ 0.75 | 0.527 | **0.631** | **+0.104** |
| avg_faithfulness | guard | ≥ 0.85 | 0.644 | 0.840 | +0.196 |
| avg_task_completion | guard | ≥ 0.80 | 0.573 | 0.612 | +0.039 |
| error_rate | guard | ≤ 0.05 | 0.000 | 0.000 | — |
| segment_match_rate | guard | 100% | 0.654 | 0.846 | +0.192 |

**Items (answer_correctness):** улучшились Δ≥0.05: **8** · регрессии Δ≤−0.05: **2** (#21, #3 — intensive schedule) · стабильны: 16.

**Регрессии:** #21 (0.40→0.00), #3 (0.40→0.20) — разбор: generation/retrieval на вопросах про расписание интенсива.

## Наблюдения / находки

- **Неудачный прогон** `…094214Z`: 100% `task_error` — backend не перезагружен после добавления `config_id`; отрицательный результат сохранён в JSON и журнале (не удалять, E-26).
- Agent output изменён в **25/26** items; score-only улучшений **0** — эффект от поведения агента, не variance судьи.
- Главная метрика **0.631** — всё ещё 🔴 vs порог 0.75; guard faithfulness 0.840 — ниже целевого 0.85, но вырос vs baseline.
- Langfuse UI: scores на Dataset Runs — Task 05 ✅; backfill исторических прогонов (`make eval-backfill-runs`).

## Решение

**🔁 Итерация (candidate зафиксирован, не production)**

- Candidate **принят для eval-fix траектории**: Δ главной **+0.104**, все guard-метрики ↑ или стабильны, `error_rate=0`.
- **Не деплоим** v2 в production: порог 0.75 не достигнут; 2 регрессии требуют разбора.
- Конфиг `candidate-rag-first-prompt` остаётся в `evals/configs/` как зафиксированный положительный результат итерации #1 (E-22).

Обоснование: compare рекомендует принять при росте главной без просадки guard; порог north-star не выполнен → следующая итерация (E-7: generation-only items или retrieval backend).

## Следующие шаги

- [ ] Итерация #2 eval-fix: generation-only провалы или retrieval (отдельный candidate, E-7)
- [x] Task 05: Langfuse dataset_run_items + scores в UI
- [ ] Расширить error analysis по regressed items #3, #21
