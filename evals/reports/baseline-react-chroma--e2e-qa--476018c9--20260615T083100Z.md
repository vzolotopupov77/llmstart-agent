# Experiment report: baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z

## Контекст прогона

- **Config:** `baseline-react-chroma`
- **Dataset:** `e2e/e2e-qa/v001`
- **Judge:** `google/gemini-2.5-flash-lite`
- **Agent model:** `openai/gpt-4o-mini`
- **Items:** 26
- **Duration:** 709s
- **Git SHA:** `476018c9`
- **Source JSON:** `evals/reports/runs/baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z.json`

## Сводка vs пороги (metrics-map, e2e-qa)

| Метрика | Value | 🟢 порог | 🔴 порог | Статус |
|---------|------:|---------:|---------:|:------:|
| avg_answer_correctness | 0.527 | ≥0.75 | <0.60 | 🔴 |
| avg_faithfulness | 0.644 | ≥0.85 | <0.70 | 🔴 |
| avg_task_completion | 0.573 | ≥0.80 | <0.65 | 🔴 |
| error_rate | 0.000 | <0.05 | ≥0.10 | 🟢 |

**Вердикт baseline:** главная метрика 🔴 (0.527 vs 0.75). Faithfulness 🔴, task_completion 🔴. Инфрастабильность 🟢 (error_rate=0.000).

## Распределение item-level scores

| Метрика | n | min | p25 | p50 | p75 | max | avg |
|---------|--:|----:|----:|----:|----:|----:|----:|
| `answer_correctness` | 26 | 0.00 | 0.20 | 0.40 | 0.80 | 1.00 | 0.53 |
| `faithfulness` | 26 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 0.64 |
| `task_completion` | 26 | 0.00 | 0.30 | 0.70 | 0.70 | 1.00 | 0.57 |

## Таксономия провалов (топ-5 worst + общая)

- **retrieval:** 9 items
- **generation:** 10 items
- **behavior:** 1 items
- **unknown:** 6 items

## Топ-5 худших items

### #1 — item index 2

- **Input:** assistant: Новый поток интенсива по AI-driven разработке в Cursor — первый урок в выходной день. Подробности на llmst...
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.00, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The agent's response does not address the user's request to know the time of the event in MSK and its relevance to the user's location in San Francisco (SF). It fails to provide any time information or comment on the time zone difference, nor does it assess the suitability of the slot for travel.
- **Experiment trace (scores):** [b9fa53e449e1…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/b9fa53e449e18fc560379d49884dea0f)
- **Agent session (spans):** [88fd21b6…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/88fd21b6-5ec5-4961-b52f-375730b2c505)
- **Span evidence (agent trace):**
Agent trace `505c3dc28980d01f5d633fbeaafb0db7`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #2 — item index 9

- **Input:** Оплатил agents, вот чек не прикладываю — просто подтверждаю оплату.
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.00, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** confirm_payment
- **Judge (answer_correctness):** The agent's response does not reflect accepting the text confirmation of payment (mock) as requested in step 3. Instead, it states that payment could not be confirmed, which contradicts the user's input and the requirement to acknowledge the mock confirmation.
- **Experiment trace (scores):** [e85b04ae01db…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/e85b04ae01dbec4b741d95dc2ac0f3fc)
- **Agent session (spans):** [144c935e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/144c935e-f418-4cc4-88cf-6dd02ff0b291)
- **Span evidence (agent trace):**
Agent trace `1449a1c5bddb4e48e9d161b6a2782509`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `TOOL` **confirm_payment**
- `CHAIN` **tools**
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #3 — item index 24

- **Input:** подскажите в каком формате проходят занятия?
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.10, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The agent's response does not address any of the evaluation steps. It fails to mention the online format, practical assignments, the 'combo 2026' aspect, or the availability of recordings for self-paced learning. Instead, it asks for clarification, which is not relevant to the evaluation criteria.
- **Experiment trace (scores):** [628e1de61fbf…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/628e1de61fbfa76a593241e16a86d56e)
- **Agent session (spans):** [63bd3a6e…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/63bd3a6e-383f-4dfb-8801-46ee43c3fc0d)
- **Span evidence (agent trace):**
Agent trace `60e0e1619d291ed4e1a2ade73dc1e286`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #4 — item index 20

- **Input:** Чем комбо отличается от покупки курсов по отдельности?
- **Scores:** correctness=0.00, faithfulness=0.00, task_completion=0.20, segment=0
- **Слой провала:** `retrieval` — faithfulness=0.00 или пустой retrieval при ожидании RAG
- **Tools:** —
- **Judge (answer_correctness):** The response does not mention any of the four specific programs (agents, deep-agents, fullstack-aidd, vibe-coding-intensive) or the unified access to material updates, which are required by evaluation steps 3 and 4. It only provides general benefits of combo courses.
- **Experiment trace (scores):** [90533ee9ddf2…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/90533ee9ddf2f0918d01ea1309152272)
- **Agent session (spans):** [94634a20…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/94634a20-77bb-4159-b06f-1906e1d20f94)
- **Span evidence (agent trace):**
Agent trace `d4b560408a6163d1493c5a53f8530750`:
- `GENERATION` **ChatOpenAI**
- `CHAIN` **model**
- `CHAIN` **LangGraph**

### #5 — item index 23

- **Input:** подскажите в какое время будут проходить занятия и какая продолжительность?
- **Scores:** correctness=0.00, faithfulness=1.00, task_completion=0.20, segment=1
- **Слой провала:** `generation` — answer_correctness=0.00 при faithfulness=1.00
- **Tools:** search_knowledge_base
- **Judge (answer_correctness):** The agent's response does not reflect any of the required information: duration up to 2 hours, exact slot times not yet determined, evening/weekend slots as a guideline, or availability of recordings. Instead, it states that specific information about time and duration is unavailable.
- **Experiment trace (scores):** [2d5363aba260…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/trace/2d5363aba260fa0b74aac203cc284038)
- **Agent session (spans):** [b62b1496…](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/sessions/b62b1496-077f-4ccd-a172-3f32fbc1bf2d)
- **Span evidence (agent trace):**
Agent trace `2f17342d7ba0792358016614b4e6dc6c`:
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
