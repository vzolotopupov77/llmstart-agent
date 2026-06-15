# Error analysis — e2e/e2e-qa v001

> **Дата:** 2026-06-15 · **Задача:** [sprint-eval-03 Task 01](../../docs/sprints/eval/sprint-eval-03-eval-fix-iteration-2/tasks/01-error-analysis/plan.md)
> **Метод:** К-3 (gather → open coding → cluster → label & measure → decide & act)
> **Primary run:** `candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z` (0.631)
> **Reference run:** `baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z` (0.527)
> **Compare:** [compare report](compare--baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z--vs--candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z.md)
> **Open coding (generated):** [error-analysis-open-coding.md](error-analysis-open-coding.md)

---

## 1. Gather

| Источник | Что использовано |
|----------|------------------|
| Run JSON ×2 | scores, agent message, tools, retrieval_context, judge comments |
| Манифест v001 | `item_id`, `intent` (G1–G9), `answer_key_points` — join по нормализованному input (порядок run ≠ порядок YAML) |
| Langfuse traces | span evidence из analyze-отчётов candidate run (топ-10) |
| Compare | 8 improved / 2 regressed / 16 stable |

**Эффект v2 prompt (iter #1):** retrieval-skip снизился (heuristic **9→5** items); главная метрика **+0.104**. Остаточный провал — **generation/behavior** при вызванном RAG.

---

## 2. Open coding (выборка)

Полная таблица 26 items — в [error-analysis-open-coding.md](error-analysis-open-coding.md). Ниже — items с **AC < 0.75** на candidate + регрессии.

| run idx | item_id | intent | AC | Δ | layer* | open note (первичная причина) |
|--------:|---------|--------|---:|--:|--------|--------------------------------|
| 23 | e2e-qa-0003 | G1.3 | 0.00 | 0.00 | generation | «нет данных» вместо ориентиров: до 2 ч, вечер/выходные, записи |
| 9 | e2e-qa-0017 | G9.4 | 0.00 | 0.00 | retrieval | mock «оплатил» — нет `confirm_payment`, только запрос контактов |
| 21 | e2e-qa-0005 | G2.2 | 0.00 | **−0.40** | generation | **регрессия:** intensive не распознан, отказ вместо структуры семинаров |
| 2 | e2e-qa-0024 | G1.4 | 0.00 | 0.00 | generation | timezone SF: нет MSK-времени и оценки travel |
| 3 | e2e-qa-0023 | G3.2 | 0.20 | **−0.20** | retrieval | **регрессия:** multi-turn — игнор sync-предпочтения, подмена продукта |
| 15 | e2e-qa-0011 | G4.5 | 0.20 | 0.00 | generation | objection: повторный запрос «цели» после отказа пользователя |
| 1 | e2e-qa-0025 | G3.3 | 0.40 | 0.00 | generation | барьер «до 15 сентября» — нет следующего шага / потока |
| 18 | e2e-qa-0008 | G3.1 | 0.40 | 0.00 | generation | objection по пятнице днём — нет альтернативы вечер/выходные |
| 16 | e2e-qa-0002 | G1.2 | 0.60 | +0.30 | generation | формат/комбо — частичное покрытие key_points |
| 4 | e2e-qa-0022 | G9.1 | 0.70 | 0.00 | generation | рассрочка: неполная политика MVP mock |
| 5 | e2e-qa-0021 | G4.1 | 0.70 | 0.00 | generation | demo objection — частичное описание программы |
| 13 | e2e-qa-0013 | G4.2 | 0.70 | +0.50 | retrieval | «не вижу что внутри» — улучшился, но ниже north-star |
| 14 | e2e-qa-0012 | G5.1 | 0.70 | +0.30 | generation | CPO/комбо — не все key_points (код, честность про код) |
| 17 | e2e-qa-0009 | G4.3 | 0.70 | 0.00 | behavior | demo/возврат — borderline, частичное покрытие |

\* heuristic layer из `failure_analysis.py` — см. §6.

---

## 3. Cluster — таксономия провалов

| Код | Definition | Пример item_id |
|-----|------------|----------------|
| **GEN-NO-DATA** | RAG вызван, контекст есть, но ответ «точных данных нет» / уход в уточняющий вопрос вместо ориентиров из KB | e2e-qa-0003, e2e-qa-0024 |
| **GEN-KP-MISS** | Ответ частично релевантен, но не покрывает `answer_key_points` (формат, состав комбо, политики) | e2e-qa-0025, e2e-qa-0008, e2e-qa-0002 |
| **PROD-MAP** | Неверная привязка к продукту (intensive, vibe-coding-intensive) или подмена SKU | e2e-qa-0005 |
| **BEH-FUNNEL** | Mock payment / confirm / lead — неверная tool-trajectory | e2e-qa-0017 |
| **BEH-MULTI** | Multi-turn: игнор контекста assistant/user, подмена темы | e2e-qa-0023 |
| **BEH-OBJECTION** | G4.x: demo/цена/доверие — политика «нет демо», давление, повтор квалификации | e2e-qa-0011, e2e-qa-0021, e2e-qa-0013 |
| **RET-SKIP** | Нет `search_knowledge_base` при FAQ (на candidate **редко** после v2) | *(baseline-heavy; на candidate — e2e-qa-0017 без tools)* |

7 категорий; **RET-EMPTY** (пустой RAG при вызове) на candidate не выделен отдельно — единичные случаи внутри GEN-NO-DATA.

---

## 4. Label & measure

**Primary label:** candidate run, AC < 0.75 → **14/26 (54%)**.

| Категория | count | failure rate | intent (top) |
|-----------|------:|-------------:|--------------|
| GEN-KP-MISS | 5 | 19% | G3.x, G1.2, G5.1, G9.1 |
| BEH-OBJECTION | 4 | 15% | G4.x |
| GEN-NO-DATA | 2 | 8% | G1.3, G1.4 |
| PROD-MAP | 1 | 4% | G2.2 |
| BEH-FUNNEL | 1 | 4% | G9.4 |
| BEH-MULTI | 1 | 4% | G3.2 |

*Примечание:* один item — одна primary category; смешанные случаи (0005 = PROD-MAP + GEN-NO-DATA) → primary **PROD-MAP** (first failure).

### Heuristic layer (candidate)

| layer | baseline | candidate | Δ |
|-------|--------:|----------:|--:|
| retrieval | 9 | 5 | −4 |
| generation | 10 | 10 | 0 |
| behavior | 1 | 5 | +4 |
| unknown | 6 | 6 | 0 |

v2 **убрал retrieval-skip**, но **generation** остался доминирующим; рост **behavior** — artifact heuristic (segment/task_completion) + реальные funnel/objection провалы.

### Что v2 починил (Δ ≥ +0.05)

| item_id | Δ | категория до → после |
|---------|--:|----------------------|
| e2e-qa-0021 | +1.00 | RET-SKIP → OK (комбо программы) |
| e2e-qa-0002 | +0.80 | RET-SKIP → GEN-KP-MISS (частично) |
| e2e-qa-0013 | +0.50 | RET-SKIP → BEH-OBJECTION (borderline) |
| e2e-qa-0012 | +0.30 | generation → borderline |
| e2e-qa-0015 | +0.30 | generation → borderline |

### Регрессии (разбор)

| run idx | item_id | Δ | root cause |
|--------:|---------|--:|------------|
| 21 | e2e-qa-0005 | −0.40 | v2 RAG-first: search вызван, но ответ «расписание не определено» + нет структуры intensive → **PROD-MAP + GEN-NO-DATA** |
| 3 | e2e-qa-0023 | −0.20 | multi-turn: после assistant про пятницу днём агент предлагает другой intensive без признания sync-ограничения → **BEH-MULTI** |

---

## 5. Decide & act

| P | Категория | Действие | Куда |
|---|-----------|----------|------|
| **P0** | GEN-NO-DATA, GEN-KP-MISS, PROD-MAP | Prompt **v3**: синтез KB-ориентиров, привязка `vibe-coding-intensive`, не говорить «нет данных» при partial KB | **Task 03** (plan апрувнут) |
| **P0** | BEH-FUNNEL | Prompt v3: mock confirm → `confirm_payment` + fallback на lead | **Task 03** |
| **P1** | BEH-MULTI | Уточнить criteria + multi-turn guard в v002; prompt v3 rule 12 | **Task 02** + Task 03 |
| **P1** | BEH-OBJECTION | Items G4.x: явнее `must_not` / demo policy в v002 | **Task 02** |
| **P2** | RET-SKIP | На candidate редко; мониторить после v3 | eval-04 / regression |

### Task 03 — валидация гипотезы

**Подтверждено:** iter #2 через **prompt v3** (не смена модели). Данные: 10 generation-провалов при faithfulness≥0.7; rec analyze #1; model upgrade не адресует «нет данных» при наличии RAG.

**Без изменений:** `config_id: candidate-generation-keypoints-v3`, compare vs `…094647Z`.

### Task 02 — кандидаты v002

| item_id | Что уточнить в criteria |
|---------|-------------------------|
| e2e-qa-0023 | sync-preference, запрет подмены продукта без ответа на objection |
| e2e-qa-0005 | структура intensive обязательна даже при TBD расписании |
| e2e-qa-0017 | `gt_quality: verified` — tool trajectory confirm_payment |
| e2e-qa-0024 | timezone: MSK + SF comment как отдельные key_points |

---

## 6. Layer vs domain (расхождения)

| item_id | heuristic layer | domain category | Комментарий |
|---------|-----------------|-----------------|-------------|
| e2e-qa-0017 | retrieval | BEH-FUNNEL | нет tools → heuristic retrieval; доменно — funnel |
| e2e-qa-0023 | retrieval | BEH-MULTI | faithfulness просел из-за подмены продукта |

---

## 7. Ограничения

- 26 items — ориентировочные частоты (К-4).
- Items 0.70–0.74 — borderline; judge variance возможна (gemini-2.5-flash-lite).
- Join manifest↔run по input; run index в compare ≠ index в YAML.

---

## ⛔ Гейт Task 02

Апрув таксономии (7 категорий) и приоритетов P0–P2 → можно открывать **Task 02 plan**.
