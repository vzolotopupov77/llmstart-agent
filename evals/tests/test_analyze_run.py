"""Tests for failure analysis helpers."""

from __future__ import annotations

from scripts.failure_analysis import (
    analyze_items,
    classify_failure_layer,
    distribution,
    top_worst,
)


def test_classify_retrieval_low_faithfulness() -> None:
    layer, _ = classify_failure_layer(
        answer_correctness=0.3,
        faithfulness=0.5,
        task_completion=0.4,
        segment_match=1.0,
        has_retrieval_context=True,
        tools=["search_knowledge_base"],
    )
    assert layer == "retrieval"


def test_classify_generation() -> None:
    layer, _ = classify_failure_layer(
        answer_correctness=0.4,
        faithfulness=0.8,
        task_completion=0.5,
        segment_match=1.0,
        has_retrieval_context=True,
        tools=[],
    )
    assert layer == "generation"


def test_analyze_and_top_worst() -> None:
    items = [
        {
            "input": "q1",
            "output": {"message": "a1", "tools": [], "retrieval_context": ["ctx"]},
            "scores": [
                {"name": "answer_correctness", "value": 0.9},
                {"name": "faithfulness", "value": 0.9},
                {"name": "task_completion", "value": 0.9},
                {"name": "segment_match", "value": 1.0},
            ],
        },
        {
            "input": "q2",
            "output": {"message": "a2", "tools": [], "retrieval_context": []},
            "scores": [
                {"name": "answer_correctness", "value": 0.1},
                {"name": "faithfulness", "value": 0.9},
                {"name": "task_completion", "value": 0.2},
                {"name": "segment_match", "value": 1.0},
            ],
        },
    ]
    analyzed = analyze_items(items)
    worst = top_worst(analyzed, 1)
    assert worst[0].answer_correctness == 0.1
    assert worst[0].failure_layer == "generation"


def test_distribution() -> None:
    stats = distribution([0.0, 0.5, 1.0])
    assert stats["count"] == 3
    assert stats["min"] == 0.0
    assert stats["max"] == 1.0
