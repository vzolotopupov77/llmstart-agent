"""Tests for compare_runs."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.compare_runs import (
    analyze_item_patterns,
    build_compare_markdown,
    build_factor_analysis_section,
    compare_runs,
    compute_item_deltas,
    detect_change_factors,
    load_run_report,
    validate_comparable,
)

RUN_A = "baseline-react-chroma--e2e-qa--476018c9--20260614T182238Z"
RUN_B = "baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z"


def test_validate_comparable_same_dataset() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    warnings = validate_comparable(run_a, run_b)
    assert isinstance(warnings, list)


def test_validate_comparable_rejects_dataset_mismatch() -> None:
    run_a = load_run_report(RUN_A)
    run_b = {**load_run_report(RUN_B), "langfuse_dataset": "e2e/e2e-qa/v002"}
    with pytest.raises(ValueError, match="Несовпадение датасета"):
        validate_comparable(run_a, run_b)


def test_compute_item_deltas_real_runs() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    deltas = compute_item_deltas(run_a, run_b)
    assert len(deltas) == 26
    avg = sum(d.delta for d in deltas) / len(deltas)
    assert avg > 0.3


def test_build_compare_markdown_sections() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    md = build_compare_markdown(RUN_A, RUN_B, run_a, run_b, warnings=["test warning"])
    assert "## Run-level metrics" in md
    assert "avg_answer_correctness" in md
    assert "## Item-level: answer_correctness" in md
    assert "test warning" in md


def test_compare_runs_writes_file(tmp_path: Path) -> None:
    out = compare_runs(RUN_A, RUN_B, tmp_path)
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Compare:" in text


def test_load_run_report_missing() -> None:
    with pytest.raises(FileNotFoundError):
        load_run_report("nonexistent-run-name")


def test_fixture_minimal_compare() -> None:
    run_a = {
        "langfuse_dataset": "e2e/e2e-qa/v001",
        "run_metadata": {"dataset_version": "v001"},
        "config_id": "cfg-a",
        "judge": {"name": "judge-a"},
        "git_sha": "abc",
        "items": [{"input": "q1", "scores": [{"name": "answer_correctness", "value": 0.2}]}],
        "run_scores": [{"name": "avg_answer_correctness", "value": 0.2}],
    }
    run_b = {
        "langfuse_dataset": "e2e/e2e-qa/v001",
        "run_metadata": {"dataset_version": "v001"},
        "config_id": "cfg-b",
        "judge": {"name": "judge-a"},
        "git_sha": "abc",
        "items": [{"input": "q1", "scores": [{"name": "answer_correctness", "value": 0.8}]}],
        "run_scores": [{"name": "avg_answer_correctness", "value": 0.8}],
    }
    md = build_compare_markdown("run-a", "run-b", run_a, run_b)
    assert "0.800" in md or "0.8" in md
    deltas = compute_item_deltas(run_a, run_b)
    assert deltas[0].delta == pytest.approx(0.6)


def test_build_factor_analysis_section() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    section = build_factor_analysis_section(run_a, run_b, warnings=["warn"])
    text = "\n".join(section)
    assert "## Факторный анализ" in text
    assert "### Рекомендации" in text
    assert "avg_answer_correctness" in text
    assert "предупреждения" in text


def test_detect_change_factors_same_agent() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    factors = detect_change_factors(run_a, run_b)
    config = next(f for f in factors if f.name == "config_id")
    assert config.changed is False


def test_analyze_item_patterns_real_runs() -> None:
    run_a = load_run_report(RUN_A)
    run_b = load_run_report(RUN_B)
    patterns = analyze_item_patterns(run_a, run_b)
    assert patterns.total == 26
    assert patterns.zero_to_pass >= 1
