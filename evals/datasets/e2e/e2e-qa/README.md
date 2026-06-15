# Датасет: e2e-qa

**Группа (слой):** e2e (E-11)  
**Текущая версия:** v002 (`v002_2026-06-15.yaml`) · предыдущая: v001  
**Changelog v002:** [v002-changelog.md](./v002-changelog.md)  
**Формат:** YAML (E-12)

## Что проверяет

Сквозное качество ответа на типичный pre-purchase вопрос: RAG-факты, продукт, сегмент, тон — без изоляции одного слоя (dataset-map).

## Источник items

- **real_dialog:** CHAT_0014, 0020, 0070, 0110 (legacy `datasets/b2c/v2`, extraction)
- **synthetic:** `data/b2c/` (faq, catalog, courses-overview)
- Отбор: 26 items, ~62% extraction / ~38% synthetic; 6 multi-turn
- **reviewed_by:** `product-owner` (2026-06-14)

## Метрики

См. [metrics-map.md](../../../../docs/eval/metrics-map.md): главная `avg_answer_correctness`, guard faithfulness / task_completion / error_rate.

## Честность ground truth (E-14)

| gt_quality | Доля (v001) | Причина |
|------------|-------------|---------|
| approximate | ~81% (21/26) | extraction + paraphrased assistant context |
| verified | ~19% (5/26) | tools + kb_verified items |

## Правила пополнения

- Правка = новый файл `vNNN_YYYY-MM-DD.yaml` (E-11)
- Эталон утверждает человек **до** `reviewed_by` (E-13)

### v002 (2026-06-15)

Критерии уточнены для 7 items (error analysis eval-03): 0003, 0005, 0011, 0017, 0021, 0023, 0024. См. changelog.

## Зеркало в Langfuse (E-16)

**folders-as-versions:** `e2e/e2e-qa/v001`, `e2e/e2e-qa/v002`
