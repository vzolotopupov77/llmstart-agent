# Patch: eval hygiene + console UX + Langfuse stack (2026-06-10)

Дополнения к [eval-methodology.md](../eval-methodology.md) по итогам sprint eval-01, tasks 08–09 + smoke v002–v004.

## Новые / уточнённые принципы

### E-27. Локальный JSON — source of truth
- Каждый `make eval-experiment` пишет `evals/reports/runs/<run_name>.json` (schema **v2**).
- Поля: `timing`, `judge`, `full_config_snapshot`, `duration_ms` per item.
- `analyze` / `compare` читают только локальные JSON.

### E-28. Judge config обязателен и отделён от агента
- Блок `judge:` в run config — **обязателен** (Pydantic).
- Модель judge фиксируется в JSON-отчёте; не наследуется от `model:` агента.
- Judge должен уметь **structured JSON** для DeepEval/G-Eval; 8B-модели (Llama 3.1 8B) — не подходят.

### E-29. Dataset item ID глобально уникальны в Langfuse
- При subset-версии (`v002`) суффикс в `id`: `e2e-qa-v002-0001`, не переиспользовать id из v001.
- Иначе `create_dataset_item` → 404 «already exists in another dataset».

### E-30. OTEL metadata ≤ 200 символов
- `facts`, `must_not`, `criteria` → `expected_output` в Langfuse payload.
- В metadata только `_count` / `_preview`.
- Тест: `test_metadata_propagation.py` в `make eval-validate`.

### E-31. Версии Langfuse: self-hosted `:3` + SDK 4.x
- Docker-образы self-hosted: `langfuse/langfuse:3` (тега `:4` в Hub нет; v4 — cloud).
- Python SDK 4.x — норма; при server major 3 включается compat patch для `dataset_version`.
- `check_langfuse_versions.py`: сверка **running server** с compose (`:3`), не SDK==Docker major.
- После смены образа / устаревшего server: `make down && make up-langfuse` (pull + recreate).

### E-32. Console UX для долгих прогонов
- `run_experiment.py` — Rich Live dashboard (прогресс, ETA, фазы agent/judge, scores).
- `--no-ui` / non-TTY → plain logs.
- Модуль: `evals/scripts/experiment_console.py`.

### E-33. Langfuse contract preflight (task 09)
- `langfuse_contracts.py` — Pydantic-схемы payload'ов (dataset item, run item, run_metadata).
- `make eval-validate` → `check_langfuse_contracts.py` (smoke `dataset_run_items.create`).
- `check_langfuse_versions.py` — сверка **running server** с compose (`/api/public/health`).

### E-34. Langfuse self-hosted: что исправили (2026-06-10)

**Симптом:** WARNING «Server 3.132 при compose/SDK 4», `Failed to create dataset run item`, `dataset_run_url: null`, UI Dataset Runs без drill-down.

**Корневая причина (три слоя, не путать):**

| Слой | Ошибочное ожидание | Реальность |
|------|-------------------|------------|
| Docker compose | `langfuse:4` | Тега **нет** в Hub; self-hosted только `:3` |
| Running server | «нужен v4» | Старые контейнеры на `:3` без pull (3.132) |
| Python SDK | major == Docker major | SDK **4.x** + server **3.x** — штатно; compat patch для `dataset_version` |

**Исправления в репо:**

1. `devops/langfuse.compose.yml` — `langfuse/langfuse:3`, `langfuse-worker:3`.
2. `Makefile` `up-langfuse` — `docker compose pull` перед `up -d`.
3. `check_langfuse_versions.py` — WARNING только если server ≠ compose major или server недоступен; не требует SDK==Docker.
4. `langfuse_compat.apply_dataset_run_item_compat()` — strip `dataset_version` на server 3.x (остаётся нужным).

**Операционный чеклист перед экспериментом:**

```bash
make down && make up-langfuse   # pull + recreate
curl -s localhost:3300/api/public/health   # version ≥ 3.17x
make eval-validate              # pytest + contracts + version check
```

**Критерий «здоровья»:** `check_langfuse_contracts` → `dataset_run_item ok`; в прогоне — `langfuse_linked: true`, `dataset_run_url` в JSON, 0× `Failed to create dataset run item` в логе.

### E-35. Eval-fix: промпт v002 поверх сильного стека (smoke v004)

- Базовый стек: `google/gemini-2.5-flash` + judge `openai/gpt-4o-mini` (не 8B).
- Итерация качества: `prompt.version: v002` (guardrails + обязательный RAG/`list_b2c_products`).
- На smoke v002: `answer_correctness` +0.10, `response_relevancy` +0.30, `scope_adherence` +0.15 vs v003; `faithfulness` может просесть — смотреть per-item в analyze.
- Конфиг-эталон smoke: `evals/configs/candidate-strong-gemini-v004.yaml`.

### E-36. Итог sprint eval-01 (2026-06-10)

- **Baseline** (`baseline-react-embedded`, prompt v001, v001 20 items): точка отсчёта — e2e 0.31, ood scope 0.42, ugo 0.32.
- **Eval-fix:** guardrails prompt v002 → сильный стек + judge GPT-4o-mini → `candidate-strong-gemini-v004`.
- **Лучший кандидат на smoke v002:** e2e 0.57, ood scope 0.95, ugo 0.65, error_rate 0.
- Полный отчёт: `docs/sprints/eval/sprint-eval-01-vertical-slice/SUMMARY.md`.

## Шаблоны обновлены

- `templates/eval/run-config-template.yaml` — блок `judge`
- `templates/eval/run-report-schema.md` — schema v2
