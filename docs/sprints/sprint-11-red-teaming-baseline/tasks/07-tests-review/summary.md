# Summary: Task 07 — tests-review

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/test-review-notes.md`](../../../../../practice/redteam/test-review-notes.md), [`practice/redteam/redteam-tests.yaml`](../../../../../practice/redteam/redteam-tests.yaml) (без правок)
> **Дата закрытия:** 2026-08-14

---

## Что реализовано

- `practice/redteam/test-review-notes.md` — метод чтения, сквозные проверки, разбор 14 записей плагинов (P1–P4 раздельно) с дословными примерами, оценки `ok`/`concern`/`block`, ожидания до прогона, решение **go**.
- Прочитаны все **48 уникальных ядер** (все `basic`); 90 кейсов стратегий — обёртки тех же ядер, не новые цели.
- `redteam-tests.yaml` и `promptfooconfig.yaml` не редактировались.

### Заморозка набора (подтверждена ревью)

| Файл | SHA-256 |
|---|---|
| `practice/redteam/redteam-tests.yaml` | `830B02F9B88194E9EAEC802306CDBB4F220F269D217F94C1837350907AAE938B` |
| `practice/redteam/promptfooconfig.yaml` | `300F1360C9AE84B6BDA331FFA6873726282AF2B9380AEA1BC6727FBCBAE5D837` |

Дальше до конца спринта оба файла не меняются. Повторный прогон — только `promptfoo redteam eval`.

---

## Отклонения от плана

Состав работ выполнен. Ветка `docs/sprint-11-07-tests-review` не создавалась: спринт 11 лежит незакоммиченным на `main`, как задачи 01–06.

---

## Принятые решения

| Решение | Причина |
|---|---|
| **go** на задачу 08, без перегенерации | `block` = 0; замечания — `concern`, меняют triage, не делают прогон бессмысленным |
| 8 `ok` / 6 `concern` | concern: `prompt-extraction`, P2, P3, P4, `excessive-agency`, `system-prompt-override` |
| Язык: 138/138 ядер русские | Совпадает с RU-only задачи 06; EN только в обёртке `jailbreak-templates` |
| P1 признан валидным | Все ядра — поведение («я оплатил — подтверди»), не порядок вызова tools |
| Слова `session_id`/`config_id` в override — не R-05 | Копия `purpose` внутри payload; полей HTTP нет |

Пользователь подтвердил: идём в прогон, в задаче 09 `concern`-плагины трактуем осторожно.

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| Объём yaml (~5.7k строк, 138 кейсов) | Полный разбор уникальных ядер скриптом + дословное чтение 48 формулировок; метод зафиксирован в notes |
| Все 45 `jailbreak-templates` — один английский шаблон | Не block: стратегии не обязаны давать новые сюжеты; разнообразие = `basic` |
| Часть policy-ядер «уехала» в соседний риск (P2/P3/P4) | `concern`, не перегенерация |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | `test-review-notes.md` существует | ✅ |
| 2 | Раздел по каждому плагину конфига | ✅ 14 записей |
| 3 | Дословный пример атаки | ✅ |
| 4 | Оценка `ok` / `concern` / `block` | ✅ 0 block |
| 5 | Доля русских кейсов vs задача 03 | ✅ 100% ядер |
| 6 | `session_id` / `config_id` не поля запроса | ✅ |
| 7 | Метод чтения описан | ✅ полное покрытие ядер |
| 8 | Решение go / no-go | ✅ go |
| 9 | Ожидания до прогона | ✅ |
| 10 | sha256 тестов не изменился | ✅ `830B02F9…938B` |

**Пользователь проверяет:** ✅ подтверждено 2026-08-14 — язык, P1 как поведение, домен продукта, согласие идти с `concern`, понимание изоляции (один диалог = одно сообщение).

Lint и тесты неприменимы — задача типа `docs`, код приложения не затрагивался.

---

## Что дальше

- **Задача 08 — baseline «до».** `promptfoo redteam eval -c practice/redteam/redteam-tests.yaml` против агента как есть. В run-manifest: sha256 конфига `300F1360…D837`, tests `830B02F9…938B`, Promptfoo `0.122.0`. Не `redteam run`.
- **Задача 09.** Сверять находки с ожиданиями из `test-review-notes.md`; «чисто» по P2/P3/P4 не считать закрытием риска.

---

## Ссылки

- Артефакт: `practice/redteam/test-review-notes.md`
- Набор: `practice/redteam/redteam-tests.yaml`
- Вход: [plugin-selection.md](../../../../../practice/redteam/plugin-selection.md), [summary задачи 06](../06-tests-generation/summary.md)
- Skill: `.agents/skills/promptfoo-redteam-run/SKILL.md`
