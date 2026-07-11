# Карта метрик — LLMStart Agent (llmstart.ru)

> **Создаётся:** задача 03 sprint-eval-01 · **Методология:** [.methodology/eval/eval-methodology.md](../../.methodology/eval/eval-methodology.md)
> **Входы:** [dataset-map.md](dataset-map.md) (✅ 2026-06-14; дополнена sprint-09), [metrics-guide.md](../../.methodology/eval/metrics-guide.md)
> **Статус:** ✅ утверждена 2026-06-14; дополнена sprint-09 / 2026-06-26
> **Последнее обновление:** 2026-06-26

**Judge-модель:** из run-config (`judge.name`, отдельно от модели агента, E-17). Пороги ниже — **до первого прогона** (E-20); изменение только решением с записью в секции «Пороги».

---

## Главная метрика и guard-метрики (E-18)

| Роль | Метрика (run-level) | Датасет | Зачем именно она |
|---|---|---|---|
| **Главная (north-star)** | `avg_answer_correctness` | `e2e/e2e-qa` | С-1: «агент ответил правильно по смыслу и фактам»; есть эталон (`answer_key_points`); совпадает с бизнес-вопросом качества pre-purchase |
| Guard | `avg_faithfulness` | `e2e/e2e-qa` | Главная может расти при галлюцинациях «красивого текста»; faithfulness ловит несоответствие retrieved-контексту |
| Guard | `avg_task_completion` | `e2e/e2e-qa` | Задача пользователя решена end-to-end (не только факты, но и полезность ответа) |
| Guard | `error_rate` | **все** датасеты | Run-level: доля items с `task_error=true` (E-19); инфра/LLM/tool failures не маскируются средним score |

**Правило решения:** конфиг **лучше** ⟺ `avg_answer_correctness` вырос при **не-просевших** guard (`avg_faithfulness`, `avg_task_completion`, `error_rate`).

**Сравнение конфигов (eval-01):** только на `e2e/e2e-qa` v001; component-датасеты — eval-02+.

---

## Метрики по датасетам

### e2e/e2e-qa

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `answer_correctness` | в (G-Eval) | DeepEval `GEval` — criteria из `expected_output.answer_key_points` (+ опц. `must_not`) | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | NUMERIC 0–1 | ≥ **0.75** / < **0.60** | Эталон — criteria, не литеральный ответ; GEval покрывает частичное выполнение key_points (аналог LLM-judge 0/0.5/1 из dataset-plan) |
| `faithfulness` | б | RAGAS `Faithfulness` | [Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) | item: trace | NUMERIC 0–1 | ≥ **0.85** / < **0.70** | Reference-free guard против галлюцинаций (категория B) |
| `segment_match` | а | Детерминированный `exact_match` поля `expected_output.segment` | metrics-guide §A | item: trace | BOOLEAN | **100%** / < **95%** | P0 G7; дешёвая проверка до judge |
| `task_error` | а | Детерминированный флаг исключения прогона | metrics-guide §A, E-19 | item: trace | BOOLEAN | **0%** items / > **5%** | Обязательная item-level метрика |

**Run-level агрегаты:** `avg_answer_correctness`, `avg_faithfulness`, `avg_task_completion` (DeepEval [TaskCompletionMetric](https://deepeval.com/docs/metrics-task-completion), subset e2e ≥ **0.80** / < **0.65**), `error_rate` (< **0.05** / ≥ **0.10**).

**Особые режимы:** multi-turn items — один trace на item; TaskCompletion читает весь trace.

---

### rag/rag-retrieval

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `answer_correctness` | в | DeepEval `GEval` по `answer_key_points` | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | NUMERIC 0–1 | ≥ **0.80** / < **0.65** | Изолированный слой generation+retrieval по FAQ (G1 P0) |
| `faithfulness` | б | RAGAS `Faithfulness` | [Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) | item: trace | NUMERIC 0–1 | ≥ **0.90** / < **0.75** | FAQ-датасет: фактические ошибки критичнее тона |
| `search_tool_used` | а | Детерминированно: `search_knowledge_base` в trace, если `expected_output.tools` содержит search | metrics-guide §A | item: span (tool) | BOOLEAN | ≥ **95%** когда ожидался / — | Диагностика «ответ без RAG» |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `avg_answer_correctness`, `avg_faithfulness`, `error_rate`.

**Отложено (dataset-map):** `context_recall`, `context_precision` — нет `chunk_ids` в эталоне; добавить в metrics-map v2 после фиксации chunking.

**Особые режимы:** faithfulness на trace; опционально дублировать score на span retrieval при появлении named span в трейсе.

---

### rag/b2b-rag

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `answer_correctness` | в | DeepEval `GEval` по `answer_key_points` | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | NUMERIC 0–1 | ≥ **0.75** / < **0.60** | С-6; B2B факты из KB |
| `segment_match` | а | `exact_match` → `segment: b2b` | metrics-guide §A | item: trace | BOOLEAN | **100%** / < **100%** | Не смешивать с B2C checkout (G7.2) |
| `b2c_checkout_must_not` | в | DeepEval `GEval` criteria: «не предложил B2C checkout команде / счёт на 20 человек через create_payment_link» | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | BOOLEAN | **100%** / любой fail 🔴 | Жёсткое бизнес-правило из dataset-map `must_not` |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `avg_answer_correctness`, `error_rate`; segment_match aggregate **100%**.

---

### behavior/segment-routing

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `segment_match` | а | `exact_match` `expected_output.segment` | metrics-guide §A | item: trace | BOOLEAN | **100%** / < **95%** | G7 P0; детерминированная категория A — приоритет над judge |
| `routing_quality` | в | DeepEval `GEval`: «ответ использует правильную аудиторию KB и не задаёт B2B-вопросы B2C-клиенту (и наоборот)» по `answer_key_points` | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | NUMERIC 0–1 | ≥ **0.85** / < **0.70** | Тон маршрутизации (С-5, С-7) |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `segment_match_rate` (доля 1.0), `avg_routing_quality`, `error_rate`.

---

### behavior/tool-trajectory

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `tool_correctness` | б (C) | DeepEval `ToolCorrectnessMetric`, режим **IN_ORDER** (E-21) | [ToolCorrectness](https://deepeval.com/docs/metrics-tool-correctness) | item: trace | NUMERIC 0–1 | ≥ **0.90** / < **0.75** | G8–G9; сравнение `tools_called` vs `expected_output.tools` |
| `argument_match` | а | Детерминированное сравнение args ключевых полей (`product_code`, `audience`) | metrics-guide §A | item: span (tool) | NUMERIC 0–1 | ≥ **0.95** / < **0.80** | Args важнее имён (Sharp edges OSS tool calling) |
| `executed_tools_count` | а | COUNT observations type=tool; alert if expected ≥1 and count=0 | metrics-guide §A | item: trace | NUMERIC | expected match / **0 при expected≥1** 🔴 | Диагностика сломанного tool calling |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `avg_tool_correctness`, `error_rate`.

**Особые режимы:** **IN_ORDER** — лишний легитимный tool не фейлит; **EXACT** не используем без ADR.

---

### behavior/funnel-to-lead

> **Статус датасета:** sprint eval-02 / v0.2 (user simulation, E-23). Пороги зафиксированы заранее, прогон — позже.

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `funnel_state_check` | а | `state_check`: запись в `data/leads.txt` + наличие payment URL в trace при сценарии оплаты | metrics-guide §A | item: trace | BOOLEAN | ≥ **0.85** / < **0.70** | С-2→С-3 детерминированный успех |
| `task_completion` | б | DeepEval `TaskCompletionMetric` | [TaskCompletion](https://deepeval.com/docs/metrics-task-completion) | item: trace | NUMERIC 0–1 | ≥ **0.80** / < **0.65** | Multi-turn: задача решена целиком |
| `tool_correctness` | б | `ToolCorrectnessMetric` IN_ORDER на цепочку create_payment_link → confirm_payment → save_lead | [ToolCorrectness](https://deepeval.com/docs/metrics-tool-correctness) | item: trace | NUMERIC 0–1 | ≥ **0.85** / < **0.70** | Поведенческая траектория воронки |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `funnel_success_rate`, `error_rate`.

---

### edge/edge-cases

| Метрика | Ступень E-17 | Фреймворк / точное имя | Ссылка | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|---|
| `must_not_violation` | в | DeepEval `GEval` criteria из `expected_output.must_not` (демо-URL, давление на «цель», выдуманные preview) | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | BOOLEAN | **100% pass** / любой fail 🔴 | G4 политика «публичного демо нет» — жёсткий guard |
| `answer_correctness` | в | DeepEval `GEval` по `answer_key_points` | [GEval](https://deepeval.com/docs/metrics-llm-evals) | item: trace | NUMERIC 0–1 | ≥ **0.70** / < **0.55** | G3–G4: тон и содержание; порог ниже e2e (сложнее кейсы) |
| `faithfulness` | б | RAGAS `Faithfulness` | [Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) | item: trace | NUMERIC 0–1 | ≥ **0.85** / < **0.70** | Senior-skeptic: не выдумывать факты про демо/возврат |
| `task_error` | а | см. выше | — | item: trace | BOOLEAN | 0% / >5% | E-19 |

**Run-level:** `must_not_pass_rate` (**100%**), `avg_answer_correctness`, `error_rate`.

---

### graphrag/multi-hop · graphrag/global

> **Реализовано:** sprint-09, задача 02 · **Baseline зафиксирован:** 2026-06-26  
> **Конфиг:** `evals/configs/graphrag-baseline.yaml` · **Evaluators:** `get_graphrag_evaluators()` в `evals/scripts/evaluators.py`

| Метрика | Ступень E-17 | Фреймворк / точное имя | Уровень | Тип score | Порог 🟢 / 🔴 | Обоснование |
|---|---|---|---|---|---|---|
| `answer_correctness` | в (G-Eval) | DeepEval `GEval` по `expected_output.reference_answer` | item: trace | NUMERIC 0–1 | ≥ **0.65** / < **0.50** | Главная метрика сегмента; эталон — полный reference_answer из KB |
| `required_entity_recall` | а | Детерминированный: доля `required_entities` из `expected_output`, найденных в тексте ответа (substring match) | item: trace | NUMERIC 0–1 | ≥ **0.70** / < **0.50** | Retrieval-guard: граф должен находить нужные сущности (коды курсов, имена); независим от judge |
| `faithfulness` | б | RAGAS `Faithfulness` | item: trace | NUMERIC 0–1 | ≥ **0.75** / < **0.60** | Guard: ответ не противоречит retrieved-контексту; порог ниже e2e (multi-hop может частично опираться на параметризованные данные) |
| `task_error` | а | Детерминированный флаг исключения | item: trace | BOOLEAN | **0%** / > **5%** | E-19 |

**Run-level агрегаты:**

| Метрика | Описание | Реализация |
|---|---|---|
| `error_rate` | Доля task_error items | `evals/scripts/evaluators.py` |
| `avg_answer_correctness` | Средняя по всем items прогона | — |
| `avg_required_entity_recall` | Средняя recall по entities | — |
| `avg_faithfulness` | Средняя faithfulness | — |
| `avg_answer_correctness_{segment}` | Средняя answer_correctness, сгруппированная по `graphrag_type` из Langfuse-метаданных (`gr_type`) | `avg_answer_correctness_by_graphrag_type()` — возвращает список Evaluation |

**Baseline (2026-06-26, Qdrant-hybrid без графа):**

| Сегмент | answer_correctness | required_entity_recall | faithfulness |
|---|---|---|---|
| multi-hop (n=12) | **0.500** | **0.701** | **0.810** |
| global (n=6) | **0.200** | **0.292** | **0.767** |

**Особые режимы:** `required_entity_recall` возвращает `1.0` (N/A) если `required_entities` пуст — не влияет на avg при items без требований.

---

### multimodal-rag (sprint-10) ✅

> **Реализовано:** sprint-10 Task 02–08 · **Финальный отчёт:** [multimodal-final.md](../../evals/reports/multimodal-final.md)  
> **Baseline:** [multimodal-baseline.md](../../evals/reports/multimodal-baseline.md)  
> **Sprint metric map:** [metric_map.md](../sprints/sprint-10-multimodal-rag/metric_map.md)

| Метрика | Сегменты | Слой | Тип | Примечание |
|---|---|---|---|---|
| `recall_at_k` | S1, S2, S3 | retrieval | NUMERIC 0–1 | Любой `required_slides` в top-k |
| `ndcg_at_5` | S1, S2, S3 | retrieval | NUMERIC 0–1 | Не для S5 |
| `mrr` | S1, S2, S3 | retrieval | NUMERIC 0–1 | |
| `set_recall_at_k` | S4 | retrieval | NUMERIC 0–1 | Доля найденных required slides |
| `trap_slide_in_topk` | S5 | retrieval (diag) | NUMERIC 0–1 | Не primary; ловушечный слайд в top-k |
| **`correct_refusal_rate`** | **S5** | **generation/behavior** | NUMERIC 0–1 | **Primary S5** — отказ без выдумки |
| `answer_correctness` | S1–S4 | generation (опц.) | NUMERIC 0–1 | GEval, Task 03+ |
| **CER** | A/OCR | ingestion-quality | NUMERIC | Task 04, не в retrieval-скор |
| **TEDS** | D/multivector | ingestion-quality | NUMERIC | Task 07, слайды 10/11 |

**Агрегация:** только по сегменту (S1_text … S5_unanswerable), не macro-average по корпусу.

---

## Кастомные метрики (E-17г)

| Метрика | ADR | Статус |
|---|---|---|
| `required_entity_recall` | sprint-09 Task 02 | ✅ Реализована (`evals/scripts/evaluators.py`). Категория **А** (детерминированная substring-проверка). Применяется только в группе `graphrag`. |

---

## Сводка порогов для baseline (E-20)

Зафиксировано **до** первого прогона sprint eval-01 (только `e2e/e2e-qa`):

| Run-level ключ | 🟢 baseline принят | 🔴 регрессия |
|---|---|---|
| `avg_answer_correctness` | ≥ 0.75 | < 0.60 |
| `avg_faithfulness` | ≥ 0.85 | < 0.70 |
| `avg_task_completion` | ≥ 0.80 | < 0.65 |
| `error_rate` | < 0.05 | ≥ 0.10 |
| `segment_match_rate` (e2e) | ≥ 0.95 | < 0.90 |

Item-level пороги — в таблицах датасетов выше.

**Пороги для graphrag-сегментов (зафиксированы до первого прогона sprint-09):**

| Run-level ключ | 🟢 baseline принят | 🔴 регрессия |
|---|---|---|
| `avg_answer_correctness` (multi-hop) | ≥ 0.65 | < 0.50 |
| `avg_answer_correctness` (global) | ≥ 0.65 | < 0.50 |
| `avg_required_entity_recall` | ≥ 0.70 | < 0.50 |
| `avg_faithfulness` | ≥ 0.75 | < 0.60 |
| `error_rate` | < 0.05 | ≥ 0.10 |

### История изменений порогов

| Дата | Метрика | Было → стало | Основание |
|---|---|---|---|
| 2026-06-14 | все (e2e) | — | Первичная фиксация при создании карты (E-20) |
| 2026-06-26 | graphrag/* | — | Зафиксированы пороги sprint-09 baseline; metricс `required_entity_recall` добавлена |

---

## Реализация (задачи 04–05)

| Компонент | Где | Примечание |
|---|---|---|
| Item evaluators | `evals/scripts/evaluators.py` | задача 05 |
| Run evaluators | `run_evaluators=` + `run_metadata` | E-9, E-19 |
| Judge config | `evals/configs/*.yaml` → `judge:` | E-5, E-17 |
| Integrity | `gt_quality: verified \| approximate` влияет на интерпретацию абсолютных порогов (E-14) | approximate — только относительное сравнение конфигов |

---

## Утверждение

- [x] dataset-map утверждён: 2026-06-14
- [x] Карта метрик показана и утверждена: пользователь / 2026-06-14 (⛔ гейт задачи 03)
- [x] Секция `graphrag/*` добавлена: 2026-06-26 (sprint-09 задача 02 baseline)
