# Roadmap — Eval-трек: LLMStart Agent (llmstart.ru)

> **Методология:** [.methodology/eval/eval-methodology.md](../.methodology/eval/eval-methodology.md)
> **Продуктовый roadmap:** [roadmap.md](roadmap.md)
> **Последнее обновление:** 2026-06-15 (sprint-eval-03 закрыт)

---

## Цель трека

Измеримое качество агента: для любого изменения системы (промпт, модель, реализация, retrieval) — ответ «стало лучше или хуже и где» по главной метрике (E-18) на версионированных датасетах.

---

## Предусловия трека (Слой 0 методологии)

| Пункт | Статус | Комментарий |
|---|---|---|
| Агент работает e2e, доступен по API | ✅ | Agent Core: `POST /api/v1/chat` (FastAPI, порт 8003), ReAct + MCP tools in-process; веб и Telegram через Core |
| Трейсинг + спаны инструментов в Langfuse | ✅ | SDK v3, self-hosted v3 (sprint-07); trace за turn, LLM/tool spans в `observability/langfuse.py` |
| Реестр конфигураций (`config_id`, E-6) | ✅ | Задача 01 sprint-eval-01; `evals/configs/`, `AgentConfigRegistry` |
| ≥ 10 кейсов с известным ответом | ✅ | `datasets/b2c/v2/dataset.jsonl` (72 items), `datasets/b2b/v2/dataset.jsonl` (15), 5 реальных чатов в `datasets/dialogs/`, отчёт `datasets/extraction/analysis-report.md`, КБ `data/` |
| Главная метрика определена (E-18) | ✅ | `avg_answer_correctness` на `e2e/e2e-qa` — [metrics-map.md](eval/metrics-map.md) |
| ≥ 2 конфигурации для сравнения | ✅ | `baseline-react-chroma` + `candidate-rag-first-prompt` в `evals/configs/` (sprint-eval-02) |

---

## Легенда

📋 Planned · 🚧 In Progress · ✅ Done · ⏸ Paused · 🗄 Archived

> **⚠️ KR — это обещания спринтов, а не todo создания roadmap.** При генерации этого документа никакие рабочие артефакты (dataset-map, metrics-map, конфиги, манифесты) НЕ создаются — они появляются только внутри задач спринтов после апрува плана (правило агента №8 методологии).

---

## v0.1 — Eval MVP: вертикальный срез ✅

**Цель:** полный путь «манифест → review → sync → baseline-прогон → отчёт» работает на одном датасете.

**Ключевые результаты:**
- [x] Реестр конфигов: `config_id` реально меняет поведение агента (E-6)
- [x] Каркас `evals/` + команды операций работают (E-2)
- [x] `dataset-map.md` и `metrics-map.md` утверждены — 2026-06-14
- [x] Датасет `e2e-qa`: v001, 26 items, sync ✅
- [x] Baseline-ран — `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z`
- [x] Отчёт анализа — [baseline report](../evals/reports/baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z.md)

**Спринты:**
| # | Sprint | Цель | Статус | Документ |
|---|--------|------|--------|---------|
| eval-01 | vertical-slice | baseline-оценка на e2e-qa одной командой | ✅ | [sprint-eval-01](sprints/eval/sprint-eval-01-vertical-slice/README.md) |
| eval-02 | eval-fix-loop | evaluators, re-baseline, compare, candidate, Langfuse UI | ✅ | [sprint-eval-02](sprints/eval/sprint-eval-02-eval-fix-loop/README.md) |
| eval-03 | eval-fix-iteration-2 | error analysis, e2e-qa v002, candidate #2, E-22 2/2 | ✅ | [sprint-eval-03](sprints/eval/sprint-eval-03-eval-fix-iteration-2/README.md) |
| eval-04 | datasets-coverage | component-датасеты + funnel-to-lead (E-23) | 📋 | [sprint-eval-04](sprints/eval/sprint-eval-04-datasets-coverage/README.md) |

---

## v0.2 — Сравнимость и цикл улучшения 🚧

**Цель:** сравнение конфигураций и работающий eval-fix loop.

**Ключевые результаты:**
- [x] `compare` с защитой версии датасета (E-16) — sprint-eval-02 Task 03
- [x] ≥ 1 candidate-конфиг прогнан и сравнён с baseline (E-7) — [exp-003](../evals/reports/exp-003-candidate-rag-first-prompt.md), Δ +0.104
- [x] ≥ 2 итерации eval-fix loop с зафиксированной дельтой (E-22) — exp-003 + exp-004
- [ ] `funnel-to-lead` через user simulation (E-23) → **eval-04**
- [x] Первый error analysis с таксономией провалов; категории → items (К-3/К-4) — eval-03 ✅

---

## v1.0 — Институционализация 📋

**Цель:** eval как постоянная практика, а не разовая акция.

**Ключевые результаты:**
- [ ] Skill проекта (правила агента + шаблоны методологии)
- [ ] CI regression-gate по главной метрике
- [ ] Annotation queues для разметки (corrected outputs → эталоны; human baseline для судьи)
- [ ] Разметка approximate → verified расширена (E-14)
- [ ] (опц.) Онлайн-evaluators на прод-трафике

---

## История изменений

| Дата | Изменение |
|------|-----------|
| 2026-06-15 | **sprint-eval-03 закрыт:** E-22 2/2, v002 baseline 0.662, v3 отклонён |
| 2026-06-15 | Task 04 eval-03: rebaseline winning candidate на v002 — exp-005 |
| 2026-06-15 | Task 01 eval-03: error analysis e2e-qa v001 — 7 категорий, P0 prompt v3 |
| 2026-06-15 | Перестановка спринтов: eval-03 = eval-fix #2 + error analysis; eval-04 = datasets-coverage |
| 2026-06-15 | sprint-eval-02 закрыт: re-baseline 0.527, candidate v2 +0.104, Langfuse UI + backfill |
| 2026-06-15 | Task 03: compare_runs + факторный анализ (RU warnings) |
| 2026-06-15 | Task 02: re-baseline e2e-qa (avg_answer_correctness 0.527 vs 0.135 broken judge) |
| 2026-06-14 | sprint-eval-01 закрыт: vertical slice e2e-qa, baseline + analyze report |
| 2026-06-14 | Задача 05: baseline run e2e-qa v001 (26 items, avg_answer_correctness 0.135) |
| 2026-06-14 | Задачи 02–03 закрыты: dataset-map и metrics-map утверждены |
