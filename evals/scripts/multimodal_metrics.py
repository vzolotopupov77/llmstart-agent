"""Retrieval metrics for multimodal slide RAG eval."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scripts.multimodal_models import (
    MultimodalDatasetItem,
    Segment,
    item_gold_slides,
    item_trap_slides,
)


@dataclass(frozen=True)
class RetrievalScores:
    recall_at_k: float
    ndcg_at_5: float
    mrr: float
    set_recall_at_k: float | None = None
    trap_slide_in_topk: float | None = None


def _binary_relevance(slide_id: int, required: set[int]) -> int:
    return 1 if slide_id in required else 0


def recall_at_k(ranked_slides: list[int], required: set[int], k: int) -> float:
    top = ranked_slides[:k]
    return 1.0 if any(slide in required for slide in top) else 0.0


def mrr(ranked_slides: list[int], required: set[int]) -> float:
    for rank, slide in enumerate(ranked_slides, start=1):
        if slide in required:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_slides: list[int], required: set[int], k: int) -> float:
    top = ranked_slides[:k]
    dcg = sum(
        _binary_relevance(slide, required) / math.log2(index + 2) for index, slide in enumerate(top)
    )
    ideal_hits = min(len(required), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def set_recall_at_k(ranked_slides: list[int], required: set[int], k: int) -> float:
    top = set(ranked_slides[:k])
    if not required:
        return 0.0
    return len(required & top) / len(required)


def trap_slide_in_topk(ranked_slides: list[int], trap_slides: set[int], k: int) -> float:
    """Diagnostic for S5: misleading slide retrieved (not a success metric)."""
    top = ranked_slides[:k]
    return 1.0 if any(slide in trap_slides for slide in top) else 0.0


def score_item(
    item: MultimodalDatasetItem,
    ranked_slides: list[int],
    *,
    k: int,
) -> RetrievalScores:
    required = item_gold_slides(item)
    segment: Segment = item.segment

    if segment == "S5_unanswerable":
        traps = item_trap_slides(item)
        return RetrievalScores(
            recall_at_k=0.0,
            ndcg_at_5=0.0,
            mrr=0.0,
            trap_slide_in_topk=trap_slide_in_topk(ranked_slides, traps, k),
        )

    if segment == "S4_multi":
        sr = set_recall_at_k(ranked_slides, required, k)
        return RetrievalScores(
            recall_at_k=recall_at_k(ranked_slides, required, k),
            ndcg_at_5=ndcg_at_k(ranked_slides, required, k),
            mrr=mrr(ranked_slides, required),
            set_recall_at_k=sr,
        )

    return RetrievalScores(
        recall_at_k=recall_at_k(ranked_slides, required, k),
        ndcg_at_5=ndcg_at_k(ranked_slides, required, k),
        mrr=mrr(ranked_slides, required),
    )


def aggregate_by_segment(
    rows: list[tuple[Segment, RetrievalScores]],
) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[RetrievalScores]] = {}
    for segment, scores in rows:
        buckets.setdefault(segment, []).append(scores)

    result: dict[str, dict[str, float]] = {}
    for segment, scores_list in sorted(buckets.items()):
        n = len(scores_list)
        entry: dict[str, float] = {
            "n": float(n),
            "recall_at_k": sum(s.recall_at_k for s in scores_list) / n,
            "mrr": sum(s.mrr for s in scores_list) / n,
            "ndcg_at_5": sum(s.ndcg_at_5 for s in scores_list) / n,
        }
        set_vals = [s.set_recall_at_k for s in scores_list if s.set_recall_at_k is not None]
        if set_vals:
            entry["set_recall_at_k"] = sum(set_vals) / len(set_vals)
        trap_vals = [s.trap_slide_in_topk for s in scores_list if s.trap_slide_in_topk is not None]
        if trap_vals:
            entry["trap_slide_in_topk"] = sum(trap_vals) / len(trap_vals)
        result[segment] = entry
    return result
