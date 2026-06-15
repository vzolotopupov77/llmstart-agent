# Plan: Задача 05 — Langfuse dataset_run_items + метрики в UI

> **Спринт:** [../../README.md](../../README.md) · **Методология:** [.methodology/eval/eval-methodology.md](../../../../../../.methodology/eval/eval-methodology.md), patch [E-34](../../../../../../.methodology/eval/patches/2026-06-10-eval-hygiene-and-console.md)
> **Статус:** ✅ Done

## Цель

Метрики eval-прогонов видны в Langfuse UI: Dataset → Runs → drill-down по items со scores. Сейчас runs создаются, но `dataset_run_items=[]` — UI пустой.

## Диагностика (уже выполнена)

| Факт | Деталь |
|------|--------|
| Runs в Langfuse | ✅ `dataset_run_id` есть в JSON (`8486f15b-…`) |
| Items linking | ❌ `dataset_run_items.list()` → 0 для всех прогонов |
| API create | Возвращает 200, но worker не персистит |
| Worker logs | `dataset-run-item-upsert-queue` → Prisma: `min_version` column missing, `monitors`/`pricing_tiers` tables missing |
| Корневая причина | **DB schema отстаёт от образа `langfuse:3.125.0`** — не баг evaluators/runner |

**Skills:** langfuse (CLI/contracts), docker-expert (compose/migrations)

---

## Состав работ

### 5.1 Починить Langfuse stack (infra)

- [ ] **5.1.1** Пересоздать стек с pull образов: `docker compose pull` + `up -d` (или `make up` с pull-шагом в Makefile)
- [ ] **5.1.2** Дождаться миграций Postgres (web healthy, worker без Prisma-ошибок `min_version` / `monitors`)
- [ ] **5.1.3** Если миграции не применились инкрементально — **clean start** по runbook sprint-07 (`down -v` + `up`, ⚠️ потеря traces/datasets в локальном инстансе → повторный `make eval-sync`)
- [ ] **5.1.4** Зафиксировать чеклист в `devops/README.md` (troubleshooting: «Dataset Runs без items / metrics»)

### 5.2 Preflight: Langfuse contracts (E-33)

- [ ] **5.2.1** `evals/scripts/check_langfuse_versions.py` — сверка running server vs compose pin (`/api/public/health`)
- [ ] **5.2.2** `evals/scripts/check_langfuse_contracts.py` — smoke `dataset_run_items.create` + `list` (items > 0 после flush)
- [ ] **5.2.3** `evals/scripts/langfuse_compat.py` — strip `datasetVersion` на server 3.x (если потребуется после тестов)
- [ ] **5.2.4** `evals/Makefile` → `validate` вызывает versions + contracts (после pytest)

### 5.3 Post-run verification в runner

- [ ] **5.3.1** `run_experiment.py` — после прогона: poll `dataset_run_items.list`, записать `langfuse_linked: true/false`
- [ ] **5.3.2** `run_report.py` — fallback `dataset_run_url` (если SDK вернул `null`: `host/project/{project_id}/datasets/{dataset_id}/runs/{run_id}`)
- [ ] **5.3.3** Unit-тест: URL builder + linked-flag logic (без live Langfuse)

### 5.4 Верификация end-to-end

- [ ] **5.4.1** `make eval-validate` — green (contracts ok)
- [ ] **5.4.2** `make eval-experiment … --dry-run` (1 item) → `langfuse_linked: true`, items list ≥ 1
- [ ] **5.4.3** ⛔ Пользователь открывает Dataset Run в UI — видны item scores (answer_correctness, faithfulness, …)
- [ ] **5.4.4** Убрать boilerplate «fix в sprint-eval-02/03» из `analyze_run.py`, `compare_runs.py` (или заменить на «resolved in task 05»)

### 5.5 Документация спринта

- [ ] Обновить sprint `README.md`: задача 05, DoD #6 (Langfuse UI metrics)
- [ ] После апрува DoD — `summary.md`

---

## DoD

| # | Критерий | Проверка |
|---|----------|----------|
| 1 | Worker без Prisma-ошибок `min_version` / `dataset-run-item-upsert` | `docker logs langfuse-worker` |
| 2 | `make eval-validate` включает contracts smoke | exit 0 |
| 3 | Dry-run: `dataset_run_items` ≥ 1 | API list / JSON `langfuse_linked: true` |
| 4 | `dataset_run_url` не null в JSON | `reports/runs/*.json` |
| 5 | UI: Run → items → scores | ⛔ пользователь |
| 6 | Unit-тесты preflight/URL builder | pytest green |

---

## Артефакты

- `evals/scripts/check_langfuse_versions.py`
- `evals/scripts/check_langfuse_contracts.py`
- `evals/scripts/langfuse_compat.py` (если нужен)
- `evals/scripts/run_experiment.py`, `run_report.py`, `langfuse_helpers.py`
- `evals/tests/test_langfuse_contracts.py`
- `evals/Makefile`, корневой `Makefile` (опц. `up-langfuse` с pull)
- `devops/README.md` — troubleshooting section
- `docs/sprints/eval/sprint-eval-02-eval-fix-loop/README.md`

---

## Scope

**Входит:** Langfuse infra fix, preflight scripts, post-run verification, devops docs, sprint docs.

**НЕ трогаем:**
- evaluators, agent, candidate configs (task 04)
- Полный re-baseline 26 items (только dry-run для smoke)
- Rich Live console (E-32) — отдельная задача

---

## Риски

| Риск | Митигация |
|------|-----------|
| `down -v` удалит локальные datasets/traces | После recreate: `make eval-sync` + повторный smoke run |
| Worker/web digest mismatch | Проверка versions script; pin пару образов |
| SDK 3.15 vs server 3.125 | Contracts smoke; compat patch при необходимости |

---

## Команды проверки

```bash
make up                                    # или up-langfuse с pull
make eval-validate
make eval-experiment CONFIG=configs/baseline-react-chroma.yaml DATASET=e2e/e2e-qa  # dry-run через --dry-run в runner
# UI: Datasets → e2e/e2e-qa/v001 → Runs → последний run → scores
```
