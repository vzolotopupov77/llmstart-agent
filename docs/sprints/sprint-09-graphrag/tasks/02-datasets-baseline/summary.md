# Summary: Task 02 — datasets-baseline

> **Sprint:** sprint-09-graphrag  
> **Статус:** ✅ Done  
> **Дата:** 2026-06-26  
> **Отчёт:** [`evals/reports/graphrag-baseline.md`](../../../../evals/reports/graphrag-baseline.md)

---

## Что сделано

### Датасеты

| Датасет | Файл | n | Версия |
|---------|------|---|--------|
| multi-hop | `evals/datasets/graphrag/multi-hop/v002_2026-06-26.yaml` | 12 | v002 (усиленная: MH-06 и MH-11 — 3+ узла) |
| global | `evals/datasets/graphrag/global/v001_2026-06-26.yaml` | 6 | v001 |

v001 multi-hop (12 вопросов) оказался завышен — два вопроса не требовали обхода 3+ узлов, что давало answer_correctness 0.500. В v002 они заменены на настоящие 3-hop вопросы.

### Baseline-прогон

**Config:** `graphrag-baseline.yaml` — Qdrant-hybrid top_k=5, gpt-4o-mini, judge: gemini-2.5-flash-lite.

**Результаты:**

| Сегмент | n | answer_correctness | required_entity_recall@5 | faithfulness |
|---------|--:|------------------:|-------------------------:|-------------:|
| single-hop | 26¹ | **0.662** | — | — |
| multi-hop | 12 | **0.383** | **0.618** | **0.749** |
| global | 6 | **0.200** | **0.292** | **0.767** |

¹ Прокси из exp-005 (тот же Qdrant-hybrid backend).

**Дельты:**
- multi-hop: −42% vs single-hop
- global: −70% vs single-hop

---

## Ключевые решения

| Решение | Обоснование |
|---------|-------------|
| v002 вместо v001 для multi-hop | v001 содержал 2 «псевдо-multi-hop» вопроса; v002 с настоящими 3-hop даёт честный baseline |
| Прокси single-hop из exp-005 | Прогон нового сегмента был избыточен — экономия ресурсов |
| Judge: gemini-2.5-flash-lite | Дешевле gpt-4o при достаточной точности для scoring |

---

## Паттерны провалов flat RAG

| Паттерн | Вопросы | Причина |
|---------|---------|---------|
| Агрегация числовых полей по N нодам | GL-02, MH-01 | top-5 чанков из одного файла |
| Entity gap (данные не в chunks) | GL-01 (авторы) | Нет ноды Instructor в индексе |
| Intersection тем двух курсов | MH-03, MH-08 | Требует двух retrieval + JOIN |
| Path traversal (RECOMMENDED_BEFORE) | MH-01, MH-10, MH-12 | Граф не представлен в чанках |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | Датасеты в `evals/datasets/graphrag/` | ✅ (multi-hop v002, global v001) |
| 2 | Config валиден, прогон без ошибок | ✅ |
| 3 | Метрики по трём сегментам | ✅ |
| 4 | Просадка на multi-hop/global зафиксирована | ✅ (−42% / −70%) |
