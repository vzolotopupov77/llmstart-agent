# Summary: Task 05 — Langfuse dataset_run_items + UI scores

> **План:** [plan.md](./plan.md)
> **Дата:** 2026-06-15

## Что сделано

### Infra (мягкий путь, без `down -v`)

- **Корень:** `langfuse-web:3.125.0` + worker digest **3.181.0** → worker Prisma errors, `dataset_run_items` не персистились
- **Фикс:** оба образа → **`3.185.0`**, `make up` с `pull` перед `up -d`
- Миграции применились: `All migrations have been successfully applied`
- Troubleshooting в `devops/README.md`

### Eval contour

- `check_langfuse_versions.py`, `check_langfuse_contracts.py` → `make eval-validate`
- `run_experiment.py`: `langfuse.linked`, poll `dataset_run_items`
- `run_report.py`: fallback `dataset_run_url`, поле `linked`
- `backfill_dataset_run_items.py` + `make eval-backfill-runs` — восстановление старых прогонов из JSON

### Backfill исторических runs

| Run | Items linked |
|-----|--------------|
| `…182021Z` (dry) | 1/1 |
| `…182238Z` (baseline broken judge) | 26/26 |
| `…083100Z` (re-baseline) | 26/26 |
| `…094214Z`, `…094647Z` (candidate) | 26/26 |
| `…100746Z`, `…100916Z` (dry) | 1/1 |
| `…105250Z` | уже linked (новый прогон) |

## DoD

| # | Критерий | ✅ |
|---|----------|---|
| 1 | Worker без Prisma-ошибок | ✅ |
| 2 | `make eval-validate` + contracts | ✅ |
| 3 | Dry-run `linked: true` | ✅ |
| 4 | `dataset_run_url` в JSON | ✅ |
| 5 | Backfill старых runs | ✅ 7/7 JSON |
| 6 | pytest | ✅ 42 passed |

## Проверка в UI

Dataset `e2e/e2e-qa/v001` → Runs — у re-baseline и candidate должны быть items + scores.

Пример: `…083100Z` → http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/datasets/cmqe0gb320001qf07auwu9h56/runs/8486f15b-0ee6-4e51-a1b8-d4e9aee6e570

## Команды

```bash
make up
make eval-validate
make eval-backfill-runs          # все JSON
make eval-backfill-runs RUN=…    # один run
```
