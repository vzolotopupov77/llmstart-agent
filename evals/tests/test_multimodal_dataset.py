"""Tests for multimodal RAG dataset and retrieval metrics."""

from __future__ import annotations

from scripts.multimodal_metrics import (
    aggregate_by_segment,
    ndcg_at_k,
    recall_at_k,
    score_item,
    set_recall_at_k,
)
from scripts.multimodal_models import ItemMetadata, MultimodalDatasetItem, load_multimodal_dataset


def test_load_multimodal_dataset_v002() -> None:
    manifest = load_multimodal_dataset(
        "datasets/multimodal/multimodal-rag/v002_2026-07-05.json",
    )
    assert manifest.version == "v002"
    assert len(manifest.items) == 38
    segments = {item.segment for item in manifest.items}
    assert segments == {
        "S1_text",
        "S2_chart",
        "S3_layout",
        "S4_multi",
        "S5_unanswerable",
    }
    s2 = [item for item in manifest.items if item.segment == "S2_chart"]
    assert len(s2) == 9
    s5 = [item for item in manifest.items if item.segment == "S5_unanswerable"]
    assert len(s5) == 6
    assert all(item.expected_behavior == "refusal" for item in s5)
    assert all(item.trap_slides for item in s5)
    assert all(not item.required_slides for item in s5)


def test_load_multimodal_dataset_v001_legacy_s5() -> None:
    manifest = load_multimodal_dataset(
        "datasets/multimodal/multimodal-rag/v001_2026-07-05.json",
    )
    assert manifest.version == "v001"
    s5 = [item for item in manifest.items if item.segment == "S5_unanswerable"]
    assert all(item.required_slides for item in s5)


def test_recall_and_ndcg() -> None:
    required = {10, 11}
    ranked = [5, 10, 3, 11, 1]
    assert recall_at_k(ranked, required, k=5) == 1.0
    assert set_recall_at_k(ranked, required, k=5) == 1.0
    assert ndcg_at_k(ranked, required, k=5) > 0.0


def test_s5_trap_slides_scoring() -> None:
    item = MultimodalDatasetItem(
        id="S5-test",
        segment="S5_unanswerable",
        question="test?",
        reference_answer="нет ответа",
        trap_slides=[10],
        expected_behavior="refusal",
        metadata=ItemMetadata(reviewed_by="test"),
    )
    scores = score_item(item, [10, 2, 3, 4, 5], k=5)
    assert scores.ndcg_at_5 == 0.0
    assert scores.recall_at_k == 0.0
    assert scores.trap_slide_in_topk == 1.0


def test_s5_legacy_required_slides_fallback() -> None:
    item = MultimodalDatasetItem(
        id="S5-legacy",
        segment="S5_unanswerable",
        question="test?",
        reference_answer="нет ответа",
        required_slides=[10],
        expected_behavior="refusal",
        metadata=ItemMetadata(reviewed_by="test"),
    )
    scores = score_item(item, [10, 2, 3, 4, 5], k=5)
    assert scores.trap_slide_in_topk == 1.0


def test_aggregate_by_segment() -> None:
    item = MultimodalDatasetItem(
        id="S1-test",
        segment="S1_text",
        question="q",
        reference_answer="a",
        required_slides=[2],
        metadata=ItemMetadata(reviewed_by="test"),
    )
    scores = score_item(item, [2, 1, 3], k=3)
    agg = aggregate_by_segment([(item.segment, scores)])
    assert agg["S1_text"]["recall_at_k"] == 1.0
