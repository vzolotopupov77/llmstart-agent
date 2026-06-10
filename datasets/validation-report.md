# Validation Report

**Версия:** v1  
**Дата:** auto-run  
**Статус:** PASS

## Структурная проверка

- B2C записей: **70**
- B2B записей: **15**
- Уникальные id: **да**
- Ошибки: **0**
- Предупреждения: **6**

### Предупреждения
- [G4] b2c-syn-rag-009: G4 record without must_not guardrails
- [G4] b2c-syn-objection-m04: G4 record without must_not guardrails
- [routing] b2c-syn-segment-001: b2c-segment with expected segment=b2b (OK for routing eval)
- [routing] b2c-syn-segment-003: b2c-segment with expected segment=b2b (OK for routing eval)
- [routing] b2c-syn-segment-m01: b2c-segment with expected segment=b2b (OK for routing eval)
- [routing] b2c-syn-segment-005: b2c-segment with expected segment=b2b (OK for routing eval)

## Покрытие B2C

### По типам

- b2c-objection: 18
- b2c-product: 13
- b2c-rag: 20
- b2c-segment: 8
- b2c-tools: 11

### По группам

- G1: 9
- G2: 13
- G3: 6
- G4: 8
- G5: 8
- G6: 4
- G7: 8
- G8: 5
- G9: 9

### turn_mode: single=54, multi=16

## Покрытие B2B

- b2b-nurture: 4
- b2b-rag: 7
- b2b-segment: 4

## Семантические заметки (выборочно)

- G4: все записи проверены на явный отказ «публичного демо нет»
- G9 рассрочка (b2c-syn-rag-003): must_not на обещание рассрочки
- B2B: нет create_payment_link — корректно для корп. сделок
- Chunk ids / Hit Rate@k: не применялось
- v2: G9.4 = payment tool-flow; reconstruction source для B2B segment

## Validation Sample

Выборка для ревью человеком: [`validation-sample.md`](validation-sample.md) (7 B2C + 2 B2B)
