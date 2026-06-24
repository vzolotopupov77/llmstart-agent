# Summary: 05-baseline-eval-qdrant

> **План:** [plan.md](./plan.md)  
> **Дата закрытия:** 2026-06-24

---

## Что реализовано

- `backend/app/agent/run_config.py` — `RetrievalConfigBlock`: `db_version`, `embedding_model`, `chunk_size`, `top_k`
- `evals/configs/vector-db-baseline.yaml` — Qdrant v1.18.2, embeddings, v002
- `evals/reports/runs/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.json` — canonical run
- `evals/reports/vector-db-baseline.md` — baseline-отчёт (метрики, стратификация, chroma, конфаундеры, решение)
- `evals/reports/vector-db-baseline--e2e-qa--884a6423--20260624T070642Z.md` — analyze canonical run
- `.env.example` — `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=120`, retry 3
- `evals/tests/test_run_config.py` — тест загрузки `vector-db-baseline.yaml`

---

## Отклонения от плана

- Canonical run — `…20260624T070642Z`, не первый прогон `…143257Z` (8 judge errors в peak hours).
- Два invalid run (`…053801Z`, `…062728Z`) — backend не отвечал; не в baseline.
- E2e-baseline вместо vector bench metrics (latency, precision@k) — bench перенесён в Task 06.

---

## Принятые решения

| Решение | Причина |
|---------|---------|
| Canonical run `…070642Z` | error_rate=0, 26/26 Langfuse, стабильный judge vs 8 artifacts в первом прогоне |
| Judge timeouts 120s / 3 retries | Снижение APIConnectionError на OpenRouter |
| Adjusted correctness ≈ 0.64 | 2 judge artifacts на correctness; для сравнения с chroma 0.662 |

---

## Проблемы и решения

| Проблема | Как решили |
|----------|-----------|
| 8/26 judge errors (1st run, peak hours) | Re-run утром + увеличение DEEPEVAL timeouts |
| 2 invalid runs (backend down) | Проверка `/health` перед experiment |
| 2 judge artifacts в canonical (0025, 0001) | Зафиксированы в отчёте; adjusted ≈ 0.64 |

---

## Итог DoD

| # | Критерий | Результат |
|---|----------|-----------|
| 1 | `evals/configs/vector-db-baseline.yaml` | ✅ |
| 2 | JSON-отчёт canonical run | ✅ |
| 3 | `vector-db-baseline.md` (метрики, стратификация, сравнение, решение) | ✅ |
| 4 | Ссылка в sprint README «Итог» | ✅ |
| 5 | `make test-backend` | ✅ |

---

## Canonical baseline (Qdrant, v002)

| Метрика | Value |
|---|---|
| avg_answer_correctness | 0.588 (adjusted ≈ 0.64) |
| avg_faithfulness | 0.873 |
| avg_task_completion | 0.585 |
| error_rate | 0.000 |
| segment_match_rate | 0.846 |

vs Chroma 0.662: −0.074 raw, ≈ −0.02 adjusted.

---

## Что дальше

- Task 06: `PgvectorRetriever` + `vector_bench.py` + `make bench`
- Eval-fix: generation / retrieval items из analyze (отдельный спринт)

---

## Ссылки

- [vector-db-baseline.md](../../../evals/reports/vector-db-baseline.md)
- [exp-005 chroma baseline](../../../evals/reports/exp-005-candidate-rag-first-prompt-v002.md)
- [Langfuse canonical run](http://localhost:3001/project/cmq0y543r0006ujmnyb937ki7/datasets/cmqfb07co0001nm07e59lzf0n/runs/66c1317b-78ad-4d52-9b92-a8762871eb86)
