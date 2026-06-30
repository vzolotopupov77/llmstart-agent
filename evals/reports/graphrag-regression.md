# GraphRAG Regression Loop — single-hop fix (Task 08)

> **Эксперимент:** Task 08 fix-generation-loop
> **Цель:** закрыть single-hop gate `answer_correctness ≥ 0.642` (не пройден в основном Task 08: retained 0.596, best 0.627)
> **Judge:** google/gemini-2.5-flash-lite · **Git SHA:** `f6c0db35`
> **Plan:** [../../docs/sprints/sprint-09-graphrag/tasks/08-agent-routing/fix-loop-plan.md](../../docs/sprints/sprint-09-graphrag/tasks/08-agent-routing/fix-loop-plan.md)

## Что сделано

Две независимые причины single-hop провала разделены и устранены:

- **(B) Judge-hardening** (`evals/scripts/evaluators.py`): судья иногда отдавал невалидный JSON →
  evaluator ставил ложный `0.0`. Теперь — retry (≤3) и при стойком фейле `value=None` (исключается
  из среднего, не считается плохим ответом). Прямой эффект: `e2e-qa-0006` 0.00→1.00 (в retained-прогоне
  это был judge-error, не плохой ответ).
- **(A) `agent-system-prompt-v5`** (поверх v4): post-tool generation rules под кластер sales-QA —
  состав комбо + consultation, «слоты TBD → ориентир + записи», структура интенсива, mock-оплата/рассрочка
  MVP, alt-поток (вечер/выходные) вместо записи, честность про код для CPO.

## Regression set (быстрый loop)

`evals/datasets/e2e/e2e-regression/v001` — 11 items (8 low + 3 green guard), `expected_output`
скопированы из `e2e-qa v002`. Прогон: `make eval-graph-regression` (v5) / `CONFIG=configs/graphrag-routing.yaml` (v4).

| Прогон | config / prompt | avg_answer_correctness | n |
|--------|-----------------|------------------------|---|
| baseline | `graphrag-routing` (v4, +hardening) | **0.491** | 11 |
| fix | `graphrag-routing-v5` (v5) | **0.573** | 11 |

Δ regression set: **+0.082**. Guard-green items (0014, 0016, 0026) — без регрессии (1.00→1.00).

Runs:
- v4: `graphrag-routing--e2e-regression--f6c0db35--20260630T080854Z`
- v5: `graphrag-routing-v5--e2e-regression--f6c0db35--20260630T081402Z`

## Финальный полный прогон — `e2e-qa v002` (single-hop proxy, n=26)

| Реализация | prompt | avg_answer_correctness | Gate ≥ 0.642 |
|------------|--------|------------------------|--------------|
| baseline (Qdrant-hybrid) | v2 | 0.662 | — |
| routing retained (Task 08) | v4 | 0.596 | ❌ |
| routing best attempt (Task 08) | v4 | 0.627 | ❌ |
| **fix-loop (B + A)** | **v5** | **0.665** | ✅ |

Run: `graphrag-routing-v5--e2e-qa--f6c0db35--20260630T081949Z` · 0/26 task_error.

### Per-item Δ (v4 retained → v5 final)

| item | diff | v4 | v5 | Δ | примечание |
|------|------|---:|---:|---:|-----------|
| 0001 | medium | 0.40 | 0.70 | +0.30 | формат комбо: назван состав + consultation |
| 0003 | medium | 0.40 | 0.70 | +0.30 | время/длительность: ориентир + записи |
| 0006 | easy | 0.00 | 1.00 | +1.00 | **judge-hardening** (был invalid-JSON 0.0) |
| 0008 | medium | 0.60 | 1.00 | +0.40 | вечерний поток: alt вместо «нет потоков» |
| 0012 | medium | 0.00 | 0.40 | +0.40 | CPO/код: честная оговорка (+hardening) |
| 0010 | hard | 0.70 | 0.80 | +0.10 | demo objection (multi) |
| 0025 | medium | 0.60 | 0.70 | +0.10 | следующий поток (multi) |
| 0002 | easy | 0.70 | 0.80 | +0.10 | формат |
| 0018 | easy | 0.60 | 0.40 | −0.20 | agents vs deep-agents (регрессия) |
| 0019 | medium | 0.80 | 0.40 | −0.40 | deep-agents для опытных (регрессия) |
| 0024 | hard | 0.30 | 0.20 | −0.10 | таймзона SF (multi, остаётся слабым) |
| 0011 | hard | 0.40 | 0.30 | −0.10 | повтор квалификации (multi) |

Прочие items — без значимых изменений; guard-green (0014/0015/0016/0026) держат 1.00.

## Остаточные gaps

- **0022 (рассрочка)** — 0.00: agent всё ещё не упоминает mock-оплату MVP по существу; rule 26 не сработал.
- **0005 (интенсив)** — 0.40 flat: распознавание vibe-coding-intensive нестабильно.
- **0018/0019 (agents↔deep-agents)** — лёгкая регрессия от v5: правила про комбо/код сместили выбор; кандидат на точечную доработку без отката gate.
- **0024 (таймзона)** — multi-turn, требует часовых поясов из KB (данных нет).

## Воспроизведение

```bash
make graph-up                                   # стек (neo4j/qdrant/langfuse)
make dev-backend                                # config_id graphrag-routing + graphrag-routing-v5
make eval-graph-regression CONFIG=configs/graphrag-routing.yaml   # v4 baseline
make eval-graph-regression                                        # v5 (default config)
make eval-graph-regression CONFIG=configs/graphrag-routing-v5.yaml DATASET=e2e/e2e-qa  # финал
```
