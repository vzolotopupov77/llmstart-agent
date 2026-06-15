# Plan: Задача 05 — Runner + evaluators + baseline

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md)
> **Статус:** ✅ Done

## Цель

Baseline-прогон реального агента по `e2e/e2e-qa/v001` одной командой (`make eval-experiment`): Langfuse Dataset Run со scores, полный `run_metadata` (E-9), локальный JSON-отчёт (E-27).

## Соответствие методологии

- **E-3/E-6** — task бьёт в `POST /api/v1/chat` с `config_id` из run-config
- **E-9** — имя рана `{config_id}--{dataset}--{git_sha8}--{ISO-ts}`; `run_metadata` = конфиг + judge + dataset@version + git_sha
- **E-17** — judge из `judge:` в YAML, отдельно от модели агента
- **E-18/E-19** — item evaluators + run-level `error_rate`, reasoning судьи в `comment`
- **E-25** — run-level ключи только в `run_metadata`; SDK pin в lockfile
- **E-27** — `evals/reports/runs/<run_name>.json` (schema v2)

**Входы:** ✅ [metrics-map.md](../../../../eval/metrics-map.md), ✅ `e2e/e2e-qa/v001` в Langfuse, ✅ `baseline-react-chroma.yaml`

**Skills:** langfuse (Experiments SDK), metrics-guide

---

## Состав работ

### 5.1 Зависимости и инфраструктура judge

- [ ] **5.1.1** Добавить в `evals/pyproject.toml`: `httpx`, `deepeval`, `ragas` (pin в lockfile, E-25)
- [ ] **5.1.2** `evals/scripts/judge_client.py` — фабрика LLM для judge через OpenRouter (`OPENAI_API_KEY` + `OPENAI_BASE_URL` из `.env`, модель из `RunConfig.judge`)
- [ ] **5.1.3** Preflight в `run_experiment.py`: backend health (`GET /health` или chat smoke), Langfuse auth, OpenRouter key

### 5.2 Agent task (E-3)

- [ ] **5.2.1** `evals/scripts/agent_task.py` — HTTP-клиент к Agent Core:
  - single-turn: один `POST /api/v1/chat` (`channel: web`, `config_id`)
  - multi-turn: последовательные вызовы с одним `session_id` — только **user**-реплики из `input[]`; leading `assistant` в эталоне — контекст датасета, не replay (ограничение API)
  - output: `{ "message", "session_id", "trace_id" (из Langfuse metadata если доступен), "tools", "error" }`
- [ ] **5.2.2** Timeout + retry 1× на 503; исключения → `output=None` (не ронять весь ран, E-19)

### 5.3 Evaluators (только e2e-qa, metrics-map)

- [ ] **5.3.1** `evals/scripts/evaluators.py`:
  | Метрика | Тип | Реализация |
  |---------|-----|------------|
  | `task_error` | item, A | `output is None` → 1.0 |
  | `segment_match` | item, A | exact match `expected_output.segment` vs metadata/trace |
  | `answer_correctness` | item, GEval | criteria из `answer_key_points` (+ `must_not`) |
  | `faithfulness` | item, RAGAS | контекст из Langfuse trace (tool spans `search_knowledge_base`); skip→0 + comment если trace пуст |
  | `task_completion` | item, DeepEval | `TaskCompletionMetric` по input + final answer (+ multi-turn input как контекст) |
- [ ] **5.3.2** Run-level: `error_rate`, `avg_answer_correctness`, `avg_faithfulness`, `avg_task_completion`, `segment_match_rate`
- [ ] **5.3.3** Factory `get_e2e_evaluators(judge_config)` — judge model inject один раз

### 5.4 Runner

- [ ] **5.4.1** `run_experiment.py`:
  - загрузка `RunConfig`, резолв dataset slug → Langfuse name `e2e/e2e-qa/v001` (из `config.datasets` + manifest)
  - `langfuse.get_dataset(...).run_experiment(name, task, evaluators, run_evaluators, metadata=run_metadata)`
  - `run_metadata`: `full_config_snapshot`, `judge`, `git_sha`, `langfuse_dataset`, `dataset_version`
- [ ] **5.4.2** Запись `evals/reports/runs/<run_name>.json` (schema v2) после прогона
- [ ] **5.4.3** Строка в `evals/reports/experiments-log.md` (🚧 → ✅)
- [ ] **5.4.4** CLI: `--config`, `--dataset`, `--dry-run` (1 item), `--no-ui` (plain logs)

### 5.5 Тесты

- [ ] **5.5.1** Unit: `segment_match`, `task_error`, run-level aggregates (без LLM)
- [ ] **5.5.2** Unit: run name builder (E-9 format)
- [ ] **5.5.3** Unit: multi-turn input parser (user messages extraction)
- [ ] **5.5.4** Mocked GEval smoke (patch judge client)

### 5.6 Baseline-прогон

- [ ] **5.6.1** `make dev-backend` + `make eval-experiment CONFIG=configs/baseline-react-chroma.yaml DATASET=e2e/e2e-qa`
- [ ] **5.6.2** Evidence в summary: Dataset Run URL, 3 item scores, run_metadata snapshot
- [ ] **5.6.3** ⛔ **СТОП:** пользователь открывает ран в Langfuse — понятно ЧТО прогонялось (E-9)

---

## Scope

**Входит:** e2e-qa v001, baseline config, evaluators по metrics-map для e2e, локальный JSON, experiments-log

**Не входит:** `analyze_run.py` (задача 06), `compare_runs.py`, Rich Live UI (E-32 — plain progress), `check_langfuse_contracts`, остальные датасеты

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | `make eval-experiment` завершается на e2e-qa | exit 0 |
| 2 | Langfuse Dataset Run с scores на items | UI / CLI |
| 3 | `run_metadata` восстанавливает конфиг (E-9) | JSON snapshot |
| 4 | `task_error` + `error_rate` (E-19) | scores present |
| 5 | Judge reasoning в `comment` GEval items | sample item |
| 6 | Локальный JSON schema v2 (E-27) | файл в `reports/runs/` |
| 7 | Unit-тесты evaluators/runner | pytest green |
| 8 | ⛔ Пользователь проверил ран в UI | summary evidence |

---

## Артефакты

- `evals/scripts/run_experiment.py` (реализация)
- `evals/scripts/evaluators.py`
- `evals/scripts/agent_task.py`
- `evals/scripts/judge_client.py`
- `evals/scripts/run_report.py` (writer JSON v2)
- `evals/tests/test_evaluators.py`, `test_run_experiment.py`
- `evals/reports/runs/<baseline-run>.json`
- `evals/reports/experiments-log.md`

---

## Риски

| Риск | Митигация |
|------|-----------|
| Faithfulness без chunk_ids | контекст из tool spans trace; comment при пустом retrieval |
| Multi-turn без replay assistant | replay только user turns + session_id; задокументировать в summary |
| DeepEval/RAGAS + OpenRouter | `judge_client` + env; fail-fast preflight |
| 26 items × judge = cost/time | `--dry-run` для отладки; sequential concurrency=1 по умолчанию |
| Backend не запущен | preflight health check с понятной ошибкой |

---

## Команды проверки

```bash
make eval-validate
make dev-backend   # отдельный терминал
make eval-experiment CONFIG=configs/baseline-react-chroma.yaml DATASET=e2e/e2e-qa
make eval-experiment CONFIG=configs/baseline-react-chroma.yaml DATASET=e2e/e2e-qa  # повтор — новый run_name (не идемпотентен по дизайну)
```
