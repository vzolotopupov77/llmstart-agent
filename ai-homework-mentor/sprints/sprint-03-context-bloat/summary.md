# Summary: Sprint 03 — context-bloat

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-18

---

## Что реализовано

- `mentor/events.py` — `PlanEvent`, `FileEvent`, `ContextEvent`
- `mentor/tracker.py` — `stream_with_tracking()`: парсинг `messages` из `stream(updates)`, carry-over токенов между retry
- `mentor/renderer.py` — `VerboseRenderer`: план, файлы, рост контекста, итоговая панель
- `mentor/agent.py` — интеграция verbose-трекинга; `agent_recursion_limit` / `agent_max_attempts` из конфига
- `mentor/cli.py` — verbose через `VerboseRenderer`; итоговая панель контекста даже при ошибке агента
- `mentor/config/` — приоритет `.env` над `config.yaml`; `MODEL`, `AGENT_RECURSION_LIMIT`, `AGENT_MAX_ATTEMPTS`
- `tests/test_tracker.py` — 11 unit-тестов трекера
- `README.md` — модули `renderer.py`, `tracker.py`

---

## Отклонения от плана

- Трекинг через **callbacks** (`on_chat_model_end`) заменён на парсинг **`AIMessage` из updates** — callbacks LangGraph не доходят до LLM при `agent.stream()`
- `AsyncIterator` заменён на **синхронный** поток (CLI Typer sync)
- Дополнительно (не в plan.md): fix приоритета `MODEL` в конфиге; `agent_recursion_limit` 100→200; `agent_max_attempts` 5→10; carry-over токенов между retry

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| `usage_metadata.input_tokens` из `AIMessage` в updates | Надёжный источник токенов без callbacks |
| `tool_calls` на `AIMessage` для файлов | `on_tool_end` не получает `name` / не вызывается |
| Carry-over `session_tokens` между retry | Иначе ложные «0 → 31K (+31K)» при continue в том же thread |
| Fresh thread: `input_tokens < prev` → сброс `tokens_before` | Новый `thread_id` — окно LLM начинается заново |
| Итоговая панель до сообщения об ошибке | Образовательная цель спринта — показать боль даже при неполной проверке |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| Verbose без строк контекста (callbacks молчат) | Парсинг `messages` из `stream(updates)` |
| «0 → N» на каждом retry при растущем окне | Carry-over `session_tokens` + детекция fresh thread |
| Дубли `📄 Прочитан` | Убран повторный preview в `on_context_event` |
| `MODEL` из `.env` игнорировался | `yaml` + `env.model_dump(exclude_unset=True)` вместо `AppConfig(**yaml)` |
| Ttlg (442 файла) упирается в шаги, не в контекст | `AGENT_RECURSION_LIMIT=200`, настраивается через `.env` |

---

## Наблюдаемый паттерн для Sprint 04 (carry-over)

1. **README:** агент ищет `README.md` в корне workspace, не `code/README.md` — ложное «README отсутствует» при dogfooding.
2. **Пути вне `code/`:** модель читает `backend/src/...` или `/submission.md` вместо `code/backend/...` — verbose показывает `⚠ Путь вне code/`. Fix — явные пути в промптах/брифах субагентов (Sprint 04).

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `--verbose` показывает размер контекста после каждого шага | ✅ |
| 2 | Live-обновление плана (todo) | ✅ |
| 3 | Прочитанные файлы на каждом шаге | ✅ |
| 4 | Итоговая панель: рост контекста и % от лимита | ✅ |
| 5 | `--compact` без изменений | ✅ |
| 6 | `make ci` → exit 0 | ✅ (31 тест) |

---

## Что дальше

- **Sprint 04 (subagents-isolation):** Reviewer-субагенты; verbose показывает контраст чистого контекста; fix путей `code/` в брифах
- **Sprint 05:** валидация синтеза против `code-index.md`
- v0.1 на репо 400+ файлов может не завершиться — ожидаемо до субагентов

---

## Ссылки

- [roadmap.md](../../roadmap.md) — v0.2, Sprint 03 закрыт
- [sprint-04-subagents-isolation/plan.md](../sprint-04-subagents-isolation/plan.md)
