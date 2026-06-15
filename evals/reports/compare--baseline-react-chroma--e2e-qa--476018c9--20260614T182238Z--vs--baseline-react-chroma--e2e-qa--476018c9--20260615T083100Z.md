# Compare: `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` (A) vs `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` (B)

## Контекст

- **Run A:** `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z` · config `baseline-react-chroma` · dataset `e2e/e2e-qa/v001`
- **Run B:** `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` · config `baseline-react-chroma` · dataset `e2e/e2e-qa/v001`
- **Items:** 26 (aligned by index)

## ⚠️ Предупреждения

- Одинаковые config, git и judge: дельта scores скорее от evaluators или non-determinism агента/судьи — интерпретируй с осторожностью.

## Run-level metrics

| Метрика | A | B | Δ (B−A) |
|---------|---:|---:|--------:|
| `avg_answer_correctness` | 0.135 | 0.527 | +0.392 ↑ |
| `avg_faithfulness` | 0.608 | 0.644 | +0.037 ↑ |
| `avg_task_completion` | 0.438 | 0.573 | +0.135 ↑ |
| `error_rate` | 0.000 | 0.000 | +0.000 → |
| `segment_match_rate` | 0.654 | 0.654 | +0.000 → |

## Item-level: answer_correctness

- **Avg item Δ:** +0.392 · improved ≥0.05: 18 · regressed ≤-0.05: 1

### Top improved (B vs A)

- **#11** Δ=+1.00 (0.00 → 1.00): Хочу пройти обучение для себя, не от компании. Это к вам как к физлицу?
- **#22** Δ=+1.00 (0.00 → 1.00): Не могу найти на сайте расписание и формат — где это посмотреть?
- **#6** Δ=+0.80 (0.00 → 0.80): Нужно обучить 30 инженеров в компании, есть бюджет на корпоративный договор. Вы делаете такое?
- **#7** Δ=+0.80 (0.00 → 0.80): Уже делал RAG и tools в проде, хочу продвинутые агентные воронки. Сразу deep-agents?
- **#19** Δ=+0.80 (0.00 → 0.80): У вас несколько курсов — из какого вы могли бы показать описание программы? Меня интересует именно содержание, не отзыв…

### Top regressed (B vs A)

- **#14** Δ=-0.10 (0.50 → 0.40): ИТ разработка, в основном в области ИИ. Но код сам не пишу. Ближе к CPO. Хочу руку набить на инструменте, что-то сам пр…

## Факторный анализ

### Изменённые факторы

| Фактор | A | B | Изменился |
|--------|---|---|:---------:|
| Config | `baseline-react-chroma` | `baseline-react-chroma` | — |
| Git SHA | `476018c9` | `476018c9` | — |
| Agent model | `openai/gpt-4o-mini` | `openai/gpt-4o-mini` | — |
| Prompt | `agent-system-prompt-v1` | `agent-system-prompt-v1` | — |
| Retrieval | `chroma-embedded` | `chroma-embedded` | — |
| Judge | `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` | — |
| Dataset | `e2e/e2e-qa/v001` | `e2e/e2e-qa/v001` | — |

### Декомposition метрик (B − A)

- **`avg_answer_correctness`** (главная (E-18): покрытие key_points): Δ=+0.392 — улучшение.
- **`avg_faithfulness`** (guard: опора на retrieval context): Δ=+0.037 — улучшение.
- **`avg_task_completion`** (guard: выполнение задачи пользователя): Δ=+0.135 — улучшение.
- **`error_rate`** (infra: падения runner/API): Δ=+0.000 — стабильно.
- **`segment_match_rate`** (guard: B2C/B2B routing): Δ=+0.000 — стабильно.

### Интерпретация

- **Главная метрика (`avg_answer_correctness`):** рост **+0.392** (A → B).
- **Доминирующий фактор — методология оценки (evaluator/judge input):** 0 items улучшились при **том же** ответе; 9 items: ~0 → pass (artifact broken GEval).
- **Смешанный эффект:** 26 items с другим ответом агента (re-run non-determinism) — часть Δ не только от судьи.
- **Agent output:** идентичен в 0/26 items (0%), изменён в 26.

### Паттерны по items (answer_correctness)

- Улучшились (Δ≥0.05): **18** · ухудшились: **1** · стабильны: **7**
- Score-only улучшения (тот же ответ агента): **0**
- 0 → ≥0.5 (очистка judge artifact): **9**
- ≥0.5 → 0 (реgression / judge): **0**

### Рекомендации

1. **Не трактовать Δ как улучшение агента** — config/git/agent не менялись; зафиксируй **канонический baseline** (run B) для Task 04+.
2. **Следующий compare:** candidate (один параметр, E-7) vs канонический baseline на `e2e/e2e-qa/v001`.
3. **При candidate-прогоне** смотри: `avg_answer_correctness` ↑ при стабильном `error_rate` и без просадки `avg_faithfulness`.
4. **Eval-infra:** Langfuse dataset_run_items — scores в UI (sprint-eval-03+).
5. **Judge variance:** при пограничных Δ — повторный прогон или стабильный judge (gpt-4o-mini) для arbitration.

_Учитывай предупреждения в начале отчёта._

## Source files

- A: `evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json`
- B: `evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json`
