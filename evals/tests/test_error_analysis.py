"""Tests for build_error_analysis merge helper."""

from __future__ import annotations

from pathlib import Path

from scripts.build_error_analysis import (
    FAIL_THRESHOLD,
    merge_runs,
)

RUNS_DIR = Path(__file__).resolve().parents[1] / "reports" / "runs"
BASELINE = "baseline-react-chroma--e2e-qa--476018c9--20260615T083100Z"
CANDIDATE = "candidate-rag-first-prompt--e2e-qa--476018c9--20260615T094647Z"


def test_merge_runs_item_count_and_deltas() -> None:
    merged = merge_runs(
        RUNS_DIR / f"{BASELINE}.json",
        RUNS_DIR / f"{CANDIDATE}.json",
    )
    assert len(merged) == 26
    assert all(it.item_id.startswith("e2e-qa-") for it in merged)
    by_id = {it.item_id: it for it in merged}
    assert by_id["e2e-qa-0005"].delta <= -0.05
    failing = [it for it in merged if it.ac_candidate < FAIL_THRESHOLD]
    assert len(failing) >= 10


def test_merge_loads_manifest_intent() -> None:
    merged = merge_runs(
        RUNS_DIR / f"{BASELINE}.json",
        RUNS_DIR / f"{CANDIDATE}.json",
    )
    by_id = {it.item_id: it for it in merged}
    assert by_id["e2e-qa-0024"].intent == "G1.4"
    assert by_id["e2e-qa-0003"].intent == "G1.3"
    assert len(by_id["e2e-qa-0003"].key_points) >= 3
