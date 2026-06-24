# Task 05: baseline-eval-qdrant

> **Sprint:** sprint-08-vector-db  
> **Статус:** ✅ Done

## Цель

Прогнать eval-датасет `e2e/e2e-qa/v002` через QdrantRetriever, зафиксировать e2e-baseline метрики как точку отсчёта для vector-db спринта.

## Состав работ

- [x] Расширить `RetrievalConfigBlock` (db_version, embedding_model, chunk_size, top_k)
- [x] Создать `evals/configs/vector-db-baseline.yaml`
- [x] `make up` + `make index` (Qdrant)
- [x] `make -C evals experiment CONFIG=configs/vector-db-baseline.yaml DATASET=e2e/e2e-qa`
- [x] `make -C evals analyze RUN=vector-db-baseline--e2e-qa--884a6423--20260623T143257Z`
- [x] `evals/reports/vector-db-baseline.md` — метрики, стратификация, сравнение, решение
- [x] Обновить sprint README

## DoD

- [x] `evals/configs/vector-db-baseline.yaml` существует
- [x] JSON-отчёт в `evals/reports/runs/`
- [x] `evals/reports/vector-db-baseline.md` с метриками, сравнением и разделом «Решение»
- [x] Sprint README обновлён

## Артефакты

- `evals/configs/vector-db-baseline.yaml`
- `evals/reports/runs/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.json` (canonical)
- `evals/reports/vector-db-baseline.md`
- `evals/reports/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.md` (analyze)
