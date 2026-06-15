# Plan: Задача 06 — Отчёт анализа baseline

> **Спринт:** [../../README.md](../../README.md) · **Статус:** ✅ Done

## Цель

Из локального JSON прогона (E-27) — markdown-отчёт: сводка vs пороги, распределение, топ-5 худших items со слоем провала.

## Состав

- [x] `analyze_run.py` — читает `evals/reports/runs/<run>.json`, пишет `evals/reports/<run>.md`
- [x] `failure_analysis.py` — классификация retrieval / generation / behavior
- [x] Опционально: span-evidence из Langfuse session trace (session_id)
- [x] Тесты на классификацию и загрузку отчёта
- [x] Прогон на baseline + summary (⛔ review pending)

## DoD

| # | Критерий |
|---|----------|
| 1 | `make eval-analyze RUN=<name>` → `.md` в `evals/reports/` |
| 2 | Разделы: сводка, пороги, распределение, топ-5, рекомендации |
| 3 | Слой провала + trace/session ссылка у каждого топ-5 |
| 4 | ⛔ Пользователь читает отчёт |
