"""Tests for evaluators and run utilities."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from app.agent.run_config import JudgeConfigBlock
from langfuse import Evaluation

from scripts.agent_task import (
    build_chat_headers,
    extract_user_messages,
    format_input_for_eval,
    format_judge_input,
)
from scripts.evaluators import (
    build_evaluation_steps,
    build_geval_criteria,
    build_task_description,
    get_e2e_evaluators,
)
from scripts.judge_client import SyncOpenRouterJudge, create_judge_model
from scripts.run_utils import build_run_name, resolve_dataset_slug

JUDGE = SimpleNamespace(
    name="google/gemini-2.5-flash-lite",
    provider="openrouter",
    temperature=0.0,
)


def test_extract_user_messages_single() -> None:
    assert extract_user_messages("  hello  ") == ["hello"]


def test_build_chat_headers_includes_eval_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVAL_ACCESS_KEY", raising=False)
    assert build_chat_headers() == {"Accept": "application/json"}
    monkeypatch.setenv("EVAL_ACCESS_KEY", "  eval-secret  ")
    assert build_chat_headers() == {
        "Accept": "application/json",
        "X-LLMStart-Eval-Key": "eval-secret",
    }


def test_extract_user_messages_multi() -> None:
    item_input = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ignored"},
        {"role": "user", "content": "second"},
    ]
    assert extract_user_messages(item_input) == ["first", "second"]


def test_format_input_for_eval() -> None:
    text = format_input_for_eval([{"role": "user", "content": "q"}])
    assert "user: q" in text


def test_task_error_evaluator() -> None:
    bundle = get_e2e_evaluators(JUDGE)
    task_error = bundle.item_evaluators[0]
    failed = task_error(output=None)
    assert failed.name == "task_error"
    assert failed.value == 1.0
    ok = task_error(output={"message": "hi"})
    assert ok.value == 0.0


def test_segment_match_evaluator() -> None:
    bundle = get_e2e_evaluators(JUDGE)
    segment_match = bundle.item_evaluators[1]
    result = segment_match(
        output={"segment": "b2c"},
        expected_output={"segment": "b2c"},
    )
    assert result.value == 1.0


def test_error_rate_run_evaluator() -> None:
    bundle = get_e2e_evaluators(JUDGE)
    error_rate = bundle.run_evaluators[0]
    item_results = [
        SimpleNamespace(
            evaluations=[Evaluation(name="task_error", value=1.0)],
        ),
        SimpleNamespace(
            evaluations=[Evaluation(name="task_error", value=0.0)],
        ),
    ]
    result = error_rate(item_results=item_results)
    assert result.name == "error_rate"
    assert result.value == 0.5


def test_build_run_name_format() -> None:
    name = build_run_name(config_id="baseline-react-chroma", dataset_slug="e2e-qa")
    assert name.startswith("baseline-react-chroma--e2e-qa--")
    parts = name.split("--")
    assert len(parts) == 4


def test_resolve_dataset_slug() -> None:
    slug, version, lf_name = resolve_dataset_slug("e2e/e2e-qa")
    assert slug == "e2e-qa"
    assert version == "v001"
    assert lf_name == "e2e/e2e-qa/v001"


def test_format_judge_input_last_user_turn() -> None:
    item_input = [
        {"role": "user", "content": "Есть курс в записях?"},
        {"role": "assistant", "content": "Да, agents подходит."},
        {"role": "user", "content": "Следующий поток когда?"},
    ]
    text = format_judge_input(item_input)
    assert "Последний запрос пользователя" in text
    assert "Следующий поток когда?" in text
    assert "Есть курс в записях?" in text
    assert text.index("Следующий поток") > text.index("Есть курс")


def test_build_evaluation_steps_distinct_per_item() -> None:
    installment = build_evaluation_steps(
        {"answer_key_points": ["не обещать рассрочку сейчас"], "must_not": ["обещать рассрочку"]}
    )
    payment = build_evaluation_steps({"answer_key_points": ["создать ссылку на оплату agents"]})
    assert any("рассрочк" in step for step in installment)
    assert any("оплат" in step for step in payment)
    assert installment != payment


def test_build_task_description_from_key_points() -> None:
    task = build_task_description({"answer_key_points": ["признать временной барьер"]})
    assert "временной барьер" in task
    assert "последний запрос" in task


def test_create_answer_correctness_metric_uses_evaluation_steps() -> None:
    expected = {"answer_key_points": ["ответ про рассрочку"], "must_not": ["обещать рассрочку"]}
    steps = build_evaluation_steps(expected)
    criteria = build_geval_criteria(expected)
    joined = " ".join(steps)
    assert "рассрочк" in joined
    assert "рассрочк" in criteria
    assert "ПОСЛЕДНИЙ" in criteria or "последн" in criteria.lower()


def test_create_judge_model_returns_sync_judge() -> None:
    judge = JudgeConfigBlock(
        provider="openrouter",
        name="google/gemini-2.5-flash-lite",
        temperature=0.0,
    )
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        model = create_judge_model(judge)
    assert isinstance(model, SyncOpenRouterJudge)


@patch("deepeval.models.llms.gateway_model.AsyncOpenAI")
@patch("deepeval.models.llms.gateway_model.OpenAI")
def test_sync_judge_uses_sync_client(
    mock_openai: MagicMock,
    mock_async_openai: MagicMock,
) -> None:
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_completion.usage.prompt_tokens = 1
    mock_completion.usage.completion_tokens = 1
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai.return_value = mock_client

    judge = JudgeConfigBlock(
        provider="openrouter",
        name="google/gemini-2.5-flash-lite",
        temperature=0.0,
    )
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        model = create_judge_model(judge)
    output, _ = model.generate("hello")

    assert output == "ok"
    mock_openai.assert_called()
    mock_async_openai.assert_not_called()


def test_create_task_completion_metric_sets_explicit_task() -> None:
    expected = {"answer_key_points": ["следующий поток или запись"]}
    task = build_task_description(expected)
    assert "следующий поток" in task
    assert "последний запрос" in task


@patch("scripts.evaluators.create_answer_correctness_metric")
def test_answer_correctness_creates_fresh_geval_per_call(
    mock_create_metric: MagicMock,
) -> None:
    mock_metric = MagicMock()
    mock_metric.score = 0.8
    mock_metric.reason = "covers key points"
    mock_create_metric.side_effect = [mock_metric, MagicMock(score=0.2, reason="miss")]

    bundle = get_e2e_evaluators(JUDGE)
    answer_correctness = bundle.item_evaluators[2]

    answer_correctness(
        input="Есть ли рассрочка?",
        output={"message": "Рассрочки пока нет."},
        expected_output={"answer_key_points": ["не обещать рассрочку"]},
    )
    answer_correctness(
        input="Дайте ссылку на оплату.",
        output={"message": "Вот ссылка."},
        expected_output={"answer_key_points": ["ссылка на оплату"]},
    )

    assert mock_create_metric.call_count == 2
    first_expected = mock_create_metric.call_args_list[0][0][1]
    second_expected = mock_create_metric.call_args_list[1][0][1]
    assert first_expected["answer_key_points"] != second_expected["answer_key_points"]


@patch("scripts.evaluators.create_answer_correctness_metric")
def test_answer_correctness_retries_then_succeeds(
    mock_create_metric: MagicMock,
) -> None:
    """Transient judge failure (invalid JSON) is retried, not scored 0.0."""
    mock_metric = MagicMock()
    mock_metric.measure.side_effect = [ValueError("invalid JSON"), None]
    mock_metric.score = 0.9
    mock_metric.reason = "covers key points"
    mock_create_metric.return_value = mock_metric

    bundle = get_e2e_evaluators(JUDGE)
    answer_correctness = bundle.item_evaluators[2]
    result = answer_correctness(
        input="Есть ли рассрочка?",
        output={"message": "Рассрочки пока нет."},
        expected_output={"answer_key_points": ["не обещать рассрочку"]},
    )

    assert result.value == 0.9
    assert mock_metric.measure.call_count == 2


@patch("scripts.evaluators.create_answer_correctness_metric")
def test_answer_correctness_skips_on_persistent_judge_failure(
    mock_create_metric: MagicMock,
) -> None:
    """Persistent judge failure -> value=None (skip), never a false 0.0."""
    mock_metric = MagicMock()
    mock_metric.measure.side_effect = ValueError("invalid JSON")
    mock_create_metric.return_value = mock_metric

    bundle = get_e2e_evaluators(JUDGE)
    answer_correctness = bundle.item_evaluators[2]
    result = answer_correctness(
        input="Чем комбо отличается?",
        output={"message": "Комбо дешевле."},
        expected_output={"answer_key_points": ["все четыре программы"]},
    )

    assert result.value is None
    assert "judge_skipped" in (result.comment or "")
    assert mock_metric.measure.call_count == 3


def test_avg_answer_correctness_excludes_skipped() -> None:
    """Run-level average must ignore judge_skipped (value=None) items."""
    bundle = get_e2e_evaluators(JUDGE)
    avg_ac = next(e for e in bundle.run_evaluators if e.__name__ == "avg_answer_correctness")
    item_results = [
        SimpleNamespace(evaluations=[Evaluation(name="answer_correctness", value=1.0)]),
        SimpleNamespace(evaluations=[Evaluation(name="answer_correctness", value=0.0)]),
        SimpleNamespace(evaluations=[Evaluation(name="answer_correctness", value=None)]),
    ]
    result = avg_ac(item_results=item_results)
    assert result.value == 0.5
    assert "2 items" in (result.comment or "")


@patch("scripts.evaluators.create_task_completion_metric")
def test_task_completion_passes_expected_output(
    mock_create_metric: MagicMock,
) -> None:
    mock_metric = MagicMock()
    mock_metric.score = 1.0
    mock_metric.reason = "task done"
    mock_create_metric.return_value = mock_metric

    bundle = get_e2e_evaluators(JUDGE)
    task_completion = bundle.item_evaluators[4]
    expected = {"answer_key_points": ["признать временной барьер"]}

    result = task_completion(
        input=[
            {"role": "user", "content": "Есть курс?"},
            {"role": "user", "content": "Следующий поток когда?"},
        ],
        output={"message": "Набор в сентябре уточняется."},
        expected_output=expected,
    )

    assert result.value == 1.0
    mock_create_metric.assert_called_once()
    passed_expected = mock_create_metric.call_args[0][1]
    assert passed_expected == expected
