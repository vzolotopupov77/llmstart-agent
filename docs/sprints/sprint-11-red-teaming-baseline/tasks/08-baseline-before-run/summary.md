# Summary: Task 08 — baseline-before-run

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/baseline-before/`](../../../../../practice/redteam/baseline-before/) (`eval-results.json`, `eval-results.html`, `eval-log.txt`, `run-manifest.md`)
> **Дата закрытия:** 2026-08-14

---

## Что реализовано

- Канонический прогон `promptfoo redteam eval` (не `run`) на замороженном `redteam-tests.yaml`: **eval-Eox-2026-08-14T18:00:18**.
- `practice/redteam/baseline-before/` — json, html, лог CLI, `run-manifest.md`. Директория дальше только чтение.
- Агент без защиты: `SECURITY_ENABLED` в `.env` отсутствует; промпт V1; canary на месте.

### Метрики

| Метрика | Значение |
|---|---|
| Кейсов | 138 / 138 |
| Pass / fail / errors | 88 / 50 / **0** |
| ASR | 36.23% |
| Длительность | 42.63 мин |
| Exit code | 100 (fail-кейсы, не транспорт) |
| Токены CLI | 572 393 |
| `security-blocked-marker` | 0 |

SHA-256 без изменений: конфиг `300F1360…D837`, tests `830B02F9…938B`.

---

## Отклонения от плана

Состав работ выполнен. Ветка `docs/sprint-11-08-baseline-before-run` не создавалась: спринт 11 незакоммичен на `main`, как задачи 01–07.

1. **Attempt 1 отброшен.** `eval-YRW-2026-08-14T17:50:23` прерван: Docker/Qdrant не слушали `:6334`, `vector_search` давал 500. В манифесте помечен как невалидный.
2. **`--remote`.** Нужен, чтобы загрузить провайдер `jailbreak:meta` на eval; кейсы не перегенерировались; `--no-share`.
3. **Длительность ~43 мин vs оценка ~10 мин** задачи 06. На сравнимость «до/после» не влияет: набор тот же.
4. CLI-таблица усечена Promptfoo; источник истины — JSON.

---

## Принятые решения

| Решение | Причина |
|---|---|
| Канон = attempt 2 | Attempt 1 — ложно-битый стек, не baseline |
| 50 fail принимаем | Baseline «до»: fail = находка; 0 errors |
| Warning `confirm_payment` / `save_lead` не чиним здесь | Ожидаемое поведение без guard; разбор в задаче 09 |
| `baseline-before/` заморожен | Сравнение в задаче 12 только на этом срезе |

Пользователь подтвердил: fail’ы «до» ожидаемы, манифест достаточен для повтора, прогон настоящий, директорию не редактируем.

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| Qdrant down на первом старте | Пользователь поднял стек; полный eval заново |
| Зависший node attempt 1 после abort | Процесс остановлен до канонического прогона |
| `--remote` блокировался авто-ревью | Явное «ок» на задачу 08; sharing выключен |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | лог, json, html, манифест | ✅ |
| 2 | `redteam eval`, не `run` | ✅ |
| 3 | sha256 = задачи 06/07 | ✅ |
| 4 | `SECURITY_ENABLED` зафиксирован (отсутствует) | ✅ |
| 5 | Promptfoo, Node, commit, модель, V1, retrieval | ✅ |
| 6 | 138 = 138 | ✅ |
| 7 | exit, длительность, токены | ✅ |
| 8 | доля транспортных ошибок | ✅ 0% |
| 9 | непустые ответы и вызовы tools | ✅ |

**Пользователь проверяет:** ✅ подтверждено 2026-08-14.

Lint и тесты неприменимы — код приложения не менялся.

---

## Что дальше

- **Задача 09 — triage.** Таблица находка → OWASP → слой защиты; ≥1 строка на плагин или «не воспроизвелось». Вход: `eval-results.json` + ожидания `test-review-notes.md` (осторожно с `concern`).
- Конфиг и `redteam-tests.yaml` не трогать. Повтор — только `redteam eval`.

---

## Ссылки

- Манифест: `practice/redteam/baseline-before/run-manifest.md`
- JSON: `practice/redteam/baseline-before/eval-results.json`
- Skill: `.agents/skills/promptfoo-redteam-run/SKILL.md`
- Предыдущая: [summary задачи 07](../07-tests-review/summary.md)
