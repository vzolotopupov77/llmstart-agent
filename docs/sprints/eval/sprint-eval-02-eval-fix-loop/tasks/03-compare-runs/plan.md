# Plan: Задача 03 — compare_runs

> **Спринт:** [../../README.md](../../README.md) · **Статус:** ✅ Done

## Цель

`make eval-compare RUN_A=… RUN_B=…` → markdown с дельтой run-level и item-level метрик; guard E-16 (одна версия датасета).

## Состав

- [x] `compare_runs.py` — load JSON, validate, delta, markdown
- [x] Unit-тесты (guard, delta, markdown sections)
- [x] Fix Makefile `-m scripts.compare_runs`
- [x] Demo: old broken-judge vs new re-baseline
- [x] summary (⛔ review pending)

## DoD

| # | Критерий |
|---|----------|
| 1 | `make eval-compare` exit 0, `.md` в `evals/reports/` |
| 2 | E-16: ошибка при разных `langfuse_dataset` |
| 3 | Таблица run-level + топ improved/regressed items |
| 4 | ⛔ Пользователь просмотрел compare report |
