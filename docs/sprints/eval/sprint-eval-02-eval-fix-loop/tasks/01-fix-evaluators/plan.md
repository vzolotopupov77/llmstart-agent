# Plan: Задача 01 — Fix GEval + task_completion

> **Спринт:** [../../README.md](../../README.md) · **Статус:** ✅ Done

## Цель

Item-level судьи (`answer_correctness`, `task_completion`) оценивают **текущий** item по его `expected_output.answer_key_points`, без «утечки» контекста соседних items и без generic «payment link» на FAQ-вопросах.

## Проблема (evidence)

Baseline item `e2e-qa-0025` (вопрос про набор в сентябре):
- `expected_output.answer_key_points` — временной барьер, следующий поток, без точной даты
- GEval comment: *«did not create a payment link for agents»* — criteria из другого сценария
- `task_completion` comment корректен → разная логика двух метрик

Гипотезы: singleton `GEval` с mutable `criteria`; judge не видит criteria явно; multi-turn input без акцента на **последний user turn**.

## Состав

- [x] **1.1** Per-item `GEval` instance (или `evaluation_steps` из key_points) — без shared mutable state
- [x] **1.2** Criteria: явно включить `answer_key_points` + `must_not` + «оценивай только ответ на последний user turn»
- [x] **1.3** `task_completion`: передавать `expected_output` / criteria в DeepEval (не только raw input)
- [x] **1.4** Unit-тесты: mocked judge — item A criteria ≠ item B; multi-turn last-turn
- [x] **1.5** Smoke: 3 items — comments релевантны key_points (`scripts/smoke_evaluators.py`)

## DoD

| # | Критерий |
|---|----------|
| 1 | `pytest evals/tests/test_evaluators.py` — новые кейсы green |
| 2 | Smoke на 3 items: GEval comment упоминает key_points item, не «payment link» где не нужно |
| 3 | Нет singleton mutable `criteria` между items |
| 4 | ⛔ Пользователь выборочно проверил 2–3 judge comments после smoke |

## Артефакты

- `evals/scripts/evaluators.py`
- `evals/tests/test_evaluators.py`
- (опц.) `evals/scripts/run_utils.py` — helper для criteria

## Scope

**Трогаем:** evaluators, тесты.

**НЕ трогаем:** manifest, agent prompt, `compare_runs.py`, полный re-baseline (задача 02).

## Риски

- DeepEval GEval API может кэшировать prompt — митigation: новый instance per call
- Judge variance останется — не блокер; цель — **релевантность** criteria, не идеальный score
