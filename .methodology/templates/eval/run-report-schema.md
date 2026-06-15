# Схема локального отчёта прогона (E-27)

Файл: `evals/reports/runs/<run_name>.json`  
`schema_version`: **2**

## Обязательные поля верхнего уровня

| Поле | Тип | Описание |
|------|-----|----------|
| `run_name` | string | `{config_id}--{dataset}--{git_sha8}--{ISO-ts}` |
| `config_id` | string | Идентификатор run config |
| `dataset_slug` | string | Короткое имя датасета (`e2e-qa`, …) |
| `langfuse_dataset` | string | Полный путь в Langfuse |
| `git_sha` | string | Полный SHA коммита |
| `started_at` / `finished_at` | ISO-8601 | Границы прогона |
| `timing` | object | `total_duration_ms`, `items_total`, `items_with_timing` |
| `judge` | object | `provider`, `name`, `temperature` — модель оценщика |
| `run_metadata` | object | Плоский snapshot параметров прогона |
| `full_config_snapshot` | object | Полный RunConfig после резолва промпта |
| `items[]` | array | Per-item: input, output, scores, `duration_ms`, trace_id |
| `run_scores[]` | array | Агрегаты (`error_rate`, `avg_*`) |
| `langfuse` | object | `dataset_run_id`, `dataset_run_url` (если есть) |
| `source` | string | `experiment` \| `export` |

## Правила

- Каждый `make eval-experiment` **обязан** писать JSON до завершения процесса.
- `analyze` / `compare` читают только локальные JSON, не Langfuse API.
- Judge фиксируется в отчёте независимо от модели агента.
