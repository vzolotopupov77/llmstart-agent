# Compare: `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` (A) vs `candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z` (B)

## Контекст

- **Run A:** `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` · config `candidate-rag-first-prompt` · dataset `e2e/e2e-qa/v001`
- **Run B:** `candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z` · config `candidate-generation-keypoints-v3` · dataset `e2e/e2e-qa/v001`
- **Items:** 26 (aligned by index)

## ⚠️ Предупреждения

- Разный config_id: A='candidate-rag-first-prompt', B='candidate-generation-keypoints-v3'

## Run-level metrics

| Метрика | A | B | Δ (B−A) |
|---------|---:|---:|--------:|
| `avg_answer_correctness` | 0.631 | 0.615 | -0.015 ↓ |
| `avg_faithfulness` | 0.840 | 0.863 | +0.024 ↑ |
| `avg_task_completion` | 0.612 | 0.631 | +0.019 ↑ |
| `error_rate` | 0.000 | 0.000 | +0.000 → |
| `segment_match_rate` | 0.846 | 0.846 | +0.000 → |

## Item-level: answer_correctness

- **Avg item Δ:** -0.015 · improved ≥0.05: 12 · regressed ≤-0.05: 11

### Top improved (B vs A)

- **#15** Δ=+0.80 (0.20 → 1.00): user: все таки хочется посмотреть на какую то часть ваших уроков, чтобы иметь представление, за что перечислять деньги …
- **#3** Δ=+0.60 (0.20 → 0.80): user: Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары? assistant: Интенсив vibe-coding-intensiv…
- **#9** Δ=+0.60 (0.00 → 0.60): Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **#1** Δ=+0.40 (0.40 → 0.80): user: Есть курс по AI-кодингу веб-проектов в записях? assistant: Отдельного веб-only курса нет; методика agents и fulls…
- **#18** Δ=+0.40 (0.40 → 0.80): Мне не подходит по формату — не смогу потратить рабочую пятницу днём на созвон. Есть вечерний поток?

### Top regressed (B vs A)

- **#10** Δ=-0.80 (1.00 → 0.20): Решил, беру agents. Как оплатить?
- **#22** Δ=-0.80 (1.00 → 0.20): Не могу найти на сайте расписание и формат — где это посмотреть?
- **#24** Δ=-0.60 (0.80 → 0.20): подскажите в каком формате проходят занятия?
- **#12** Δ=-0.60 (1.00 → 0.40): А по веб проектам — есть ли что-то для физлица, или только корпоративным?
- **#16** Δ=-0.60 (0.60 → 0.00): user: подскажите в каком формате проходят занятия? assistant: Курсы в комбо — онлайн-эфиры и задания; записи доступны. …

## Факторный анализ

### Изменённые факторы

| Фактор | A | B | Изменился |
|--------|---|---|:---------:|
| Config | `candidate-rag-first-prompt` | `candidate-generation-keypoints-v3` | ✅ |
| Git SHA | `476018c9` | `476018c9` | — |
| Agent model | `openai/gpt-4o-mini` | `openai/gpt-4o-mini` | — |
| Prompt | `agent-system-prompt-v2` | `agent-system-prompt-v3` | ✅ |
| Retrieval | `chroma-embedded` | `chroma-embedded` | — |
| Judge | `google/gemini-2.5-flash-lite` | `google/gemini-2.5-flash-lite` | — |
| Dataset | `e2e/e2e-qa/v001` | `e2e/e2e-qa/v001` | — |

### Декомposition метрик (B − A)

- **`avg_answer_correctness`** (главная (E-18): покрытие key_points): Δ=-0.015 — ухудшение.
- **`avg_faithfulness`** (guard: опора на retrieval context): Δ=+0.024 — улучшение.
- **`avg_task_completion`** (guard: выполнение задачи пользователя): Δ=+0.019 — улучшение.
- **`error_rate`** (infra: падения runner/API): Δ=+0.000 — стабильно.
- **`segment_match_rate`** (guard: B2C/B2B routing): Δ=+0.000 — стабильно.

### Интерпретация

- **Главная метрика (`avg_answer_correctness`):** падение **-0.015** (A → B).
- **Доминирующий фактор — изменение системы:** config_id, prompt. Δ отражает эффект candidate vs baseline (E-7).
- **Agent output:** идентичен в 0/26 items (0%), изменён в 26.

### Паттерны по items (answer_correctness)

- Улучшились (Δ≥0.05): **12** · ухудшились: **11** · стабильны: **3**
- Score-only улучшения (тот же ответ агента): **0**
- 0 → ≥0.5 (очистка judge artifact): **1**
- ≥0.5 → 0 (реgression / judge): **1**

### Рекомендации

1. **Принять candidate**, если главная метрика ↑, guard-метрики не просели, `error_rate` < 0.05.
2. **Разобрать regressed items** — retrieval vs generation (analyze report).
3. **Зафиксировать** winning config в `evals/configs/` и experiments-log.
4. **Judge variance:** при пограничных Δ — повторный прогон или стабильный judge (gpt-4o-mini) для arbitration.

_Учитывай предупреждения в начале отчёта._

## Source files

- A: `evals/reports/runs/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.json`
- B: `evals/reports/runs/candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.json`
