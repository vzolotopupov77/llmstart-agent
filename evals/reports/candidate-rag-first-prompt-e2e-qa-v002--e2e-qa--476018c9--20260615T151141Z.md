# Experiment report: candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z

## Контекст прогона

- **Config:** `candidate-rag-first-prompt-e2e-qa-v002`
- **Dataset:** `e2e/e2e-qa/v002`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 538s
- **Git SHA:** `476018c9`
- **Source JSON:** `evals/reports/runs/candidate-rag-first-prompt-e2e-qa-v002--e2e-qa--476018c9--20260615T151141Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.662 | ≥0.75 | <0.60 | 🟡 |
| avg_faithfulness | 0.830 | ≥0.85 | <0.70 | 🟡 |
| avg_task_completion | 0.608 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🟡 (0.662 vs 0.75). Faithfulness 🟡, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.40 | 0.70 | 1.00 | 1.00 | 0.66 |
| `faithfulness` | 26 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.83 |
| `task_completion` | 26 | 0.10 | 0.20 | 0.70 | 0.90 | 1.00 | 0.61 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 5 items
- **generation:** 11 items
- **behavior:** 4 items
- **unknown:** 6 items

## Топ-5 худших items

### #1 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent failed to provide the time in MSK and did not comment on the user's timezone (SF). It also did not assess the suitability of the slot for travel or provide a fallback from the KB when the exact time was unknown, instead stating that information was unavailable.
- **Experiment trace (scores):** [8e5c218e40cf…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/8e5c218e40cf1e60d5f8306a75152eb4)
- **Agent session (spans):** [81578354…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/81578354-ff96-410d-a7d6-1da47ae9da05)
- **Span evidence (agent trace):**
Agent trace `1060ed6514bd2311553dbd3eab1f144b`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 23

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response fails to address the user's query about the duration of the classes, which was specified as a requirement (up to 2 hours). It also does not mention the availability of recordings or provide any guidance on potential time slots (evening/weekend), despite the user's direct question about timing.
- **Experiment trace (scores):** [614cdc2ed25f…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/614cdc2ed25f84099a50322df428cbfd)
- **Agent session (spans):** [282010a8…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/282010a8-a9b4-4ac1-8e9d-9bd07647acea)
- **Span evidence (agent trace):**
Agent trace `c31a61f0b41a2d90fdafdc522d4f3ce9`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 3

- **Input:** user: Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары? assistant: Интенсив vibe-coding-intens...
- **Scores:** correctness=0.10, faithfulness=0.57, task_completion=0.10, segment=1
- **Слой провала:** `retrieval` — faithfulness=0.57 или пустой retrieval при ожидании RAG
- **Tools:** list_b2c_products
- **Judge (answer_correctness):** The response fails to acknowledge that the initial offering (vibe-coding-intensive) is not suitable for the user (Step 3). It also does not offer an alternative with evening or weekend scheduling (Step 5) and instead proposes a different product (Cursor intensive) without addressing the user's objection to non-synchronous learning (Step 8). The response does not directly address the user's prefere
- **Experiment trace (scores):** [ab3780fc3ff5…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/ab3780fc3ff558b13b70570d2a4b9d93)
- **Agent session (spans):** [2ae0bfa0…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/2ae0bfa0-9393-4995-8016-45c235f48df6)
- **Span evidence (agent trace):**
Agent trace `9e8721d84d52d577e41e76f6f8a1ad64`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 21

- **Input:** Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **Scores:** correctness=0.20, faithfulness=1.00, task_completion=0.10, segment=1
- **Слой провала:** `generation` — answer_correctness=0.20 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response fails to recognize the user's request as being about the 'Cursor' intensive (step 3) and does not explicitly name the 'code vibe-coding-intensive' (step 6). While it acknowledges a lack of schedule information, it does not provide the required structure of seminars, practice, and chat support (step 7), instead offering a generic closing statement and failing to adhere to step 
- **Experiment trace (scores):** [a2c4ce4410a4…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/a2c4ce4410a4c2a23c14ab0d3e74b462)
- **Agent session (spans):** [3b5706ed…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/3b5706ed-98f0-46f3-9d72-1d41e62134a8)
- **Span evidence (agent trace):**
Agent trace `b5766baf17ecf436f11c9ba7ace006df`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **search_knowledge_base**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 15

- **Input:** user: все таки хочется посмотреть на какую то часть ваших уроков, чтобы иметь представление, за что перечислять деньг...
- **Scores:** correctness=0.20, faithfulness=1.00, task_completion=0.20, segment=0
- **Слой провала:** `generation` — answer_correctness=0.20 при faithfulness=1.00
- **Tools:** —
- **Judge (answer_correctness):** The agent's response fails to adhere to evaluation step 7, as it insists on asking about the user's goal ('ваша цель важна', 'Если вы поделитесь, что именно вас интересует') after the user explicitly stated 'зачем вам моя цель?'. This directly contradicts the instruction not to insist on the user's goal after a refusal. The response also does not focus on the value proposition as per step 4, nor d
- **Experiment trace (scores):** [3e71044d92f9…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/3e71044d92f902ee11c3d1f9ec437949)
- **Agent session (spans):** [c4b17596…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/c4b17596-b616-4b3d-abdd-fae1d96fc2de)
- **Span evidence (agent trace):**
Agent trace `07568dd61336a4a931ec6b94302d289f`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **list_b2c_products**
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
