"""Item- and run-level evaluators for e2e-qa (metrics-map, E-19)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.agent.run_config import JudgeConfigBlock
from deepeval.metrics import FaithfulnessMetric, GEval, TaskCompletionMetric
from deepeval.test_case import LLMTestCase, SingleTurnParams
from langfuse import Evaluation

from scripts.agent_task import format_judge_input
from scripts.judge_client import create_judge_model


def _normalize_expected(expected_output: Any) -> dict[str, Any]:
    if expected_output is None:
        return {}
    if isinstance(expected_output, dict):
        return expected_output
    if hasattr(expected_output, "model_dump"):
        return expected_output.model_dump()
    return {}


def _output_message(output: Any) -> str | None:
    if output is None:
        return None
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        return output.get("message") or output.get("actual_output")
    return str(output)


def build_evaluation_steps(expected: dict[str, Any]) -> list[str]:
    """GEval steps from manifest expected_output — one list per item."""
    steps = [
        "Оценивай ТОЛЬКО ответ агента на последний запрос пользователя.",
        "Не требуй действий из предыдущих реплик, если последний запрос о другом.",
    ]
    for point in expected.get("answer_key_points") or []:
        steps.append(f"Ответ должен отражать: {point}")
    for rule in expected.get("must_not") or []:
        steps.append(f"Ответ НЕ должен: {rule}")
    return steps


def build_geval_criteria(expected: dict[str, Any]) -> str:
    """Short criteria string for GEval (paired with evaluation_steps)."""
    key_points = expected.get("answer_key_points") or []
    lines = [
        "Оцени, насколько ответ агента на ПОСЛЕДНИЙ запрос пользователя "
        "покрывает ключевые пункты эталона:",
    ]
    lines.extend(f"- {point}" for point in key_points)
    must_not = expected.get("must_not") or []
    if must_not:
        lines.append("Ответ НЕ должен:")
        lines.extend(f"- {rule}" for rule in must_not)
    return "\n".join(lines)


def build_task_description(expected: dict[str, Any]) -> str:
    """Explicit task for TaskCompletionMetric (avoids inferring wrong task)."""
    key_points = expected.get("answer_key_points") or []
    lines = [
        "Задача агента: ответить на последний запрос пользователя, удовлетворив критерии:",
    ]
    lines.extend(f"- {point}" for point in key_points)
    must_not = expected.get("must_not") or []
    if must_not:
        lines.append("Запрещено в ответе:")
        lines.extend(f"- {rule}" for rule in must_not)
    return "\n".join(lines)


def create_answer_correctness_metric(
    judge_model: Any,
    expected: dict[str, Any],
) -> GEval:
    """Fresh GEval per item — no shared mutable criteria."""
    return GEval(
        name="answer_correctness",
        criteria=build_geval_criteria(expected),
        evaluation_steps=build_evaluation_steps(expected),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=judge_model,
        async_mode=False,
    )


def create_task_completion_metric(
    judge_model: Any,
    expected: dict[str, Any],
) -> TaskCompletionMetric:
    """Fresh TaskCompletionMetric with explicit task from expected_output."""
    return TaskCompletionMetric(
        task=build_task_description(expected),
        model=judge_model,
        async_mode=False,
    )


@dataclass
class E2EEvaluatorBundle:
    """Callables for Langfuse dataset.run_experiment."""

    item_evaluators: list[Callable[..., Evaluation | list[Evaluation]]]
    run_evaluators: list[Callable[..., Evaluation]]


def get_e2e_evaluators(judge: JudgeConfigBlock) -> E2EEvaluatorBundle:
    """Build item/run evaluators with shared judge model."""
    _judge_model: Any = None
    _faithfulness_metric: FaithfulnessMetric | None = None

    def _get_judge_model() -> Any:
        nonlocal _judge_model
        if _judge_model is None:
            _judge_model = create_judge_model(judge)
        return _judge_model

    def _get_faithfulness_metric() -> FaithfulnessMetric:
        nonlocal _faithfulness_metric
        if _faithfulness_metric is None:
            _faithfulness_metric = FaithfulnessMetric(
                model=_get_judge_model(),
                async_mode=False,
            )
        return _faithfulness_metric

    def task_error(*, output: Any, **_: Any) -> Evaluation:
        failed = output is None
        return Evaluation(
            name="task_error",
            value=1.0 if failed else 0.0,
            data_type="BOOLEAN",
            comment="Task failed" if failed else "OK",
        )

    def segment_match(*, output: Any, expected_output: Any, **_: Any) -> Evaluation:
        expected = _normalize_expected(expected_output)
        expected_segment = expected.get("segment")
        if not expected_segment:
            return Evaluation(
                name="segment_match",
                value=1.0,
                comment="No expected segment",
            )
        actual_segment = None
        if isinstance(output, dict):
            actual_segment = output.get("segment")
        matched = actual_segment == expected_segment
        return Evaluation(
            name="segment_match",
            value=1.0 if matched else 0.0,
            data_type="BOOLEAN",
            comment=f"expected={expected_segment}, actual={actual_segment}",
        )

    def answer_correctness(
        *,
        input: Any,
        output: Any,
        expected_output: Any,
        **_: Any,
    ) -> Evaluation:
        message = _output_message(output)
        if not message:
            return Evaluation(
                name="answer_correctness",
                value=0.0,
                comment="No output",
            )
        expected = _normalize_expected(expected_output)
        try:
            metric = create_answer_correctness_metric(_get_judge_model(), expected)
            test_case = LLMTestCase(
                input=format_judge_input(input) if not isinstance(input, str) else input,
                actual_output=message,
            )
            metric.measure(test_case, _show_indicator=False)
            reason = getattr(metric, "reason", None) or "GEval score"
            return Evaluation(
                name="answer_correctness",
                value=float(metric.score or 0.0),
                comment=str(reason),
            )
        except Exception as exc:  # noqa: BLE001
            return Evaluation(
                name="answer_correctness",
                value=0.0,
                comment=f"Judge error: {exc}",
            )

    def faithfulness(*, input: Any, output: Any, **_: Any) -> Evaluation:
        message = _output_message(output)
        if not message:
            return Evaluation(name="faithfulness", value=0.0, comment="No output")
        contexts: list[str] = []
        if isinstance(output, dict):
            raw = output.get("retrieval_context") or []
            if isinstance(raw, list):
                contexts = [str(c) for c in raw if c]
        if not contexts:
            return Evaluation(
                name="faithfulness",
                value=0.0,
                comment="No retrieval context in trace (skipped)",
            )
        test_case = LLMTestCase(
            input=format_judge_input(input) if not isinstance(input, str) else input,
            actual_output=message,
            retrieval_context=contexts,
        )
        try:
            metric = _get_faithfulness_metric()
            metric.measure(test_case, _show_indicator=False)
            reason = getattr(metric, "reason", None) or "Faithfulness"
            return Evaluation(
                name="faithfulness",
                value=float(metric.score or 0.0),
                comment=str(reason),
            )
        except Exception as exc:  # noqa: BLE001
            return Evaluation(name="faithfulness", value=0.0, comment=f"Judge error: {exc}")

    def task_completion(
        *,
        input: Any,
        output: Any,
        expected_output: Any,
        **_: Any,
    ) -> Evaluation:
        message = _output_message(output)
        if not message:
            return Evaluation(name="task_completion", value=0.0, comment="No output")
        expected = _normalize_expected(expected_output)
        try:
            metric = create_task_completion_metric(_get_judge_model(), expected)
            test_case = LLMTestCase(
                input=format_judge_input(input) if not isinstance(input, str) else input,
                actual_output=message,
            )
            metric.measure(test_case, _show_indicator=False)
            reason = getattr(metric, "reason", None) or "TaskCompletion"
            return Evaluation(
                name="task_completion",
                value=float(metric.score or 0.0),
                comment=str(reason),
            )
        except Exception as exc:  # noqa: BLE001
            return Evaluation(name="task_completion", value=0.0, comment=f"Judge error: {exc}")

    def _avg_metric(*, item_results: Any, metric_name: str, **_: Any) -> Evaluation:
        values: list[float] = []
        for result in item_results:
            for evaluation in result.evaluations:
                if evaluation.name == metric_name and isinstance(evaluation.value, (int, float)):
                    values.append(float(evaluation.value))
        if not values:
            return Evaluation(name=f"avg_{metric_name}", value=0.0, comment="No scores")
        avg = sum(values) / len(values)
        return Evaluation(
            name=f"avg_{metric_name}",
            value=avg,
            comment=f"Average of {len(values)} items",
        )

    def error_rate(*, item_results: Any, **_: Any) -> Evaluation:
        total = len(item_results)
        failed = sum(
            1
            for result in item_results
            for evaluation in result.evaluations
            if evaluation.name == "task_error" and float(evaluation.value or 0) >= 1.0
        )
        rate = failed / max(total, 1)
        return Evaluation(
            name="error_rate",
            value=rate,
            comment=f"{failed}/{total} items failed",
        )

    def segment_match_rate(*, item_results: Any, **_: Any) -> Evaluation:
        values: list[float] = []
        for result in item_results:
            for evaluation in result.evaluations:
                if evaluation.name == "segment_match" and isinstance(
                    evaluation.value, (int, float)
                ):
                    values.append(float(evaluation.value))
        rate = sum(values) / max(len(values), 1) if values else 0.0
        return Evaluation(
            name="segment_match_rate",
            value=rate,
            comment=f"Matched {sum(values)}/{len(values)} items",
        )

    def avg_answer_correctness(*, item_results: Any, **kw: Any) -> Evaluation:
        return _avg_metric(item_results=item_results, metric_name="answer_correctness", **kw)

    def avg_faithfulness(*, item_results: Any, **kw: Any) -> Evaluation:
        return _avg_metric(item_results=item_results, metric_name="faithfulness", **kw)

    def avg_task_completion(*, item_results: Any, **kw: Any) -> Evaluation:
        return _avg_metric(item_results=item_results, metric_name="task_completion", **kw)

    return E2EEvaluatorBundle(
        item_evaluators=[
            task_error,
            segment_match,
            answer_correctness,
            faithfulness,
            task_completion,
        ],
        run_evaluators=[
            error_rate,
            avg_answer_correctness,
            avg_faithfulness,
            avg_task_completion,
            segment_match_rate,
        ],
    )
