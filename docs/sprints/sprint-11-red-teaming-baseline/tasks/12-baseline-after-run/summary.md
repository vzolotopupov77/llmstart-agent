# Summary: Task 12 — baseline-after-run

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/baseline-after/`](../../../../../practice/redteam/baseline-after/), [`practice/redteam/comparison.md`](../../../../../practice/redteam/comparison.md)
> **Дата закрытия:** 2026-08-15

---

## Что реализовано

- Канонический `promptfoo redteam eval` (не `run`) на замороженном наборе: **eval-hvm-2026-08-15T16:28:29**.
- `practice/redteam/baseline-after/` — json, html, лог CLI, `run-manifest.md`.
- `practice/redteam/comparison.md` — порог delta до трактовки, таблица плагинов, статусы F-01…F-25, регрессии, доля маркера, ручные кейсы.

### Метрики «после» vs «до»

| Метрика | До (Eox) | После (hvm) |
|---|---|---|
| Кейсов | 138 / 138 | 138 / 138 |
| Pass / fail / errors | 88 / 50 / 0 | 113 / 25 / 0 |
| ASR | 36.23% | **18.12%** (Δ −18.11 п.п., сигнал) |
| `[SECURITY_BLOCKED]` | 0 | 7 / 138 (5.1%) |
| Длительность | 42.63 мин | 60.39 мин |
| Exit code | 100 | 100 |

SHA-256 без изменений: конфиг `300F1360…D837`, tests `830B02F9…938B`. Canary тот же.

Находки: **closed 13** · **partial 4** · **open 7**. Продуктовых регрессий в автонаборе нет (3 «pass→fail» — шум грейдера).

---

## Отклонения от плана

- Ветка `docs/sprint-11-12-baseline-after-run` не создавалась: спринт 11 незакоммичен на `main`.
- Commit фиксов в манифесте нет: HEAD всё ещё `36a94ce`, FIX-1…FIX-5 в рабочем дереве.
- **Hotfix denylist после eval** (явное решение пользователя): URL вырезаются перед проверкой `product_id` / `session_id`. Повторный `redteam eval` не делали — согласовано.

---

## Принятые решения

| Решение | Причина |
|---|---|
| Порог: ≤2 кейса на плагин / <2.2 п.п. ASR = шум | Зафиксирован до трактовки чисел |
| 7 маркеров ≠ ложно-зелёный | 5.1% набора, не ~100% |
| Open/partial — backlog | Не провал спринта |
| Не повторять eval после hotfix URL | Одноходовки набор не ловят; баг поймала ручная воронка |

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| `make dev` упал перед ручными кейсами | Backend снова поднят; `/ready` 8 tools |
| `session_id` в воронке — UUID, не произвольная строка | Первый ход без id, дальше из ответа |
| Mock-URL → `[SECURITY_BLOCKED]` | Hotfix: не матчить имена params внутри `https?://…`; pytest 17 + живая ссылка в `message` |
| Exit 100 | Fail-кейсы грейдера, 0 транспортных ERROR |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | `baseline-after/` и `comparison.md` | ✅ |
| 2 | sha256 = задача 08 | ✅ |
| 3 | canary не изменился | ✅ |
| 4 | `redteam eval`, не `run` | ✅ |
| 5 | `SECURITY_ENABLED=true` и commit фиксов | ✅ флаг; SHA коммита нет (дерево незакоммичено) |
| 6 | F-01…F-25: closed/partial/open | ✅ |
| 7 | раздел регрессий | ✅ |
| 8 | доля маркера оба прогона | ✅ 0 / 7 |
| 9 | порог delta до трактовки | ✅ |
| 10 | ручные `config_id` и воронка | ✅ |
| 11 | `git diff` yaml пустой | ✅ |

**Пользователь проверяет:** ✅ 2026-08-15 (pass rate не от сплошного блока; порог; backlog; воронка; hotfix URL без нового eval).

---

## Что дальше

- **Задача 13** — `final-report.md`, антипаттерны, backlog (open/partial + D-01…D-12), «как повторить», обновить `docs/roadmap.md`, закрыть спринт.
- Yaml и `baseline-before/` не трогать. Повтор — только `redteam eval`.
- После hotfix перезапустить `make dev`, чтобы `:8003` подхватил denylist.

---

## Ссылки

- Манифест: `practice/redteam/baseline-after/run-manifest.md`
- Сравнение: `practice/redteam/comparison.md`
- Skill: `.agents/skills/promptfoo-redteam-run/SKILL.md`
- Предыдущая: [summary задачи 11](../11-fixes-implementation/summary.md)
- Следующая: [plan задачи 13](../13-final-report-roadmap/plan.md)
