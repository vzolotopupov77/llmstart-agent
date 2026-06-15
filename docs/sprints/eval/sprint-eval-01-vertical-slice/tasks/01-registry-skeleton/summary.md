# Summary: Task 01 — Реестр конфигов + каркас evals/

> **План:** [plan.md](./plan.md)
> **Дата закрытия:** 2026-06-14

---

## Что реализовано

- `evals/` — каркас контура: Makefile, configs, scripts (stub), tests, reports
- `evals/configs/baseline-react-chroma.yaml` — baseline prod-системы (E-5/E-7)
- `evals/configs/benchmark-gpt-4o.yaml` — benchmark-only, отличие только модель (E-8)
- `backend/app/agent/run_config.py` — Pydantic `RunConfig` + загрузчик YAML
- `backend/app/agent/config_registry.py` — реестр, кэш `ReactRunner` по `config_id` (E-6)
- `backend/app/agent/react_runner.py` — явные `model_name` / `temperature`
- `ChatRequest.config_id` + metadata Langfuse (`config_id`, `model`)
- Корневой `Makefile` — цели `eval-validate`, `eval-sync`, `eval-experiment`, `eval-analyze`, `eval-compare`

---

## Отклонения от плана

- `prompt.source: code` вместо `langfuse` — промпт ещё в `prompts.py`, Langfuse PM (E-10) не подключён; зафиксировано явно в baseline.
- Без `config_id` — env Settings (prod), а не принудительный baseline YAML; baseline применяется при явном `config_id: baseline-react-chroma`.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Реестр в backend, YAML в `evals/configs/` | E-3: eval бьёт в prod API; конфиги — git source of truth (E-1) |
| `evals/pyproject.toml` зависит от backend | единая схема `RunConfig`, без дублирования |
| Stub-скрипты exit 0 | вертикальный срез eval-01; наполнение в задачах 04–06 |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `config_id` меняет поведение (E-6) | ✅ unit-тест + разные `model_name` |
| 2 | Структура `evals/` | ✅ |
| 3 | make-цели eval | ✅ `make eval-validate` |
| 4 | Baseline описывает систему (E-5) | ✅ утверждено пользователем |
| 5 | Baseline исполняем | ✅ |
| 6 | Prod без `config_id` = env | ✅ |
| 7 | Lint / тесты | ✅ 45 backend + 2 eval |

---

## Что дальше

- **Задача 02:** `docs/eval/dataset-map.md` — карта датасетов по слоям e2e/rag/behavior/edge (⛔ гейт)

---

## Ссылки

- [Sprint README](../../README.md)
- [Roadmap eval](../../../../roadmap-eval.md)
