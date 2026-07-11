# Датасет: multimodal-rag

**Группа (слой):** rag · sprint-10 multimodal eval  
**Текущая версия:** v002 (`v002_2026-07-05.json`) · предыдущая: v001  
**Changelog v002:** [v002-changelog.md](./v002-changelog.md)  
**Формат:** JSON

## Что проверяет

Retrieval (и опционально generation) по **5 сегментам** визуально-плотного корпуса (66 PNG):

| Сегмент | Способность |
|---------|-------------|
| S1_text | plain text на слайде |
| S2_chart | числа с графиков / stat-боксов |
| S3_layout | схемы, layout, позиция элементов |
| S4_multi | агрегация по одному или нескольким слайдам |
| S5_unanswerable | корректный отказ (generation); trap retrieval — диагностика |

Метрики: [metric_map.md](../../../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)

## Поля записи

| Поле | S1–S4 | S5 |
|------|-------|-----|
| `required_slides` | gold-слайды для Recall / set-Recall | **не используется** |
| `trap_slides` | — | ловушечные слайды (retrieval-диагностика) |
| `expected_behavior` | — | `refusal` |
| `must_not_invent` | — | запрещённые галлюцинации |
| `metadata.multi_type` | S4: `cross_slide` \| `single_slide_dense` | — |
| `metadata.persona` | опц., перефраз стиля | опц. |

**Эталоны:** только видимое содержимое PNG; speaker notes не участвуют.

## Источник items

- **synthetic** из `docs/sprints/sprint-10-multimodal-rag/analysis.md`
- Task 01: таксономия + черновик; user-review исключений
- Task 02: PNG-verified v001
- v002: правки по dataset-reviewer

## Правила пополнения

- Правка = новый файл `vNNN_YYYY-MM-DD.json` (иммутабельность)
- `reviewed_by` — после human validation sample (**2026-07-05:** S5, S2-9, S1-6/7, S4-2)
- v001 не редактировать

## Baseline

```bash
make eval-multimodal-baseline
```

Config: `evals/configs/multimodal-baseline.yaml` → dataset v002, collection `multimodal_text_naive_v002`.
