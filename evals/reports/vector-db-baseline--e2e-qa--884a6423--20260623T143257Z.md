# Experiment report: vector-db-baseline--e2e-qa--884a6423--20260623T143257Z

## Контекст прогона

- **Config:** `vector-db-baseline`
- **Dataset:** `e2e/e2e-qa/v002`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 2609s
- **Git SHA:** `884a6423`
- **Source JSON:** `evals/reports/runs/vector-db-baseline--e2e-qa--884a6423--20260623T143257Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.465 | ≥0.75 | <0.60 | 🔴 |
| avg_faithfulness | 0.780 | ≥0.85 | <0.70 | 🟡 |
| avg_task_completion | 0.512 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.038 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🔴 (0.465 vs 0.75). Faithfulness 🟡, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.038).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.00 | 0.40 | 0.80 | 1.00 | 0.47 |
| `faithfulness` | 26 | 0.00 | 0.57 | 1.00 | 1.00 | 1.00 | 0.78 |
| `task_completion` | 26 | 0.00 | 0.20 | 0.60 | 0.90 | 1.00 | 0.51 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 7 items
- **generation:** 12 items
- **behavior:** 2 items
- **unknown:** 5 items

## Топ-5 худших items

### #1 — item index 23

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.00, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** No output
- **Experiment trace (scores):** [6714ca72d111…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/6714ca72d1113f1d311bc3185d587cf9)

### #2 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent failed to provide the time in MSK or comment on the user's timezone (SF) as required by steps 3 and 4. It also did not provide an approximation from the KB when the exact time was unknown, violating step 6 and 7. The response also incorrectly asks for clarification on the course, which is not relevant to the user's last query about time.
- **Experiment trace (scores):** [069908874acc…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/069908874accc2b713c2378b23885be9)
- **Agent session (spans):** [3dddb632…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/3dddb632-a468-412c-a46e-034efa834416)
- **Span evidence (agent trace):**
Agent trace `aee5448aa9377f4014d34d8c52bf4d3a`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 4

- **Input:** Есть ли рассрочка на комбо?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.20, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** Judge error: RetryError[<Future at 0x230564f3550 state=finished raised APIConnectionError>]
- **Experiment trace (scores):** [2296aff4606c…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/2296aff4606c53986fd26913b9b1602e)
- **Agent session (spans):** [9561dda0…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/9561dda0-7c14-422a-84cc-315d9dad4e4a)
- **Span evidence (agent trace):**
Agent trace `288f2759cc2e8a48157431f6ae35f1e7`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 17

- **Input:** Хочу иметь представление до оплаты, а не покупать и потом просить возврат. Почему нельзя посмотреть часть урока заранее?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.20, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** Judge error: RetryError[<Future at 0x2305659da50 state=finished raised APIConnectionError>]
- **Experiment trace (scores):** [f580ed18c739…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/f580ed18c739b81189ed3bcd2ebb73fb)
- **Agent session (spans):** [422cfe46…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/422cfe46-8882-4e32-a8fb-75b9728bbf6c)
- **Span evidence (agent trace):**
Agent trace `cb3ead6a044c0f93173a1c798fcd61fd`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 9

- **Input:** Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.40, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** Judge error: RetryError[<Future at 0x2305650b050 state=finished raised APIConnectionError>]
- **Experiment trace (scores):** [b2bbdb7ea588…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/b2bbdb7ea588d348ad979ec856a1a9d0)
- **Agent session (spans):** [f12bc008…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/f12bc008-5f3d-4e82-bc7f-289431eb8fc4)
- **Span evidence (agent trace):**
Agent trace `46557710cbababa60d4452bed0cf988b`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

## Рекомендации (eval-fix, v0.2)

1. **Generation (приоритет):** низкий answer_correctness при нормальном faithfulness — улучшить prompt/guardrails (key_points не покрываются; проверить GEval comments).
2. **Retrieval:** items с faithfulness < 0.70 — проверить chunking/top-k и обязательность `search_knowledge_base` до ответа.
3. **Behavior:** segment_match / task_completion — multi-turn и objection handling.
4. **Judge:** часть variance от gemini-2.5-flash-lite JSON — рассмотреть judge gpt-4o-mini для стабильности.

## Что дальше

- Согласовать top-3 исправления → candidate config → compare vs baseline (v0.2).
- Задача sprint-01 закрывается после апрува этого отчёта.
