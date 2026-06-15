# Experiment report: candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z

## Контекст прогона

- **Config:** `candidate-generation-keypoints-v3`
- **Dataset:** `e2e/e2e-qa/v001`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 626s
- **Git SHA:** `476018c9`
- **Source JSON:** `evals/reports/runs/candidate-generation-keypoints-v3--e2e-qa--476018c9--20260615T144346Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.615 | ≥0.75 | <0.60 | 🟡 |
| avg_faithfulness | 0.863 | ≥0.85 | <0.70 | 🟢 |
| avg_task_completion | 0.631 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🟡 (0.615 vs 0.75). Faithfulness 🟢, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.40 | 0.70 | 0.80 | 1.00 | 0.62 |
| `faithfulness` | 26 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.86 |
| `task_completion` | 26 | 0.10 | 0.40 | 0.70 | 0.70 | 1.00 | 0.63 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 4 items
- **generation:** 12 items
- **behavior:** 4 items
- **unknown:** 6 items

## Топ-5 худших items

### #1 — item index 23

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response does not address the user's request to know the time of the event, nor does it acknowledge the user's location in San Francisco. It fails to provide the time in MSK or comment on the suitability for the user's timezone (SF), and it does not assess if the slot is suitable for travel.
- **Experiment trace (scores):** [c97b798f126e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/c97b798f126eaca5ddb9efa16abecb20)
- **Agent session (spans):** [dde7301e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/dde7301e-71d9-475a-a2b5-06202d3ad5c5)
- **Span evidence (agent trace):**
Agent trace `8b5f5baa1ebefa43f3767f20a4fec1a3`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 16

- **Input:** Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.20, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The agent's response does not reflect the acceptance of a payment confirmation (mock) or confirm successful payment via a tool, as required by steps 3 and 4. Instead, it asks for personal information, deviating from the core requirements of the evaluation.
- **Experiment trace (scores):** [0817060c7420…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/0817060c74201f2ceb7826994845572c)
- **Agent session (spans):** [11b348ce…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/11b348ce-b91a-4524-ac1a-30254beebb39)
- **Span evidence (agent trace):**
Agent trace `9a4a6111fd8715507ec3559d0c5afff3`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 2

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.20, faithfulness=1.00, task_completion=0.30, segment=1
- **Слой провала:** `generation` — answer_correctness=0.20 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The response fails to address the user's core questions about the duration of the classes (step 3) and the specific timing of slots (step 4, step 5). While it correctly states that exact times are not yet determined, it doesn't mention the possibility of evening or weekend slots or the availability of recordings (step 6). The response also includes irrelevant information about the format of the cl
- **Experiment trace (scores):** [49d5eb31acd7…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/49d5eb31acd7649df2c6f1b810f8d4ce)
- **Agent session (spans):** [f871a7c5…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/f871a7c5-cdcf-4d38-98a7-a37fc2ba4c1f)
- **Span evidence (agent trace):**
Agent trace `c4b362b33d8eea3bae923e578ceee24f`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 10

- **Input:** user: все таки хочется посмотреть на какую то часть ваших уроков, чтобы иметь представление, за что перечислять деньг...
- **Scores:** correctness=0.20, faithfulness=1.00, task_completion=0.30, segment=0
- **Слой провала:** `generation` — answer_correctness=0.20 при faithfulness=1.00
- **Tools:** —
- **Judge (answer_correctness):** The response fails to adhere to step 7, as it insists on asking about the user's goal despite the user's explicit statement 'зачем вам моя цель?'. While it attempts to focus on value (step 4) by mentioning 'максимальную ценность от обучения', it does so in the context of pushing for the user's goal, which is a direct violation of the evaluation steps.
- **Experiment trace (scores):** [5d4aea9aa843…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/5d4aea9aa843ff069c3015ebe6daff76)
- **Agent session (spans):** [e4dac3ab…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/e4dac3ab-a968-4ca3-ad02-e457bbe3a278)
- **Span evidence (agent trace):**
Agent trace `0cf6b0e8adec4c60eb0440cf2a589918`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **list_b2c_products**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **LangGraph**
- `CHAIN` **model**

### #5 — item index 24

- **Input:** user: Есть курс по AI-кодингу веб-проектов в записях? assistant: Отдельного веб-only курса нет; методика agents и ful...
- **Scores:** correctness=0.20, faithfulness=1.00, task_completion=0.40, segment=1
- **Слой провала:** `generation` — answer_correctness=0.20 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The response fails to acknowledge the user's time barrier ('до 15 сентября очень загружен') and does not offer a next step or reminder as required by steps 3 and 6. It also doesn't propose an alternative flow or recording without losing interest (step 4). While it correctly avoids promising a specific date without KB (step 5), the overall alignment is very low due to missing key elements.
- **Experiment trace (scores):** [9b5c3116a745…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/9b5c3116a745a208325cacc642d40933)
- **Agent session (spans):** [ca95a390…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/ca95a390-93d5-419a-aa6f-9d8e932eda69)
- **Span evidence (agent trace):**
Agent trace `fdcf47082601ee74f9c24d54da9e9c9c`:
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
