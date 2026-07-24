# Summary: Sprint 06 — rubrics-skills

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-24

---

## Что реализовано

- `mentor/rubric.py` — `detect_topic()`, `select_rubric()`, `prepare_rubric()`; сильные сигналы FastAPI/CLI; skip meta/test файлов для детектора
- `mentor/config/rubrics/fastapi-service.yaml` — 6 аспектов (api-design + fastapi-templates, code-quality + modern-python, …)
- `mentor/config/rubrics/python-cli.yaml` — 5 аспектов (cli-design, code-quality + modern-python, …)
- `mentor/skills.py` — `resolve_skill()` (`.agents/skills/`, `~/.agents/skills/`, `~/.codex/skills/`)
- `mentor/brief.py` — секция «Экспертный контекст» в брифе; `build_all_briefs()`
- `mentor/agent.py` — `setup_rubric_and_briefs()`, tool `ask_user`, `interrupt_on`, HITL-сброс plan/notes, компактный retry-hint
- `mentor/events.py` — `SkillEvent`, `TopicDetectedEvent`, `RubricSelectedEvent`, `UserQuestionEvent`
- `mentor/tracker.py` — HITL loop (interrupt → prompt → resume), `pending_user_answer`
- `mentor/renderer.py` — панели темы/рубрики/навыков, HITL-вопрос, «Навыки сессии», `reset_after_topic_change()`
- `mentor/cli.py`, `mentor/render.py` — HITL callback; одна панель в verbose, panel+prompt в compact
- `mentor/config/prompts/orchestrator-system.yaml` — тематические рубрики, правила ask_user, компактный план
- `tests/test_rubric.py`, `tests/test_skills.py`, `tests/test_render.py`, `tests/test_renderer_ce.py`, `tests/test_agent.py`

---

## Отклонения от плана

- **Детектор темы** — не `\bfastapi\b` в тексте, а импорты/`FastAPI(`/`APIRouter(`; исключены `rubric.py` и `tests/` (регрессия dogfooding на `./`)
- **HITL UI** — verbose: панель через `UserQuestionEvent`, prompt без второй панели; compact: panel + prompt в `render_user_question`
- **План после HITL** — явный сброс `plan.md` и stale review-notes + reset счётчика шагов в renderer (не было в исходном plan)
- **Оркестратор** — компактный план (1 шаг на аспект + синтез) и `_next_orchestrator_action()` для retry (Sprint 06 hardening)

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `auto_topic` блокирует `ask_user` | Явная или авто тема — без лишнего HITL |
| `pending_user_answer` в tracker | Один prompt на interrupt; tool переиспользует ответ |
| Skills ищутся в нескольких путях | Локальные и глобальные `.agents/skills/` |
| Сброс workspace после ответа пользователя | Старый plan от `default.yaml` смешивал шаги с новой рубрикой |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `./` определялся как FastAPI | Убрать bare `fastapi` из паттернов; skip meta-файлов |
| Две панели «Уточняющий вопрос» | verbose: event → panel, callback → prompt only |
| Шаги [1/3]→[7/7] после HITL | Очистка plan/notes; reset renderer; hint в retry |
| Оркестратор не доходил до feedback (6 аспектов + 22 шага) | Компактный plan в prompt + next-action hint |
| Дубли HITL prompt (ранний баг) | tracker + callback dedup через `pending_user_answer` |

---

## Dogfooding

| Прогон | Результат |
|--------|-----------|
| `./ --verbose` (без темы) | auto Python CLI, `python-cli.yaml`, 7 шагов, feedback/fix_plan |
| внешний репо + «REST API на FastAPI» | `fastapi-service.yaml`, fastapi-templates, FastAPI-специфичный feedback |
| `C:\Temp\mentor-hitl-test --verbose` | default → HITL → FastAPI/CLI, одна панель, смена рубрики без restart |
| явная тема без HITL | ✅ (пользователь) |
| HITL `--compact` | ✅ (пользователь) |
| навык в `brief-*.md` | ✅ (пользователь) |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | FastAPI / CLI → правильные рубрики | ✅ auto, HITL, явная тема |
| 2 | Навык в брифе субагента | ✅ секция «Экспертный контекст» |
| 3 | HITL: один вопрос, продолжение | ✅ verbose + compact |
| 4 | Verbose — навыки по аспектам | ✅ |
| 5 | FastAPI feedback лучше default | ✅ внешний репо: APIRouter, DI, OpenAPI |
| 6 | `make ci` → exit 0 | ✅ 91 тест |
| 7 | documentation → `code/README.md` | ✅ в YAML обеих рубрик |

---

## Что дальше

- **Sprint 07 (dogfooding):** формальный E2E `mentor check .` на продукте как финальный критерий v1.0
- **Хвост (не блокирует):** Gemini Flash периодически завершает ответ без tool call → retry; при необходимости смена модели или рост `AGENT_MAX_ATTEMPTS`

---

## Ссылки

- [roadmap.md](../../roadmap.md) — v0.4 закрыт
- [sprint-07-dogfooding/plan.md](../sprint-07-dogfooding/plan.md)
