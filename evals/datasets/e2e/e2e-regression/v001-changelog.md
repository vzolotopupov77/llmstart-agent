# Changelog: e2e-regression v001

> **Task:** sprint-09 Task 08 fix-loop · **Base:** e2e-qa v002_2026-06-15.yaml · **Date:** 2026-06-30

## Summary

Новый regression-датасет (11 items) для fix-generation-loop по low-AC e2e items.
Inputs и `expected_output` скопированы из `e2e-qa v002` без изменений; `id` перенумерованы в
`e2e-reg-*` (Langfuse item id — project-global), исходный id сохранён в `metadata.legacy_id`.

## Состав

- **8 low-items** (стабильно < 0.5 AC на routing v4): 0001, 0003, 0005, 0008, 0012, 0022, 0023, 0024.
- **3 guard-green** (≈1.00 AC, контроль анти-регрессии): 0014, 0016, 0026.

## Note

Датасет — измерительный инструмент, не источник новых эталонов. При правке критериев — менять
в `e2e-qa` и пересобирать regression от него.
