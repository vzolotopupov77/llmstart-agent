# Summary: Sprint 07 — dogfooding

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-24

---

## Что реализовано

- `mentor/retrieval.py` — исключения `workspace/`, `sprints/`, `concept/` при dogfooding (нет рекурсии в `code/`)
- `mentor/config/prompts/reviewer-system.yaml` — примеры адресного feedback (файл + строки)
- `mentor/render.py` — секция «Что хорошо»; заголовки fix_plan с `[Высокий]` / `[Средний]` / `[Низкий]`
- `mentor/renderer.py` — verbose-прогресс шагов на `in_progress` и `completed`; обновление панели плана при росте todo
- `tests/test_integration.py` — smoke E2E CLI без LLM (mock OpenRouter + orchestrator)
- `tests/test_retrieval.py` — тест исключений dogfooding-директорий
- `tests/test_cli.py` — 7 тестов: `--help`, invalid args, OpenRouter fail
- `tests/test_renderer_ce.py` — регрессии verbose-плана
- `README.md` — требования, quick start от clone, «Что происходит под капотом», конфигурация
- `docs/example-feedback.md`, `docs/example-fix-plan.md` — примеры артефактов dogfooding

---

## Отклонения от плана

- **Task plans** (`tasks/01-…/plan.md`) не создавались отдельно — работа велась по sprint `plan.md` (cloud-style).
- **CE-события** на dogfooding `./` (~56 файлов) не всегда срабатывают — контекст ~22K / 120K; механика проверена в Sprint 05, в Sprint 07 подтверждены субагенты и навыки.
- **[Высокий] из fix_plan** закрыт post-dogfooding: `tests/test_cli.py`, не в исходном scope Task 01.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Исключать `sprints/` и `concept/` вместе с `workspace/` | Не код студента; снижает шум и объём индекса |
| Smoke E2E через mock orchestrator | CI без LLM; проверка wiring CLI → retrieval → feedback panel |
| Verbose-шаги на `completed`, не только `in_progress` | Агент часто пропускает `in_progress`; иначе пустой прогресс в логе |
| Примеры артефактов в `docs/` | README ссылается на реальный output dogfooding |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| `code/` мог включать служебные каталоги при `check .` | `SKIP_DIR_NAMES` в `retrieval.py` |
| Verbose: план показывал 1 шаг, прогресс только на синтезе | `on_plan_update`: completed + refresh панели |
| Compact-панель «Хорошо» пустая при заголовке «Что хорошо» | `_extract_section(..., "Хорошо", "Что хорошо")` |
| Fix Plan в панели без приоритетов | `_parse_fix_plan_lines` сохраняет `### [Высокий]` |
| Gemini Flash: retry при ранней остановке | Штатный retry (до `AGENT_MAX_ATTEMPTS`); прогон завершается |

---

## Dogfooding

| Прогон | Результат |
|--------|-----------|
| `. "CLI-утилита на Python" --verbose` | 5 субагентов, `python-cli.yaml`, modern-python, feedback/fix_plan с приоритетами |
| `. "CLI-утилита на Python" --compact` | Завершён, Feedback + Fix Plan |
| `. --verbose` (без темы) | auto Python CLI, 56 файлов, без ложного README |
| `code/` | `mentor/`, `tests/` есть; `workspace/`, `sprints/`, `concept/` нет |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `mentor check . --verbose` без ошибок | ✅ |
| 2 | `feedback.md` — адресные находки | ✅ |
| 3 | `fix_plan.md` — приоритеты | ✅ |
| 4 | Verbose: план, субагенты, навыки | ✅ (CE — по объёму контекста) |
| 5 | `code/` без рекурсии workspace | ✅ |
| 6 | `--compact` корректен | ✅ |
| 7 | README + quick start | ✅ |
| 8 | Нет ложного «README отсутствует» | ✅ |
| 9 | `make ci` → exit 0 | ✅ (105 тестов) |

---

## Что дальше

- **v1.1 (roadmap):** Checkpoint / Resume — LangGraph persistence
- **Хвост fix_plan [Средний]:** расширить README (зависимости, `.env`, примеры вывода команд)
- **Хвост fix_plan [Низкий]:** stderr для ошибок, exit codes 2/3, TypedDict для todos
- **Хвост (не блокирует):** пустая панель «Хорошо» при нестандартной структуре `feedback.md` от LLM

---

## Ссылки

- [roadmap.md](../../roadmap.md) — v1.0 закрыт
- [docs/example-feedback.md](../../docs/example-feedback.md)
- [docs/example-fix-plan.md](../../docs/example-fix-plan.md)
