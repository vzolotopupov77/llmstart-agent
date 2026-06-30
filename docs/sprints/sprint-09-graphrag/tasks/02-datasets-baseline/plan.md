# Plan: Task 02 — datasets-baseline

> **Sprint:** sprint-09-graphrag  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-26

---

## Цель

Синтезировать сегментные мини-датасеты (multi-hop, global) и прогнать текущий Qdrant-hybrid как baseline для последующего сравнения с GraphRAG.

---

## Состав работ

- Синтезировать **multi-hop датасет**: 10–12 вопросов с эталонными ответами и `required_entities`. Охват: prerequisite-цепочки, состав комбо, зависимости тем.
- Синтезировать **global датасет**: 6 вопросов-агрегатов с эталонными ответами.
- Задать сегментную метрику: `answer_correctness` по сегментам, `required_entity_recall@5`, `faithfulness`.
- Создать `evals/configs/graphrag-baseline.yaml`.
- Прогнать `make -C evals experiment` на Qdrant-hybrid.
- Сохранить baseline-отчёт `evals/reports/graphrag-baseline.md`.

---

## DoD

| # | Критерий |
|---|----------|
| 1 | Датасеты сохранены в `evals/datasets/graphrag/` |
| 2 | `graphrag-baseline.yaml` валиден; прогон завершается без ошибок |
| 3 | `graphrag-baseline.md` содержит метрики по трём сегментам |
| 4 | Baseline-метрики фиксируют ожидаемую просадку на multi-hop/global |

---

## Артефакты

- `evals/datasets/graphrag/multi-hop/v001_2026-06-26.yaml`
- `evals/datasets/graphrag/multi-hop/v002_2026-06-26.yaml` (усиленная версия)
- `evals/datasets/graphrag/global/v001_2026-06-26.yaml`
- `evals/configs/graphrag-baseline.yaml`
- `evals/reports/graphrag-baseline.md`

---

## Skills

- `langfuse` (синхронизация датасетов, прогон экспериментов)
