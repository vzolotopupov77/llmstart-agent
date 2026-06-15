# Summary: Task 04 — Candidate RAG-first prompt

> **План:** [plan.md](./plan.md)
> **Дата:** 2026-06-15

---

## Что реализовано

- [`backend/app/agent/prompts.py`](../../../../../../backend/app/agent/prompts.py) — `agent-system-prompt-v2` (RAG-first + mock payment)
- [`backend/app/agent/config_registry.py`](../../../../../../backend/app/agent/config_registry.py) — `prompt.name` → `ReactRunner` (E-6)
- [`evals/configs/candidate-rag-first-prompt.yaml`](../../../../../../evals/configs/candidate-rag-first-prompt.yaml)
- Тесты: `test_prompts.py`, расширен `test_config_registry.py`

**Candidate run:** `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z`

**Compare:** [`evals/reports/compare--baseline-…083100Z--vs--candidate-…094647Z.md`](../../../../../../evals/reports/compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md)

---

## Δ vs канонический baseline (E-7: только `prompt.name`)

| Метрика | Baseline | Candidate v2 | Δ |
|---------|----------|--------------|--:|
| avg_answer_correctness | 0.527 | **0.631** | **+0.104** |
| avg_faithfulness | 0.644 | 0.840 | +0.196 |
| avg_task_completion | 0.573 | 0.612 | +0.039 |
| segment_match_rate | 0.654 | 0.846 | +0.192 |
| error_rate | 0 | 0 | — |

Ещё 🔴 vs порог 0.75, но **первая итерация eval-fix loop** с измеримой дельтой.

---

## Заметки

- Первый прогон candidate (094214Z) — 100% task_error: backend не был перезапущен (unknown config_id). Перезапуск → успешный прогон 094647Z.
- Следующая итерация: generation-only items (faithfulness=1, low correctness) или retrieval backend (E-7 отдельно).

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Только `prompt.name` отличается | ✅ |
| 2 | Прогон + compare | ✅ |
| 3 | Δ зафиксирован | ✅ +0.104 |
| 4 | ⛔ Пользователь видит compare | ✅ 2026-06-15 |

---

## Протокол (E-26)

- [exp-003-candidate-rag-first-prompt.md](../../../../../../evals/reports/exp-003-candidate-rag-first-prompt.md)
- Журнал: [experiments-log.md](../../../../../../evals/reports/experiments-log.md)

**Решение:** 🔁 итерация #1 — candidate зафиксирован (+0.104), production не деплоим (порог 0.75 не достигнут).
