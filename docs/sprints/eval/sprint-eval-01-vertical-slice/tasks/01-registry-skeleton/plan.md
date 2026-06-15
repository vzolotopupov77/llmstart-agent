# Plan: Задача 01 — Реестр конфигов + каркас evals/

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md)
> **Статус:** 📋 Planned

## Цель

Конфигурация запуска (`config_id`) реально меняет поведение Agent Core; операции eval-контура (`validate` / `sync` / `experiment` / `analyze` / `compare`) доступны как повторяемые команды; baseline-конфиг описывает текущую прод-систему.

## Соответствие методологии

- **E-2** — операции контура через `make` (корень → `evals/`)
- **E-5** — YAML-конфиг полностью описывает систему (impl, retrieval, model, judge, prompt, datasets)
- **E-6** — `config_id` исполняем: реестр в Agent Core, не декларация
- **E-7** — baseline-файл неприкосновенен; изменения = новый config-файл
- **E-8** — второй конфиг для проверки E-6 с `benchmark_only: true`
- **E-3** — eval бьёт в тот же `POST /api/v1/chat`, не форк агента

**Концепции:** К-2 (трейс фиксирует применённый config), К-5 (baseline как точка отсчёта).

**Противоречий с eval-methodology.md:** нет.

**Отклонение от шаблона run-config (осознанное):**
- `prompt.source: code` — промпт сейчас в `backend/app/agent/prompts.py`, Langfuse Prompt Management (E-10) ещё не подключён; в baseline фиксируем факт, не выдумываем версию в Langfuse.
- `api_url: http://127.0.0.1:8003/api/v1/chat` — фактический порт backend (не 8000 из шаблона).

---

## Состав работ (атомарные шаги)

- [ ] **1.1** Pydantic-модель `RunConfig` + загрузчик YAML → проверка: `cd evals && uv run python -c "from scripts.models import load_run_config; print(load_run_config('configs/baseline-react-chroma.yaml').config_id)"`

- [ ] **1.2** Структура `evals/` (Makefile, configs/, scripts/, tests/, reports/, datasets/ — пустые группы) → проверка: `ls evals/`

- [ ] **1.3** `evals/configs/baseline-react-chroma.yaml` — текущая prod-система (см. раздел «Baseline» ниже) → проверка: ручной diff с Settings + prompts.py

- [ ] **1.4** `evals/configs/benchmark-gpt-4o.yaml` — копия baseline, отличие **только** `model.name: openai/gpt-4o`, `benchmark_only: true` (E-7/E-8) → проверка: diff двух файлов — одно поле model

- [ ] **1.5** Реестр в backend: `app/agent/config_registry.py` — загрузка YAML из `EVAL_CONFIGS_DIR` (default: `{REPO_ROOT}/evals/configs`), кэш `ReactRunner` по `(config_id, model, temperature)` → проверка: unit-тест `test_config_registry.py`

- [ ] **1.6** `ReactRunner` — принимает `model`/`temperature` явно (не только Settings); factory создаёт default runner из env → проверка: `make test-backend`

- [ ] **1.7** `ChatRequest.config_id: str | None` — опционально; `AgentService` выбирает runner из реестра; `config_id` пишется в Langfuse metadata turn → проверка: integration-тест + metadata в trace

- [ ] **1.8** Скелеты скриптов (`sync_datasets.py`, `run_experiment.py`, `analyze_run.py`, `compare_runs.py`) — CLI с `--help`, stub exit 0 + сообщение «not implemented in sprint-01» → проверка: `make -C evals validate` (pytest только config/integrity stub)

- [ ] **1.9** `evals/Makefile` по шаблону; корневой `Makefile` — цели `eval-validate`, `eval-sync`, `eval-experiment`, `eval-analyze`, `eval-compare` → проверка: `make eval-validate`

- [ ] **1.10** Smoke: два запроса с разными `config_id` → в Langfuse metadata разные `config_id` и `model` → проверка: `@pytest.mark.live` или ручной runbook в summary

---

## Baseline-конфиг (содержимое `baseline-react-chroma.yaml`)

| Поле | Значение | Источник |
|------|----------|----------|
| `config_id` | `baseline-react-chroma` | имя файла |
| `agent.impl` | `langchain-react` | `ReactRunner` + `create_agent` |
| `agent.api_url` | `http://127.0.0.1:8003/api/v1/chat` | backend README |
| `retrieval.backend` | `chroma-embedded` | `data/.chroma/`, `ensure_rag_index` |
| `model.name` | `openai/gpt-4o-mini` | `.env.example` default |
| `model.provider` | `openrouter` | Settings |
| `model.temperature` | `0.0` | явно для воспроизводимости eval |
| `judge.*` | `google/gemini-2.5-flash-lite`, temp 0 | шаблон E-17; используется в задаче 05 |
| `prompt.source` | `code` | `prompts.py` |
| `prompt.name` | `agent-system-prompt-v1` | идентификатор для metadata |
| `datasets.e2e-qa` | `v001` | пин; манифест — задача 04 |

---

## Scope

**Входит:**
- `evals/` каркас + baseline/benchmark YAML
- Реестр конфигов и `config_id` в API
- Make-цели eval в корне и `evals/`
- Unit-тесты реестра и загрузки конфига
- Stub-скрипты (без sync/experiment logic)

**Не входит:**
- `dataset-map`, `metrics-map`, манифесты (задачи 02–04)
- Полная реализация sync/run/analyze/compare (задачи 04–06)
- Langfuse Prompt Management (E-10) — отдельная задача при необходимости
- Смена retrieval backend (единственный — chroma-embedded)
- CI regression-gate (v1.0)

---

## DoD (из README спринта, задача 01)

| # | Критерий | Способ проверки |
|---|----------|-----------------|
| 1 | Agent Core принимает `config_id` и применяет конфигурацию (E-6) | POST `/api/v1/chat` с `config_id: benchmark-gpt-4o` → metadata trace: другая модель |
| 2 | Структура `evals/` по методологии | listing + Makefile |
| 3 | Команды validate/sync/experiment/analyze/compare запускаются | `make eval-validate` … `make eval-compare` (stubs OK) |
| 4 | Baseline-конфиг полностью описывает систему (E-5) | ⛔ ревью пользователя |
| 5 | Baseline исполняем (E-6) | запрос без `config_id` ≡ `config_id: baseline-react-chroma` |
| 6 | `benchmark_only` конфиг не меняет prod по умолчанию | без `config_id` — env Settings |

---

## Самопроверка

- [ ] DoD задачи — построчно
- [ ] Чек-лист «При постановке контура»: реестр работает (E-6); runner — prod chain (E-3)
- [ ] Evidence: для E-6 — скрин/metadata trace с двумя config_id (в summary после реализации)

---

## Артефакты

| Путь | Описание |
|------|----------|
| `evals/Makefile` | точка входа операций |
| `evals/pyproject.toml` | uv-проект для scripts/tests |
| `evals/configs/baseline-react-chroma.yaml` | неприкосновенный baseline |
| `evals/configs/benchmark-gpt-4o.yaml` | benchmark-only, другая модель |
| `evals/scripts/models.py` | RunConfig Pydantic + loader |
| `evals/scripts/{sync,run_experiment,analyze,compare}_*.py` | скелеты |
| `evals/tests/test_run_config.py` | загрузка YAML |
| `backend/app/agent/config_registry.py` | реестр |
| `backend/app/api/schemas/chat.py` | поле `config_id` |
| `backend/tests/test_config_registry.py` | unit-тесты |
| `Makefile` (корень) | делегирование `eval-*` |

---

## Риски

| Риск | Митигация |
|------|-----------|
| Кэш runner'ов по model — память | 2 конфига на MVP; LRU при росте |
| `benchmark-gpt-4o` дороже | `benchmark_only: true`, только eval-запросы |
| Prompt не в Langfuse | `source: code` в baseline; E-10 — позже |
