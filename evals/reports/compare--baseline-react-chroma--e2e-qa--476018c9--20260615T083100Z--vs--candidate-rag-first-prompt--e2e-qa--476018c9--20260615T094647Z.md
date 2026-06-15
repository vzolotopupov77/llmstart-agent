# Compare: `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` (A) vs `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` (B)

## Контекст

- **Run A:** `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` · config `baseline-react-chroma` · dataset `e2e/e2e-qa/v001`
- **Run B:** `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` · config `candidate-rag-first-prompt` · dataset `e2e/e2e-qa/v001`
- **Items:** 26 (aligned by index)

## ⚠️ Предупреждения

- Разный config_id: A='baseline-react-chroma', B='candidate-rag-first-prompt'

## Run-level metrics

| Метрика | A | B | Δ (B−A) |
|---------|---:|---:|--------:|
| `avg_answer_correctness` | 0.527 | 0.631 | +0.104 ↑ |
| `avg_faithfulness` | 0.644 | 0.840 | +0.196 ↑ |
| `avg_task_completion` | 0.573 | 0.612 | +0.038 ↑ |
| `error_rate` | 0.000 | 0.000 | +0.000 → |
| `segment_match_rate` | 0.654 | 0.846 | +0.192 ↑ |

## Item-level: answer_correctness

- **Avg item Δ:** +0.104 · improved ≥0.05: 8 · regressed ≤-0.05: 2

### Top improved (B vs A)

- **#20** Δ=+1.00 (0.00 → 1.00): Чем комбо отличается от покупки курсов по отдельности?
- **#24** Δ=+0.80 (0.00 → 0.80): подскажите в каком формате проходят занятия?
- **#13** Δ=+0.50 (0.20 → 0.70): Стоит ли платить такие большие деньги за курс, если я не вижу, что именно внутри?
- **#16** Δ=+0.30 (0.30 → 0.60): user: подскажите в каком формате проходят занятия? assistant: Курсы в комбо — онлайн-эфиры и задания; записи доступны. …
- **#14** Δ=+0.30 (0.40 → 0.70): ИТ разработка, в основном в области ИИ. Но код сам не пишу. Ближе к CPO. Хочу руку набить на инструменте, что-то сам пр…

### Top regressed (B vs A)

- **#21** Δ=-0.40 (0.40 → 0.00): Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **#3** Δ=-0.20 (0.40 → 0.20): user: Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары? assistant: Интенсив vibe-coding-intensiv…

## Факторный анализ

### Изменённые факторы

| Фактор | A | B | Изменился |
|--------|---|---|:---------:|
| Config | `baseline-react-chroma` | `candidate-rag-first-prompt` | ✅ |
| Git SHA | `476018c9` | `476018c9` | — |
| Agent model | `openai/gpt-4o-mini` | `openai/gpt-4o-mini` | — |
| Prompt | `agent-system-prompt-v1` | `agent-system-prompt-v2` | ✅ |
| Retrieval | `chroma-embedded` | `chroma-embedded` | — |
| Judge | `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` | — |
| Dataset | `e2e/e2e-qa/v001` | `e2e/e2e-qa/v001` | — |

### Декомposition метрик (B − A)

- **`avg_answer_correctness`** (главная (E-18): покрытие key_points): Δ=+0.104 — улучшение.
- **`avg_faithfulness`** (guard: опора на retrieval context): Δ=+0.196 — улучшение.
- **`avg_task_completion`** (guard: выполнение задачи пользователя): Δ=+0.038 — улучшение.
- **`error_rate`** (infra: падения runner/API): Δ=+0.000 — стабильно.
- **`segment_match_rate`** (guard: B2C/B2B routing): Δ=+0.192 — улучшение.

### Интерпретация

- **Главная метрика (`avg_answer_correctness`):** рост **+0.104** (A → B).
- **Доминирующий фактор — изменение системы:** config_id, prompt. Δ отражает эффект candidate vs baseline (E-7).
- **Agent output:** идентичен в 1/26 items (4%), изменён в 25.

### Паттерны по items (answer_correctness)

- Улучшились (Δ≥0.05): **8** · ухудшились: **2** · стабильны: **16**
- Score-only улучшения (тот же ответ агента): **0**
- 0 → ≥0.5 (очистка judge artifact): **2**
- ≥0.5 → 0 (реgression / judge): **0**

### Рекомендации

1. **Принять candidate**, если главная метрика ↑, guard-метрики не просели, `error_rate` < 0.05.
2. **Разобрать regressed items** — retrieval vs generation (analyze report).
3. **Зафиксировать** winning config в `evals/configs/` и experiments-log.
4. **Eval-infra:** Langfuse dataset_run_items — scores в UI (sprint-eval-03+).
5. **Judge variance:** при пограничных Δ — повторный прогон или стабильный judge (gpt-4o-mini) для arbitration.

_Учитывай предупреждения в начале отчёта._

## Source files

- A: `evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json`
- B: `evals/reports/runs/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.json`
