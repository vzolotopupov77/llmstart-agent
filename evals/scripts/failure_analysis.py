"""Failure layer taxonomy for eval run analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FailureLayer = Literal["retrieval", "generation", "behavior", "unknown"]

THRESHOLDS = {
    "answer_correctness_green": 0.75,
    "answer_correctness_red": 0.60,
    "faithfulness_green": 0.85,
    "faithfulness_red": 0.70,
    "task_completion_green": 0.80,
    "task_completion_red": 0.65,
}


@dataclass
class ItemAnalysis:
    """Parsed item with scores for ranking."""

    index: int
    input_preview: str
    answer_correctness: float
    faithfulness: float
    task_completion: float
    segment_match: float
    task_error: float
    trace_id: str | None
    session_id: str | None
    tools: list[str]
    has_retrieval_context: bool
    judge_comment: str
    failure_layer: FailureLayer
    layer_reason: str


def _score(item: dict[str, Any], name: str, default: float = 0.0) -> float:
    for score in item.get("scores", []):
        if score.get("name") == name and score.get("value") is not None:
            return float(score["value"])
    return default


def _score_comment(item: dict[str, Any], name: str) -> str:
    for score in item.get("scores", []):
        if score.get("name") == name:
            return str(score.get("comment") or "")
    return ""


def _input_preview(item: dict[str, Any], max_len: int = 120) -> str:
    output = item.get("output") or {}
    if isinstance(output, dict) and output.get("input_text"):
        text = str(output["input_text"])
    else:
        raw = item.get("input")
        if isinstance(raw, str):
            text = raw
        elif isinstance(raw, list):
            parts = [f"{m.get('role')}: {m.get('content', '')[:40]}" for m in raw[:3]]
            text = " | ".join(parts)
        else:
            text = str(raw)
    text = " ".join(text.split())
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def classify_failure_layer(
    *,
    answer_correctness: float,
    faithfulness: float,
    task_completion: float,
    segment_match: float,
    has_retrieval_context: bool,
    tools: list[str],
) -> tuple[FailureLayer, str]:
    """Heuristic failure layer (retrieval / generation / behavior)."""
    if faithfulness < THRESHOLDS["faithfulness_red"] or (
        not has_retrieval_context and "search_knowledge_base" in tools
    ):
        return (
            "retrieval",
            f"faithfulness={faithfulness:.2f} или пустой retrieval при ожидании RAG",
        )
    if answer_correctness < THRESHOLDS["answer_correctness_red"] and (
        faithfulness >= THRESHOLDS["faithfulness_red"]
    ):
        return (
            "generation",
            f"answer_correctness={answer_correctness:.2f} при faithfulness={faithfulness:.2f}",
        )
    if segment_match < 1.0 or task_completion < THRESHOLDS["task_completion_red"]:
        return (
            "behavior",
            f"segment_match={segment_match:.0f}, task_completion={task_completion:.2f}",
        )
    if answer_correctness < THRESHOLDS["answer_correctness_green"]:
        ac_thr = THRESHOLDS["answer_correctness_green"]
        return (
            "generation",
            f"answer_correctness={answer_correctness:.2f} ниже порога {ac_thr}",
        )
    return ("unknown", "смешанный или judge variance")


def analyze_items(items: list[dict[str, Any]]) -> list[ItemAnalysis]:
    """Build per-item analysis list."""
    results: list[ItemAnalysis] = []
    for index, item in enumerate(items):
        output = item.get("output") or {}
        tools_raw = output.get("tools") or [] if isinstance(output, dict) else []
        tool_names = [t.get("name", "") for t in tools_raw if isinstance(t, dict) and t.get("name")]
        retrieval_ctx = []
        if isinstance(output, dict):
            retrieval_ctx = output.get("retrieval_context") or []
        ac = _score(item, "answer_correctness")
        ff = _score(item, "faithfulness")
        tc = _score(item, "task_completion")
        sm = _score(item, "segment_match", default=1.0)
        te = _score(item, "task_error")
        layer, reason = classify_failure_layer(
            answer_correctness=ac,
            faithfulness=ff,
            task_completion=tc,
            segment_match=sm,
            has_retrieval_context=bool(retrieval_ctx),
            tools=tool_names,
        )
        session_id = output.get("session_id") if isinstance(output, dict) else None
        results.append(
            ItemAnalysis(
                index=index,
                input_preview=_input_preview(item),
                answer_correctness=ac,
                faithfulness=ff,
                task_completion=tc,
                segment_match=sm,
                task_error=te,
                trace_id=item.get("trace_id"),
                session_id=str(session_id) if session_id else None,
                tools=tool_names,
                has_retrieval_context=bool(retrieval_ctx),
                judge_comment=_score_comment(item, "answer_correctness"),
                failure_layer=layer,
                layer_reason=reason,
            )
        )
    return results


def top_worst(items: list[ItemAnalysis], n: int = 5) -> list[ItemAnalysis]:
    """Lowest answer_correctness first."""
    return sorted(items, key=lambda x: (x.answer_correctness, x.task_completion))[:n]


def distribution(values: list[float]) -> dict[str, float | int]:
    """Simple distribution stats."""
    if not values:
        return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0}
    sorted_v = sorted(values)
    count = len(sorted_v)

    def percentile(p: float) -> float:
        idx = int(p * (count - 1))
        return sorted_v[idx]

    return {
        "count": count,
        "min": sorted_v[0],
        "max": sorted_v[-1],
        "avg": sum(sorted_v) / count,
        "p25": percentile(0.25),
        "p50": percentile(0.50),
        "p75": percentile(0.75),
    }


def layer_counts(items: list[ItemAnalysis]) -> dict[str, int]:
    counts: dict[str, int] = {"retrieval": 0, "generation": 0, "behavior": 0, "unknown": 0}
    for item in items:
        counts[item.failure_layer] = counts.get(item.failure_layer, 0) + 1
    return counts
