# Experiment report: vector-db-baseline--e2e-qa--884a6423--20260624T070642Z

## Контекст прогона

- **Config:** `vector-db-baseline`
- **Dataset:** `e2e/e2e-qa/v002`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 1122s
- **Git SHA:** `884a6423`
- **Source JSON:** `evals/reports/runs/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.588 | ≥0.75 | <0.60 | 🔴 |
| avg_faithfulness | 0.873 | ≥0.85 | <0.70 | 🟢 |
| avg_task_completion | 0.585 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🔴 (0.588 vs 0.75). Faithfulness 🟢, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.20 | 0.60 | 1.00 | 1.00 | 0.59 |
| `faithfulness` | 26 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.87 |
| `task_completion` | 26 | 0.10 | 0.30 | 0.60 | 0.70 | 1.00 | 0.58 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 4 items
- **generation:** 13 items
- **behavior:** 2 items
- **unknown:** 7 items

## Топ-5 худших items

### #1 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent failed to address the user's request for the time of the event, which was the focus of the last user query. It did not provide the time in MSK, nor did it comment on the user's timezone (SF) or assess the suitability of the slot for travel. The agent also did not provide any guidance from the KB when the exact time was unknown, instead asking for clarification.
- **Experiment trace (scores):** [23aada373dbd…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/23aada373dbdc995b577ae28c8716354)
- **Agent session (spans):** [daba3e7c…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/daba3e7c-d1f2-47e4-8586-6e4ff1d4d59c)
- **Span evidence (agent trace):**
Agent trace `b30483846a314b5b1e9373fa1e1a46a5`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 21

- **Input:** Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response fails to follow the evaluation steps. It does not recognize the request as being about the Cursor intensive (step 3), nor does it provide the required structure of calls, practice, and chat support (step 4). Instead, it gives a generic refusal about not having schedule data without describing the intensive's structure (step 8).
- **Experiment trace (scores):** [2928f3ca3bb3…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/2928f3ca3bb3056c8eef63bca536e076)
- **Agent session (spans):** [6251f005…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/6251f005-3992-4d26-adb0-51b8dfb6fc8a)
- **Span evidence (agent trace):**
Agent trace `73931b23f4172b6fde13bb6015298389`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **tools**
- `TOOL` **search_knowledge_base**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 23

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response fails to address the user's query about the duration of the classes, which was specified as a requirement (up to 2 hours). It also does not mention the availability of recordings or provide any guidance on potential time slots (evening/weekend), despite the user's direct question about timing.
- **Experiment trace (scores):** [864732c9827b…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/864732c9827b78ddf82bb90e24c7765a)
- **Agent session (spans):** [4d0e8dc0…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/4d0e8dc0-7d8f-4daf-9365-207da09237be)
- **Span evidence (agent trace):**
Agent trace `ee491401b1d36a0557234940a3d0f529`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 1

- **Input:** user: Есть курс по AI-кодингу веб-проектов в записях? assistant: Отдельного веб-only курса нет; методика agents и ful...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.60, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** Judge error: 'reason'
- **Experiment trace (scores):** [c00961170990…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/c00961170990947982c7725757df10b3)
- **Agent session (spans):** [22801013…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/22801013-16ee-4dfe-b3df-8afbf95b7445)
- **Span evidence (agent trace):**
Agent trace `dabfd8af4e64a63d98ae2c6909201234`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 25

- **Input:** Добрый день. Заинтересовал комбо курс. Скажите, какой формат у курсов? Можно будет проходить в свое удобное время? Ил...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=1.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** Judge error: RetryError[<Future at 0x1a1a8fd7550 state=finished raised APIConnectionError>]
- **Experiment trace (scores):** [b3512ee6f351…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/b3512ee6f351d35a5ba88dac1272159e)
- **Agent session (spans):** [21293dbe…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/21293dbe-c6bf-4a61-9e5d-1898771adec0)
- **Span evidence (agent trace):**
Agent trace `93f4bb2dd5f8723d7f92ea93bc2e1db2`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
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
