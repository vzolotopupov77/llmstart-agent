# Summary: Sprint 04 — subagents-isolation

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-19

---

## Что реализовано

- `mentor/brief.py` — `build_brief()`, `resolve_aspect_id()` (нормализация `_` → `-`), выбор файлов по аспекту; пути только `code/...`
- `mentor/reviewer.py` — `run_reviewer()`: изолированный субагент, retry до 5 попыток, `REVIEWER_RECURSION_LIMIT=100`
- `mentor/prompts.py` — `load_yaml_prompt()` (вынесено из `agent.py`)
- `mentor/agent.py` — tool `spawn_reviewer`, `AgentRunContext`, делегирование оркестратором
- `mentor/events.py` — `SubagentStartEvent`, `SubagentEndEvent`; расширен `ContextEvent`
- `mentor/tracker.py` — эмит subagent-событий, carry-over токенов
- `mentor/renderer.py` — verbose-панели субагентов, таблица «Метод / Экономия», контраст с Sprint 03
- `mentor/retrieval.py` — шапка `code-index.md` с путями `code/` и явным `code/README.md`
- `mentor/config/__init__.py` — `SPRINT03_BASELINE_DELTA = 4500`
- `mentor/config/prompts/orchestrator-system.yaml` — делегирование, таблица aspect-id, защита от повторного spawn
- `mentor/config/prompts/reviewer-system.yaml` — промпт Reviewer + tool calls до конца
- `tests/test_brief.py`, `tests/test_reviewer.py`, `tests/test_subagent_tracker.py`
- `README.md` — модули `brief.py`, `reviewer.py`, `prompts.py`

---

## Отклонения от плана

- Вместо отдельного `create_deep_agent` с ограниченным backend — **изолированный `run_reviewer()`** через тот же harness с чистой историей и отдельным `thread_id`
- Aspect-id в рубрике (`code_quality`) vs промпте (`code-quality`) — добавлена **`resolve_aspect_id()`**, не только правка промпта
- Защита от duplicate spawn — **промпт оркестратора**, без code-guard в `spawn_reviewer` (достаточно для dogfooding)
- Δ оркестратора после spawn **56–251 токенов** (цель ≤500), но рост при `read_file` review-нот на синтезе — **carry-over в Sprint 05**

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `spawn_reviewer` возвращает строку при ошибке, не валит оркестратор | Нестабильность Gemini Flash на больших репо |
| Retry reviewer до 5 попыток, если `notes/review-<aspect>.md` не создан | Субагент иногда завершался без записи note |
| `SPRINT03_BASELINE_DELTA = 4500` в конфиге | Единая константа для контрастной строки verbose |
| Пути студента только с префиксом `code/` в промптах, брифах и `code-index` | Fix false positive «README отсутствует» |
| Таблица aspect-id в orchestrator prompt + нормализация в коде | Модель путала `code_quality` и `code-quality` |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Ложное «README отсутствует» | Промпты + `code-index` + `brief.py` с `code/README.md` |
| Reviewer не создавал note на большом репо | Retry до 5 попыток, `REVIEWER_RECURSION_LIMIT=100` |
| Duplicate spawn на шаге синтеза | Секция «Защита от повторного spawn» в orchestrator prompt |
| Aspect-id с underscore vs дефис | `resolve_aspect_id()` + таблица в промпте |
| Оркестратор раздувается при чтении review-нот | Зафиксировано как carry-over → Sprint 05 |

---

## Dogfooding

| Прогон | Результат |
|--------|-----------|
| `. "CLI-утилита на Python"` | 4 brief + 4 note; spawn Δ ≤251; без ложного README |
| GitHub `zva-hh-agent` (~108 файлов) | 4 субагента; duplicate spawn не воспроизведён после fix промпта |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `briefs/brief-<aspect>.md` ×4 | ✅ |
| 2 | `notes/review-<aspect>.md` ×4 | ✅ |
| 3 | Δ оркестратора после spawn ≤500 на аспект | ✅ (+56…+251) |
| 4 | Verbose: панели запуска/завершения субагента | ✅ |
| 5 | Контраст «↑ В Sprint 03: +4 500» | ✅ |
| 6 | Compact без изменений | ✅ |
| 7 | Нет ложного «README отсутствует» | ✅ |
| 8 | `make ci` → exit 0 | ✅ (43 теста) |

---

## Что дальше

- **Sprint 05 (context-engineering):** управление окном оркестратора — чтение review-нот без раздувания истории; валидация синтеза
- Carry-over: нестабильность Gemini Flash (много retry); ложные замечания в Feedback (валидация в Sprint 05/07)

---

## Ссылки

- [roadmap.md](../../roadmap.md) — v0.2 закрыт
- [sprint-05-context-engineering/plan.md](../sprint-05-context-engineering/plan.md)
