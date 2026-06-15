# Experiment report: candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z

## Контекст прогона

- **Config:** `candidate-rag-first-prompt`
- **Dataset:** `e2e/e2e-qa/v001`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 484s
- **Git SHA:** `476018c9`
- **Source JSON:** `evals/reports/runs/candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.631 | ≥0.75 | <0.60 | 🟡 |
| avg_faithfulness | 0.840 | ≥0.85 | <0.70 | 🟡 |
| avg_task_completion | 0.612 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🟡 (0.631 vs 0.75). Faithfulness 🟡, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.40 | 0.70 | 0.90 | 1.00 | 0.63 |
| `faithfulness` | 26 | 0.00 | 0.83 | 1.00 | 1.00 | 1.00 | 0.84 |
| `task_completion` | 26 | 0.00 | 0.40 | 0.60 | 0.90 | 1.00 | 0.61 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 5 items
- **generation:** 10 items
- **behavior:** 5 items
- **unknown:** 6 items

## Топ-5 худших items

### #1 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response does not address the user's request to know the time of the event, nor does it acknowledge the user's location in San Francisco. It fails to provide the requested time in MSK or comment on the suitability for the user's timezone (SF), and it does not assess if the event is suitable for travel.
- **Experiment trace (scores):** [d88ceaf68a8c…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/d88ceaf68a8ca9bd09876b29194d2793)
- **Agent session (spans):** [8d2c263f…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/8d2c263f-3aa8-49ea-99f9-7c68d1aeeee3)
- **Span evidence (agent trace):**
Agent trace `da260b06f0121b0e97cf677c77f4d99a`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 23

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response does not reflect any of the required information points: duration up to 2 hours, exact slot times may not be determined yet, evening or weekend slots as a guideline, and recordings will be available. The response explicitly states that specific data on time and duration is unavailable, failing to address any of the evaluation criteria.
- **Experiment trace (scores):** [9fe7fd743e78…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/9fe7fd743e78ec00444c5c10a7810449)
- **Agent session (spans):** [4fa7d973…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/4fa7d973-fa81-45e6-a1d7-44cc75b5258b)
- **Span evidence (agent trace):**
Agent trace `a2bc2d99241bd80c542e0ee174087bc6`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 9

- **Input:** Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.20, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The agent's response does not reflect the acceptance of a payment confirmation (mock) or confirm successful payment via a tool, as required by evaluation steps 3 and 4. Instead, it requests additional user information.
- **Experiment trace (scores):** [0d1873d71ef5…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/0d1873d71ef57e2b347500ecea6f27da)
- **Agent session (spans):** [287c19a8…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/287c19a8-03c0-4f91-8940-47732817b751)
- **Span evidence (agent trace):**
Agent trace `78ba416f24e139e0f436d1f009d8010f`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 21

- **Input:** Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.20, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent failed to recognize the user's request as being about the 'Cursor' intensive. It also did not provide the requested structure of calls, practice, and chat support, nor did it clarify that the request was about the vibe-coding-intensive.
- **Experiment trace (scores):** [be42ea42b454…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/be42ea42b45408bab646cc57c8252c17)
- **Agent session (spans):** [0816597e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/0816597e-18aa-4315-a972-a00bfeaa63ff)
- **Span evidence (agent trace):**
Agent trace `188b0ed6868b4844b41b32998d3a0918`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 3

- **Input:** user: Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары? assistant: Интенсив vibe-coding-intens...
- **Scores:** correctness=0.20, faithfulness=0.50, task_completion=0.00, segment=1
- **Слой провала:** `retrieval` — faithfulness=0.50 или пустой retrieval при ожидании RAG
- **Tools:** list_b2c_products
- **Judge (answer_correctness):** The response acknowledges the user's need for synchronous learning but fails to address several key requirements. It does not explicitly state that the previous intensive is unsuitable, nor does it offer an alternative with evening or weekend scheduling. Instead, it proposes a different intensive without confirming if it meets the user's preferred format (2-3 times a week after work) and incorrect
- **Experiment trace (scores):** [82ad099e1c36…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/82ad099e1c3617e308f8ee4634cabad5)
- **Agent session (spans):** [e145f01c…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/e145f01c-28be-4680-9682-110a856227bc)
- **Span evidence (agent trace):**
Agent trace `128ed9e0331a1fb7ecd659bb80495f29`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **tools**
- `TOOL` **search_knowledge_base**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

## Рекомендации (eval-fix, v0.2)

1. **Generation (приоритет):** низкий answer_correctness при нормальном faithfulness — улучшить prompt/guardrails (key_points не покрываются; проверить GEval comments).
2. **Retrieval:** items с faithfulness < 0.70 — проверить chunking/top-k и обязательность `search_knowledge_base` до ответа.
3. **Behavior:** segment_match / task_completion — multi-turn и objection handling.
4. **Infra/UI:** dataset_run_items не линкуются в Langfuse UI — scores на traces `experiment-item-run`; fix в sprint-eval-02.
5. **Judge:** часть variance от gemini-2.5-flash-lite JSON — рассмотреть judge gpt-4o-mini для стабильности.

## Что дальше

- Согласовать top-3 исправления → candidate config → compare vs baseline (v0.2).
- Задача sprint-01 закрывается после апрува этого отчёта.
