# Summary: Task 05 — config-review

> **План:** [plan.md](./plan.md)
> **Sprint:** [../../README.md](../../README.md)
> **Артефакты:** [`practice/redteam/config-review-checklist.md`](../../../../../practice/redteam/config-review-checklist.md), [`practice/redteam/promptfooconfig.yaml`](../../../../../practice/redteam/promptfooconfig.yaml) (без правок), [`practice/redteam/config-explainer.md`](../../../../../practice/redteam/config-explainer.md)
> **Дата закрытия:** 2026-08-14

---

## Что реализовано

- `practice/redteam/config-review-checklist.md` — 12 пунктов формального чек-листа, все `pass`; dry-run с фрагментом вывода; sha256 замороженного yaml; правило «задачи 06–12 конфиг не меняют».
- Dry-run живого таргета: `validate config` → `Configuration is valid.`; `validate target` → connectivity passed, session skipped; `eval` двух кейсов (`eval-78X-2026-08-14T15:36:50`) → 2/2 PASS. Доказательства: `practice/redteam/config-review-dry-run.yaml` (копия `targets`, не набор сценариев) и `config-review-dry-run.json`.
- `config-explainer.md` — добавлена ссылка на ревью задачи 05; содержимое блоков не менялось.
- `promptfooconfig.yaml` и `config-generation-prompt.md` не редактировались: расхождений с `plugin-selection.md` не было.

### Заморозка

| Файл | SHA-256 |
|---|---|
| `practice/redteam/promptfooconfig.yaml` | `B8F37D1D01786531B9F56DB74948C70624FE30423D6A1B86760959ADB75EF2C7` |

Изменение конфига дальше требует явного решения и перезапуска обоих baseline.

---

## Отклонения от плана

Состав работ выполнен. Два уточнения по артефактам, не меняющие решения:

1. **Yaml не правился.** План допускал точечные `fail` → правка человеком. Все 12 пунктов сразу `pass`, перегенерации и ручных правок конфига нет. Пункт про замечания в `config-generation-prompt.md` не сработал — системных дефектов генерации не найдено.
2. **Вспомогательный dry-run yaml/json.** План требовал фрагмент вывода в чек-листе; полный JSON и конфиг двух кейсов сохранены рядом, чтобы не копировать 2 КБ ответа только в markdown. Это не `redteam-tests.yaml` и не вход задачи 06.

Ветка `docs/sprint-11-05-config-review` не создавалась: незакрытый спринт 11 уже лежит незакоммиченным на `main`, как задачи 01–04.

---

## Принятые решения

| Решение | Причина |
|---|---|
| Конфиг заморожен as-is, без правок | Сверка с задачей 03 (14 плагинов, P1–P4, V1, entities, стратегии, параметры) совпала; `transformResponse: json.message` подтверждён live-ответом |
| 9-я строка ассерта (`search_knowledge_base`) — не fail пункта «только 8 имён» | Решение задачи 03 §3: имя из V1, признак утечки промпта, не выдуманный инструмент |
| Dry-run — `eval` двух кейсов на копии `targets`, не `redteam generate` | Генерация сценариев — задача 06; здесь проверялся только контракт таргета и извлечение `message` |

Отдельного ADR не требуется.

---

## Проблемы и решения

| Проблема | Как решили |
|---|---|
| `!String(...)` в yaml dry-run парсился как YAML-тег | Javascript-ассерты переписаны block-scalar `value: \|` |
| Backend на момент ревью был остановлен | Поднят `make dev-backend`; `/health` и `/ready` → 200 до прогона |

---

## Итог DoD

**Агент проверяет:**

| # | Критерий | Результат |
|---|---|---|
| 1 | Чек-лист, 12 пунктов `pass` | ✅ `config-review-checklist.md` |
| 2 | Валидация конфига | ✅ `Configuration is valid.` |
| 3 | Dry-run: непустой извлечённый ответ | ✅ `response.output` = plain `message`; 2/2; `list_b2c_products` |
| 4 | Нет расхождений yaml ↔ `plugin-selection.md` | ✅ 14 плагинов, 3 стратегии, policy, entities, `numTests`/`maxConcurrency` |
| 5 | sha256 зафиксирован | ✅ в чек-листе |
| 6 | Конфиг не перегенерировался | ✅ yaml задачи 05 не редактировался |

**Пользователь проверяет:** ✅ подтверждено 2026-08-14 — explainer соответствует модели угроз; dry-run показывает текст `message`, не пустоту/JSON; конфиг заморожен; правок промпта генерации не было.

Lint и тесты неприменимы — задача типа `docs`, код приложения не затрагивался.

---

## Что дальше

- **Задача 06 — tests-generation.** `redteam generate` по **этому** замороженному yaml; фактическое число кейсов сверить с `plugin-selection.md` §11.2 (138 или 276). Конфиг не менять.
- **Задачи 08 и 12.** В run-manifest — sha256 `B8F37D1D…F2C7`, версия Promptfoo `0.122.0`, модели генерации/грейдинга. Повторный прогон только `redteam eval`.

Открытых хвостов, блокирующих задачу 06, нет.

---

## Ссылки

- Артефакты: `practice/redteam/config-review-checklist.md`, `practice/redteam/config-review-dry-run.yaml`, `practice/redteam/config-review-dry-run.json`
- Замороженный конфиг: `practice/redteam/promptfooconfig.yaml`
- Вход: [plugin-selection.md](../../../../../practice/redteam/plugin-selection.md), [config-explainer.md](../../../../../practice/redteam/config-explainer.md), [tooling-setup.md](../../../../../practice/redteam/tooling-setup.md)
- Skills: `.agents/skills/promptfoo-provider-setup/SKILL.md`, `.agents/skills/promptfoo-redteam-setup/SKILL.md`, `.agents/skills/promptfoo-redteam-run/SKILL.md`
- Версия Promptfoo: `0.122.0`
