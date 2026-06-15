# Карта датасетов — LLMStart Agent (llmstart.ru)

> **Создаётся:** задача 02 sprint-eval-01 · **Методология:** [.methodology/eval/eval-methodology.md](../../.methodology/eval/eval-methodology.md)
> **Статус:** ✅ утверждена пользователем / 2026-06-14 — задача 03 (метрики) может начинаться после апрува плана задачи 03
> **Последнее обновление:** 2026-06-14

---

## Откуда выведена карта

| Источник | Что взято |
|---|---|
| [vision.md](../concept/vision.md) §3 | Сценарии С-1…С-7, С-11 — матрица покрытия; С-4, С-8…С-10 — вне scope eval MVP |
| [analysis-report.md](../../datasets/extraction/analysis-report.md) | Таксономия G1–G9 (апрув 2026-06-09); приоритеты P0–P3; пробелы корпуса (5 чатов) |
| [dataset-plan.md](../../datasets/dataset-plan.md) | Типы записей (b2c-rag, product, segment, objection, tools; B2B ветка); формат ChatML; политика G4 «демо нет» |
| Реальные диалоги | `datasets/dialogs/` — 5 чатов (4 B2C + 1 B2B), ~30–90 сообщений суммарно |
| Черновые датасеты v2 | `datasets/b2c/v2/dataset.jsonl` (72 items), `datasets/b2b/v2/dataset.jsonl` (15) — **материал для маппинга**, не eval-манifest |
| База знаний | `data/b2c/` (catalog, faq, courses-overview), `data/b2b/` (corporate-training, custom-development) — эталоны и синтетика |

**Принцип К-4:** один датасет — одна зона ответственности. Legacy JSONL не копируется в `evals/` as-is: items проходят review, `reviewed_by`, `gt_quality` (задачи 04+).

---

## Матрица покрытия сценариев

| Сценарий (vision) | Покрывающие датасеты |
|---|---|
| **С-1** Консультация по курсу (RAG + каталог) | `e2e/e2e-qa`, `rag/rag-retrieval`, `behavior/segment-routing` (частично) |
| **С-2** Покупка (мок) | `behavior/tool-trajectory`, `behavior/funnel-to-lead`, `e2e/e2e-qa` (subset) |
| **С-3** Подтверждение и лид | `behavior/tool-trajectory`, `behavior/funnel-to-lead` |
| **С-4** Демо экспертизы (SSE UI) | — *(см. «Не покрываем»)* |
| **С-5** Уточнение сегмента B2B/B2C | `behavior/segment-routing`, `rag/b2b-rag` |
| **С-6** Корпоративный запрос | `rag/b2b-rag`, `behavior/segment-routing` |
| **С-7** Сравнение B2C vs B2C для компании | `behavior/segment-routing`, `e2e/e2e-qa` |
| **С-8** Виджет на сайте | — *(канал = metadata, не отдельный датасет)* |
| **С-9** Переход web → Telegram | — *(session continuity — v0.2+)* |
| **С-10** Только Telegram | — *(channel=telegram в metadata items)* |
| **С-11** Орг. вопрос студента | `rag/rag-retrieval`, `e2e/e2e-qa` (формат, материалы) |

---

## Датасеты

### e2e/e2e-qa

| Поле | Значение |
|---|---|
| **Группа (слой)** | e2e |
| **Что проверяет** | Сквозное качество ответа на типичный pre-purchase вопрос: понимание запроса, RAG-факты, продукт, тон — без изоляции одного слоя. |
| **Обоснование** | С-1 — главная пользовательская ценность; G1–G5 доминируют в реальных чатах (4/5). Главная метрика eval-трека (E-18) привязана к этому датасету. Отдельно от component-датасетов, чтобы ловить регрессии «в целом хорошо, но клиенту бесполезно». |
| **Источник items** | real_dialog: CHAT_0014, 0020, 0070, 0110 (~12–15) · synthetic: `data/b2c/` (~8–12) · пропорция ~60/40 |
| **Схема item** | input: string или ChatML[] (multi-turn) · expected_output: **evaluation criteria** — `segment`, `product_codes[]`, `answer_key_points[]`, `should_clarify`, `acceptable_clarifications[]`, `must_not[]` (опц.) · metadata: `segment`, `intent` (G1–G9), `source`, `source_chat`, `turn_mode`, `gt_quality`, `reviewed_by` |
| **Размер (MVP)** | **≥20** (sprint eval-01 vertical slice); целевой **25–30** к eval-02 |
| **Ground truth** | key_points из KB + разбор диалогов; extraction → **approximate** (~70%); после human review → verified. Multi-turn из CHAT_0110, 0020 — paraphrased assistant context. |
| **Предполагаемый тип проверки** | judge (answer correctness по key_points) + детерминированные guard (segment, must_not) |

---

### rag/rag-retrieval

| Поле | Значение |
|---|---|
| **Группа (слой)** | rag |
| **Что проверяет** | Фактический ответ из B2C KB: формат, расписание, состав комбо, политики, сравнение курсов — слой retrieval + generation по FAQ. |
| **Обоснование** | G1 (4/5 чатов, P0) — ядро pre-purchase; изолированный слой для диагностики «RAG достаёт не то / галлюцинирует факт». С-1, С-11. |
| **Источник items** | real_dialog: G1/G4/G6 из 4 B2C чатов (~12) · synthetic: faq, courses-overview (~10–13) · ~50/50 |
| **Схема item** | input: string · expected_output: criteria — `answer_key_points[]`, `segment: b2c`, опц. `tools: [{search_knowledge_base}]` · metadata: `group`, `category` (G1.x…), `source`, `kb_verified` (если эталон привязан к файлу KB) |
| **Размер (MVP)** | 20–25 |
| **Ground truth** | verified где `kb_verified` в metadata v2; TBD расписание (G1.3) — approximate; возврат (G9.2) — approximate до сверки с faq |
| **Предполагаемый тип проверки** | judge + опц. trajectory (tool search вызван с audience=b2c) |

---

### rag/b2b-rag

| Поле | Значение |
|---|---|
| **Группа (слой)** | rag |
| **Что проверяет** | Ответы по B2B KB: корпоративное обучение, кастомная разработка, форматы, бриф — без подмены B2C checkout. |
| **Обоснование** | С-6; G7.2, G2.5, G9.3; CHAT_0127 — единственный реальный B2B чат. Отдельный датасет (решение 2026-06-09): не смешивать с B2C mix. |
| **Источник items** | real_dialog: CHAT_0127 (~2–3) · synthetic: `data/b2b/` (~8–12) · ~20/80 |
| **Схема item** | input: string · expected_output: criteria — `segment: b2b`, `answer_key_points[]`, `must_not: [B2C checkout на команду]` · metadata: `group`, `category`, `source` |
| **Размер (MVP)** | 10–15 |
| **Ground truth** | extraction approximate; синтетика по corporate-training.md → verified после review |
| **Предполагаемый тип проверки** | judge + segment exact |

---

### behavior/segment-routing

| Поле | Значение |
|---|---|
| **Группа (слой)** | behavior |
| **Что проверяет** | Классификация B2B vs B2C и выбор RAG-audience; не задавать B2B-вопросы физлицу и наоборот. |
| **Обоснование** | G7 (5/5 чатов явно/неявно, P0); С-5, С-7. Провал = не тот сегмент → неверный KB и воронка. |
| **Источник items** | real_dialog: G7 из чатов (~4) · synthetic: B2B-маркеры в B2C-канале, «курс для себя от работодателя» (~6–8) |
| **Схема item** | input: string · expected_output: **exact** `segment` + criteria `answer_key_points[]` (маршрут: consultation / list products) · metadata: `category` G7.x |
| **Размер (MVP)** | 10–15 |
| **Ground truth** | verified для однозначных маркеров; смешанные — approximate |
| **Предполагаемый тип проверки** | детерминированная (segment) + judge (тон маршрутизации) |

---

### behavior/tool-trajectory

| Поле | Значение |
|---|---|
| **Группа (слой)** | behavior |
| **Что проверяет** | Корректность вызова MCP-tools: имена, порядок (IN_ORDER), аргументы (`product_code`, `audience`). |
| **Обоснование** | G8–G9, С-2, С-3; в реальных чатах оплата **не встречается** — синтетика обязательна (analysis-report). Component-level диагностика (К-2). |
| **Источник items** | synthetic: ~100% (12–15 из v2 b2c-tools) · real_dialog: 0 |
| **Схема item** | input: string или ChatML[] · expected_output: criteria + **`tools[]`** `{name, args}` · metadata: `dataset_type`, `turn_mode` |
| **Размер (MVP)** | 12–15 |
| **Ground truth** | verified (args детерминированы по catalog/payments mock) |
| **Предполагаемый тип проверки** | детерминированная (ToolCorrectness IN_ORDER) |

---

### behavior/funnel-to-lead

| Поле | Значение |
|---|---|
| **Группа (слой)** | behavior |
| **Что проверяет** | Multi-turn воронка B2C/B2B: интерес → payment link → confirm → save_lead; удержание контекста продукта. |
| **Обоснование** | С-2 → С-3 end-to-end; G8.3 commitment без закрытия. User simulation (E-23) — сценарии в `scenarios.yaml`. |
| **Источник items** | synthetic: ~100% (8–12) · scenarios.yaml для симулятора пользователя |
| **Схема item** | input: начальная реплика · expected_output: criteria успеха сценария + tools chain · metadata: `scenario_id`, `max_turns` |
| **Размер (MVP)** | 8–12 (реализация **sprint eval-02 / v0.2**, скелет в eval-01) |
| **Ground truth** | verified после согласования сценариев |
| **Предполагаемый тип проверки** | смешанная (TaskCompletion + ToolCorrectness) |

---

### edge/edge-cases

| Поле | Значение |
|---|---|
| **Группа (слой)** | edge |
| **Что проверяет** | Возражения, доверие, timezone, senior-skeptic, отложенное решение — поведение при высокой сложности и риске галлюцинаций. |
| **Обоснование** | G3 (3/5), G4 (2/5 но **высокая сложность**, P2); error analysis (К-3): провалы «хорошо читаются, но врут про демо». Политика G4: публичного демо нет (dataset-plan §7). |
| **Источник items** | real_dialog: CHAT_0020 (G3), CHAT_0110 (G4) multi-turn (~8) · synthetic: G4.1–G4.5, G1.4 timezone (~7–12) |
| **Схема item** | input: ChatML[] предпочтительно (~40% multi) · expected_output: criteria + **`must_not[]`** (демо-URL, давление на «цель») · metadata: `difficulty: hard`, `group` G3/G4 |
| **Размер (MVP)** | 15–20 |
| **Ground truth** | approximate для тона; must_not — verified (жёсткие запреты) |
| **Предполагаемый тип проверки** | judge + детерминированная (must_not / rejection phrases) |

---

## Маппинг legacy v2 → eval-датасеты

| Legacy `metadata.dataset_type` (v2) | Eval-датасет | Примечание |
|---|---|---|
| `b2c-rag` | `rag/rag-retrieval` + часть `e2e/e2e-qa` | e2e — репрезентативная выборка, не все 25 RAG |
| `b2c-product` | `e2e/e2e-qa` | product match в сквозном слое |
| `b2c-segment` | `behavior/segment-routing` | |
| `b2c-objection` | `edge/edge-cases` + `e2e/e2e-qa` | hard cases → edge |
| `b2c-tools` | `behavior/tool-trajectory` + `funnel-to-lead` | |
| `b2b-*` | `rag/b2b-rag` + `segment-routing` | B2B nurture → b2b-rag / edge (G8.4) |

---

## Чего сознательно НЕ покрываем

| Что | Причина |
|---|---|
| **С-4** SSE / reasoning UI | Канальный UX, не Agent Core; проверяется E2E вручную / frontend-тестами |
| **С-8, С-9, С-10** как отдельные датасеты | `channel` — metadata item; один агент, различия форматирования — вне eval MVP |
| **Retrieval Hit Rate@k / chunk_ids** | Chunking не зафиксирован (dataset-plan: отложено до v2) |
| **Рассрочка, реальные платёжные провайдеры** | Нет в MVP/KB как доступная опция |
| **Эскалация живому эксперту, выдача доступа к курсу** | Вне MVP (vision) |
| **Многоходовые диалоги >4 реплик** | Короткий корпус; funnel — отдельно через user simulation |
| **Негативный отказ «навсегда ушёл»** | Редко в данных; низкий приоритет до error analysis |
| **Полное покрытие 72 B2C items в eval-01** | Vertical slice: только `e2e-qa` ≥20; остальное — sprint eval-02 |

---

## Порядок реализации

| Этап | Датасет | Спринт | Артефакт |
|---|---|---|---|
| 1 | **e2e/e2e-qa** | eval-01, задача 04 | `evals/datasets/e2e/e2e-qa/v001_*.yaml` + sync |
| 2 | `rag/rag-retrieval` | eval-04 | v001 |
| 3 | `behavior/segment-routing` | eval-04 | v001 |
| 4 | `edge/edge-cases` | eval-04 | v001 |
| 5 | `behavior/tool-trajectory` | eval-04 | v001 |
| 6 | `rag/b2b-rag` | eval-04 | v001 |
| 7 | `behavior/funnel-to-lead` + `scenarios.yaml` | eval-04 | user simulation (E-23) |

**Зеркалирование Langfuse (E-16):** folders-as-versions — `e2e/e2e-qa/v001`, …

---

## Утверждение

- [x] Карта показана и утверждена: пользователь / 2026-06-14 (⛔ гейт задачи 02)
