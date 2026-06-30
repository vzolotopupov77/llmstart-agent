# Датасет: e2e-regression

**Группа (слой):** e2e
**Текущая версия:** v001 (`v001_2026-06-30.yaml`)
**Changelog:** [v001-changelog.md](./v001-changelog.md)
**Формат:** YAML (E-12)

## Что проверяет

Быстрый regression-loop для Task 08 fix-generation: сабсет single-hop / sales-QA items из
`e2e-qa v002`, на которых routing-прогон (prompt v4) стабильно проседал по `answer_correctness`,
плюс «зелёные» guard-items для контроля анти-регрессии. Позволяет итерировать prompt/generation
на 11 items вместо полного прогона 26.

## Состав (11 items)

| reg id | source (e2e-qa) | роль | тема |
|--------|-----------------|------|------|
| e2e-reg-0001 | e2e-qa-0001 | low | формат комбо |
| e2e-reg-0002 | e2e-qa-0003 | low | время/длительность занятий |
| e2e-reg-0003 | e2e-qa-0005 | low | структура интенсива |
| e2e-reg-0004 | e2e-qa-0008 | low | вечерний поток (objection) |
| e2e-reg-0005 | e2e-qa-0012 | low | CPO без кода, комбо |
| e2e-reg-0006 | e2e-qa-0022 | low | рассрочка (MVP mock) |
| e2e-reg-0007 | e2e-qa-0023 | low | sync-objection (multi) |
| e2e-reg-0008 | e2e-qa-0024 | low | таймзона SF (multi) |
| e2e-reg-0009 | e2e-qa-0014 | guard | веб для физлица |
| e2e-reg-0010 | e2e-qa-0016 | guard | оплата agents |
| e2e-reg-0011 | e2e-qa-0026 | guard | оплата agents (multi) |

## Источник эталонов

`expected_output` скопированы **дословно** из `e2e-qa v002` (без правки критериев — E-13/E-14).
Новые `id` (`e2e-reg-*`), т.к. id items в Langfuse уникальны на проект; исходный id — в `legacy_id`.

## Метрики

Те же, что у e2e-qa (e2e evaluator bundle): `answer_correctness` (главная), guard `faithfulness`,
`task_completion`, `segment_match`, `task_error`.

## Зеркало в Langfuse (E-16)

`e2e/e2e-regression/v001`
