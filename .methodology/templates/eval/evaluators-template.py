# Шаблон: evals/scripts/evaluators.py — item- и run-level evaluators (E-19)
# Иллюстративный каркас на Langfuse SDK (Experiments). Версию SDK пинить (E-25).

from langfuse import Evaluation


# ---------- item-level: вызывается на каждый item рана ----------

def task_error(*, input, output, expected_output, metadata, **kw) -> Evaluation:
    """Упавший item — это метрика, а не исключение в логе (E-19)."""
    return Evaluation(name="task_error", value=1.0 if output is None else 0.0)


def answer_correctness(*, input, output, expected_output, metadata, **kw) -> Evaluation:
    """Главная метрика проекта (E-18). Реализация — через ragas (framework-first, E-17)."""
    if output is None:
        return Evaluation(name="answer_correctness", value=0.0, comment="No output")
    score, reason = ragas_answer_correctness(input, output, expected_output)  # обёртка над ragas
    return Evaluation(name="answer_correctness", value=score, comment=reason)


def faithfulness(*, input, output, expected_output, metadata, **kw) -> Evaluation:
    """Guard-метрика: ответ обоснован retrieved-контекстом (reference-free)."""
    if output is None:
        return Evaluation(name="faithfulness", value=0.0, comment="No output")
    score, reason = ragas_faithfulness(input, output)  # контекст — из трейса/output
    return Evaluation(name="faithfulness", value=score, comment=reason)


# ---------- run-level: вызывается один раз на весь ран ----------

def error_rate(*, item_results, **kw) -> Evaluation:
    """Guard-метрика рана: доля упавших items (E-19)."""
    failed = sum(1 for r in item_results if r.output is None)
    return Evaluation(name="error_rate", value=failed / max(len(item_results), 1))


# ---------- подключение (run_experiment) ----------
# result = dataset.run_experiment(
#     name=run_name,                       # {config_id}--{dataset}--{sha8}--{ts} (E-9)
#     task=task_fn,                        # бьёт в Agent Core с config_id (E-3/E-6)
#     evaluators=[task_error, answer_correctness, faithfulness],   # item-level
#     run_evaluators=[error_rate],                                  # run-level
#     run_metadata=run_metadata,           # конфиг целиком; run-level ключи ТОЛЬКО здесь (E-25)
# )
