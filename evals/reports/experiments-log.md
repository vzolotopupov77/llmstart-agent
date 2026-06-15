# Журнал экспериментов (E-26)

> Одна строка = один эксперимент. Полный протокол — `exp-NNN-*.md` рядом.
> Вспомогательные прогоны (smoke, failed retry) — в протоколе эксперимента, не отдельной строкой.

| Дата | Эксперимент (протокол) | Гипотеза (кратко) | Датасет@версия | Главная метрика: было → стало | Guard просели? | Решение |
|------|------------------------|-------------------|----------------|-------------------------------|----------------|---------|
| 2026-06-14 | [exp-001-baseline-e2e-qa](exp-001-baseline-e2e-qa.md) | первый замер baseline sprint-01 | e2e-qa@v001 | — → 0.135 | — | ❌ superseded (битый judge) |
| 2026-06-15 | [exp-002-rebaseline-fixed-judge](exp-002-rebaseline-fixed-judge.md) | fix evaluators → достоверный baseline | e2e-qa@v001 | 0.135 → **0.527** | нет | ✅ baseline `…083100Z` |
| 2026-06-15 | [exp-003-candidate-rag-first-prompt](exp-003-candidate-rag-first-prompt.md) | RAG-first prompt v2 ↑ retrieval/correctness | e2e-qa@v001 | 0.527 → **0.631** | нет (↑) | 🔁 итерация #1, candidate зафиксирован |
| 2026-06-15 | [exp-004-candidate-generation-keypoints-v3](exp-004-candidate-generation-keypoints-v3.md) | prompt v3 ↑ key_points synthesis / mock-pay | e2e-qa@v001 | 0.631 → **0.615** | нет (↑ faith/task) | ❌ отклонён; iter #1 остаётся winning |
| 2026-06-15 | [exp-005-candidate-rag-first-prompt-v002](exp-005-candidate-rag-first-prompt-v002.md) | winning candidate rebaseline на sharpened v002 | e2e-qa@v002 | v001 0.631 → **0.662**† | нет | ✅ v002 baseline `…151141Z` |

<!-- Вспомогательные runs (не эксперименты):
- 20260614T182021Z — smoke/partial baseline
- 20260615T094214Z — failed candidate (backend not restarted), см. exp-003
- 20260615T100746Z, 20260615T100916Z, 20260615T105250Z — smoke 1-item (sprint-eval-02 Task 05)
- 20260615T150903Z — failed v002 rebaseline (backend), см. exp-005
-->
† v001 vs v002 — разные criteria (E-16); Δ qualitative, не compare.
