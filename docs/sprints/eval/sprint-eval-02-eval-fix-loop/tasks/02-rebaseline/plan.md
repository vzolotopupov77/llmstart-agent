# Plan: Задача 02 — Re-baseline + analyze

> **Спринт:** [../../README.md](../../README.md) · **Статус:** ✅ Done

## Цель

Перепрогон `e2e/e2e-qa/v001` с исправленными evaluators (Task 01) + markdown-отчёт analyze. Сравнение с baseline sprint-eval-01.

## Состав

- [x] Preflight: backend health, Langfuse auth, OPENROUTER key
- [x] `make eval-experiment` → новый run JSON
- [x] `make eval-analyze RUN=<name>` → `.md` отчёт
- [x] Зафиксировать дельту vs `baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z`
- [x] Обновить `experiments-log.md`
- [x] summary + sprint README (⛔ review pending)

## DoD

| # | Критерий |
|---|----------|
| 1 | Новый run JSON в `evals/reports/runs/` с 26 items, error_rate=0 |
| 2 | Analyze report со всеми разделами |
| 3 | В summary — таблица метрик old vs new |
| 4 | ⛔ Пользователь видит новые метрики (осмысленнее baseline 0.135) |

## Артефакты

- `evals/reports/runs/<new-run>.json`
- `evals/reports/<new-run>.md`
- `evals/reports/experiments-log.md`

## Scope

**НЕ трогаем:** agent prompt, manifest, compare_runs (Task 03).
