# Summary: Task 06 — tests-generation

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/redteam-tests.yaml`](../../../../../practice/redteam/redteam-tests.yaml), [`practice/redteam/generate-log.txt`](../../../../../practice/redteam/generate-log.txt), [`practice/redteam/promptfooconfig.yaml`](../../../../../practice/redteam/promptfooconfig.yaml) (RU-only), [`practice/redteam/config-explainer.md`](../../../../../practice/redteam/config-explainer.md)
> **Дата закрытия:** 2026-08-14

---

## Что реализовано

- `practice/redteam/redteam-tests.yaml` — **138** кейсов, сгенерированных `promptfoo redteam generate` (не `run`) по `promptfooconfig.yaml`; все 14 записей плагинов — Success.
- `practice/redteam/generate-log.txt` — полный stdout/stderr, версии, sha256, отчёт Test Generation Report, сверка с бюджетом §11.2.
- После первой генерации (276 кейсов, RU+EN) — осознанное сокращение до **RU-only**: правка `redteam.language`, `testGenerationInstructions`, `config-explainer.md`, перегенерация.

### Заморозка

| Файл | SHA-256 |
|---|---|
| `practice/redteam/promptfooconfig.yaml` | `300F1360C9AE84B6BDA331FFA6873726282AF2B9380AEA1BC6727FBCBAE5D837` |
| `practice/redteam/redteam-tests.yaml` | `830B02F9B88194E9EAEC802306CDBB4F220F269D217F94C1837350907AAE938B` |

Предыдущие хеши (задача 05 / первая генерация): конфиг `B8F37D1D…F2C7`, tests `73950242…A367` — superseded.

Правило: оба файла не редактируются до конца спринта; изменение → перегенерация + перезапуск **обоих** baseline. Повторный прогон — только `promptfoo redteam eval`.

### Покрытие и бюджет

| Метрика | Значение |
|---|---|
| Всего кейсов | 138 |
| Язык | 100% Русский |
| Стратегии | basic 48, jailbreak-templates 45, jailbreak:meta 45 |
| Оценка одного `eval` | ~$0,4, ~10 мин (`maxConcurrency: 2`) |
| Генерация (локальная) | 9 172 токена, 9 запросов |

Кейсы по `pluginId` (после умножения стратегиями): contracts / excessive-agency / hallucination / harmful:specialized-advice / hijacking / model-identification / off-topic — по 9; policy (4 экземпляра) — 42; prompt-extraction / tool-discovery — по 15; system-prompt-override — 3 (strategy-exempt).

---

## Отклонения от плана

| План | Факт | Причина |
|---|---|---|
| Конфиг не трогать (заморожен задачей 05) | `promptfooconfig.yaml` изменён | Явное решение пользователя: убрать полное EN-дублирование (276 → 138 кейсов) |
| DoD п.2: sha256 конфига = задача 05 | Новый sha256 | Следствие правки `language` |
| Scope: только `redteam-tests.yaml`, `generate-log.txt`, `summary.md` | + `promptfooconfig.yaml`, `config-explainer.md` | Необходимо для RU-only; зафиксировано в explainer §4 |

Ветка `feat/sprint-11-06-tests-generation` не создавалась: спринт 11 лежит незакоммиченным на `main`, как задачи 01–05.

---

## Принятые решения

| Решение | Причина |
|---|---|
| RU-only вместо `[Русский, English]` | Promptfoo умножил языки 1:1 (138+138=276); для русскоязычного продукта полный EN-дубль даёт слабый прирост сигнала при удвоении стоимости/времени прогона |
| Jailbreak-стратегии оставлены | Частично компенсируют вектор смены языка без дублирования всех plugin-кейсов |
| Email через stdin (`redteam@llmstart.ru`) | `redteam generate` требует интерактивный work email; pipe — стандартный обход для non-interactive CLI |
| `PROMPTFOO_DISABLE_SHARING=true` | Внутренний таргет; sharing не нужен |

`config-review-checklist.md` (задача 05) устарел по п. 7 (язык) и sha256 конфига — актуальные значения в этом summary и `generate-log.txt`.

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| Первый запуск: «Email Verification Required», интерактивный prompt | Pipe email через `cmd /c "echo redteam@llmstart.ru\| promptfoo …"` |
| Первая генерация: 276 кейсов (50/50 RU/EN) | Обсуждение с пользователем → правка `language` → перегенерация → 138 кейсов |
| PowerShell `Tee-Object` без `-Encoding utf8` ломал лог | Перезапись шапки через `[System.IO.File]::WriteAllText` + append через cmd redirect |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | `redteam-tests.yaml` существует и непустой | ✅ 138 кейсов, ~5.7k строк |
| 2 | sha256 конфига зафиксирован | ✅ `300F1360…D837` (новый после RU-only) |
| 3 | Лог генерации сохранён | ✅ `generate-log.txt` |
| 4 | В логе: версия Promptfoo и commit | ✅ 0.122.0, `36a94ce9` |
| 5 | Кейсы по каждому плагину | ✅ 14/14 Success, 0 пустых |
| 6 | Число кейсов vs бюджет §11.2 | ✅ 138 = нижняя оценка (single locale) |
| 7 | sha256 `redteam-tests.yaml` зафиксирован | ✅ в логе и таблице выше |
| 8 | Файл не редактировался вручную | ✅ только `redteam generate` |

**Пользователь проверяет:** ✅ подтверждено 2026-08-14 — `generate` (не `run`); 138 кейсов приемлемы; все плагины покрыты; набор заморожен до конца спринта.

---

## Что дальше

- **Задача 07 — tests-review.** Выборочное/полное чтение `redteam-tests.yaml`; `test-review-notes.md` с `ok/concern/block` по плагинам; проверка policy P1 на поведенческие формулировки; go/no-go на задачу 08.
- **Задачи 08 и 12.** В run-manifest — sha256 конфига `300F1360…D837`, tests `830B02F9…938B`, Promptfoo `0.122.0`. Команда: `promptfoo redteam eval -c practice/redteam/redteam-tests.yaml`.

Открытых хвостов, блокирующих задачу 07, нет.

---

## Ссылки

- Артефакты: `practice/redteam/redteam-tests.yaml`, `practice/redteam/generate-log.txt`
- Конфиг: `practice/redteam/promptfooconfig.yaml`, `practice/redteam/config-explainer.md`
- Вход: [plugin-selection.md](../../../../../practice/redteam/plugin-selection.md) §11.2, [config-review-checklist.md](../../../../../practice/redteam/config-review-checklist.md) (sha256 устарел)
- Skill: `.agents/skills/promptfoo-redteam-run/SKILL.md`
