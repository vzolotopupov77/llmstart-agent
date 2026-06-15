# Experiment report: baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z

## Контекст прогона

- **Config:** `baseline-react-chroma`
- **Dataset:** `e2e/e2e-qa/v001`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 554s
- **Git SHA:** `476018c9`
- **Source JSON:** `evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.135 | ≥0.75 | <0.60 | 🔴 |
| avg_faithfulness | 0.608 | ≥0.85 | <0.70 | 🔴 |
| avg_task_completion | 0.438 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🔴 (0.135 vs 0.75). Faithfulness 🔴, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.13 |
| `faithfulness` | 26 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 0.61 |
| `task_completion` | 26 | 0.00 | 0.00 | 0.20 | 0.70 | 1.00 | 0.44 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 11 items
- **generation:** 13 items
- **behavior:** 1 items
- **unknown:** 1 items

## Топ-5 худших items

### #1 — item index 1

- **Input:** user: Есть курс по AI-кодингу веб-проектов в записях? assistant: Отдельного веб-only курса нет; методика agents и ful...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent failed to address any of the evaluation steps. It did not create a payment link for agents as requested, nor did it confirm that the product recommendation remained unchanged. Consequently, neither of the key points specified in the input were addressed in the actual output.
- **Experiment trace (scores):** [083a56581892…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/083a565818923b979fe8f38dacfb0398)
- **Agent session (spans):** [d48088f2…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/d48088f2-0c0c-42ff-97cd-2b54736ed48d)
- **Span evidence (agent trace):**
Agent trace `e26d48acfeac2821a43f7666a17bbcbe`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.00, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The agent failed to address any of the evaluation steps. It did not create a payment link, nor did it confirm that the product recommendation was unchanged. The agent's response indicates it did not understand the user's request or the context of the conversation, and therefore could not fulfill the implicit requirements of the evaluation steps.
- **Experiment trace (scores):** [958741a8e4e2…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/958741a8e4e226cc14f3fb54a6509d08)
- **Agent session (spans):** [84091038…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/84091038-ca87-454f-9122-8c9b6923e3ee)
- **Span evidence (agent trace):**
Agent trace `418edbd22cf442d3517f1b5dc7b9849b`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 4

- **Input:** Есть ли рассрочка на комбо?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent did not create a payment link for agents as requested in step 1. The agent also did not address the product recommendation as per step 2. Consequently, neither of the key points from step 3 were met.
- **Experiment trace (scores):** [9f95cf8910fb…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/9f95cf8910fb0276a029e31e99ecd928)
- **Agent session (spans):** [4fc7dc86…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/4fc7dc86-548d-4513-b802-afddb9207051)
- **Span evidence (agent trace):**
Agent trace `674b80c8c93938bebb64fe5b6714e46b`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 9

- **Input:** Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=0
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** confirm_payment
- **Judge (answer_correctness):** The agent did not create a payment link for agents as requested in the input. The actual output indicates a failure to confirm payment due to no pending payment, which is contrary to the input's intent. Furthermore, the input did not contain a product recommendation to be checked for changes, making step 2 of the evaluation inapplicable. Consequently, neither of the key points from the input were 
- **Experiment trace (scores):** [4d16b5e75f05…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/4d16b5e75f0543b3732819bd1e6cd625)
- **Agent session (spans):** [c190da33…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/c190da33-4b90-4a0b-8d39-a7e8916d81a9)
- **Span evidence (agent trace):**
Agent trace `7339e57aff1d15cea1056d402aa849bd`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **confirm_payment**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 21

- **Input:** Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.00, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent did not create a payment link for agents, nor did it confirm that the product recommendation was unchanged. The actual output is a response to a question about seminar schedules, which is not related to the evaluation steps. Therefore, none of the evaluation criteria were met.
- **Experiment trace (scores):** [650ba2a0f60e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/650ba2a0f60e0e77b45f7002e7561dca)
- **Agent session (spans):** [390604bf…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/390604bf-1848-4053-92ee-02536cccde0f)
- **Span evidence (agent trace):**
Agent trace `2c615f67b5a6b6ba4f93ca2bdc9f0bce`:
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
4. **Infra/UI:** dataset_run_items не линкуются в Langfuse UI — scores на traces `experiment-item-run`; fix в sprint-eval-02.
5. **Judge:** часть variance от gemini-2.5-flash-lite JSON — рассмотреть judge gpt-4o-mini для стабильности.

## Что дальше

- Согласовать top-3 исправления → candidate config → compare vs baseline (v0.2).
- Задача sprint-01 закрывается после апрува этого отчёта.
