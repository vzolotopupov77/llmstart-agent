# Summary: Sprint 05 — context-engineering

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-07-19

---

## Что реализовано

- `mentor/ce.py` — `build_ce_middleware()`, `ReportingSummarizationMiddleware` (callback из `ExtendedModelResponse`, т.к. `_summarization_event` — private state), `make_write_to_workspace_tool()`, `ce_keep_tokens()`, порог компактизации ≥85% `context_limit`
- `mentor/events.py` — `FileOffloadEvent`, `SummarizationEvent`, `CompactionEvent` (+ `dedupe_key`)
- `mentor/agent.py` — CE middleware в оркестраторе, `on_summarization` → CE-панели, мягкий return при отсутствии брифа в `spawn_reviewer`
- `mentor/tracker.py` — перехват CE из stream и callback; dedupe суммаризации; fallback отключён при `run_context`
- `mentor/renderer.py` — панели «Вынос / Суммаризация / Компактизация», секция CE в «Контекст за сессию»; **max** экономии за раз (не sum) для summarization/compaction
- `mentor/feedback_validator.py` — фильтр ложных claims «README отсутствует» по `code-index.md`
- `mentor/config/prompts/orchestrator-system.yaml` — инструкции CE + `write_to_workspace` + `compact_conversation`
- `tests/test_ce.py`, `tests/test_renderer_ce.py`, `tests/test_tracker.py`, `tests/test_feedback_validator.py`, `tests/test_agent.py`

---

## Отклонения от плана

- **SummarizationMiddleware** подключается через `register_harness_profile(excluded_middleware={"SummarizationMiddleware"})` и кастомный middleware с порогами из конфига — не через kwargs `create_deep_agent`
- **`keep`** — абсолютные токены (`ce_keep_tokens`), не `("fraction", 0.1)`: иначе при больших max_input_tokens cutoff=0
- **Компактизация** — классификация overflow-суммаризации при ≥85% `context_limit`, не отдельный compaction-only pipeline
- **Итоговая CE-статистика** — `max(savings)` на тип события; суммирование 14 compactions давало завышенные 119K
- **Триггер compaction-панели** — «≥85% context_limit (10,200 / 12,000)», не «превысил 12,000»

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| CE-события суммаризации из middleware callback, не из stream | `_summarization_event` = `PrivateStateAttr`, не попадает в `stream_mode="updates"` |
| `spawn_reviewer` возвращает soft error при отсутствии брифа | Параллельные tool calls write + spawn роняли orchestrator |
| Тесты CE с `_app_config(monkeypatch)` | Локальный `.env` с низкими порогами ломал `make ci` |
| Dedupe CE-панелей по `dedupe_key` | Дубли summarization в verbose при stream + callback |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| CE-панели суммаризации не видны | `ReportingSummarizationMiddleware` + callback в `agent.py` |
| Дубли панелей и завышенная экономия (205K) | Отключить stream-fallback при callback; dedupe; max в summary |
| Crash `бриф не найден` | Soft return в `_spawn_reviewer_impl` |
| Завышенная «экономия компактизации» 119K | `max` вместо `sum` в `_format_ce_summary` |
| `make ci` падал из-за `.env` override | `_app_config()` в `test_ce.py` |

---

## Dogfooding

| Прогон | Результат |
|--------|-----------|
| `--verbose`, `CONTEXT_LIMIT=12000`, `.` | 15/15 todos; 10× summarization + 3× compaction; feedback/fix_plan; финал 11 195 tok (93% лимита) |
| `--compact`, `.` | 18/18 todos; feedback/fix_plan; без CE-панелей (ожидаемо) |
| README false positive | Не воспроизведён |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Summarization при `summarization_threshold` | ✅ verbose: 10× панель |
| 2 | Compaction при `context_limit` | ✅ verbose: 3× панель, порог 10 200 |
| 3 | Verbose CE-панели: механизм, до/после, экономия | ✅ |
| 4 | Агент продолжает после CE | ✅ feedback.md после суммаризации/compaction |
| 5 | Параметры из config/.env | ✅ limit 12K, threshold 10K в dogfooding |
| 6 | Compact без регрессий | ✅ 18/18, todos + Feedback |
| 7 | `make ci` → exit 0 | ✅ 65 тестов |

**Carry-over README-validator:** ✅ нет ложного «README отсутствует»

---

## Что дальше

- **Sprint 06 (rubrics-skills):** тематические рубрики + публичные skills
- **Хвост (не блокирует):** `render.py` ищет секцию «Хорошо», агент пишет «Что хорошо» — compact-панель показывает пустое «Хорошо» при полном `feedback.md`
- **Хвост:** явный `max_tokens` в `build_chat_model` — снизить риск OpenRouter pre-check при малом балансе

---

## Ссылки

- [roadmap.md](../../roadmap.md) — v0.3 закрыт
- [sprint-06-rubrics-skills/plan.md](../sprint-06-rubrics-skills/plan.md)
