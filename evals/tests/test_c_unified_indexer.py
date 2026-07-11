"""Tests for CUnifiedIndexer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from indexers.c_unified import CUnifiedIndexer
from indexers.config import EVALS_ROOT
from indexers.factory import load_multimodal_config


def test_c_unified_indexer_build_index_mocked(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "slide-01.png").write_bytes(b"png")
    (corpus_dir / "slide-02.png").write_bytes(b"png")

    cfg = load_multimodal_config(EVALS_ROOT / "configs" / "multimodal-c-unified.yaml")
    cfg.corpus_dir = corpus_dir
    cfg.collection = "test_multimodal_unified_unit"

    indexer = CUnifiedIndexer(cfg)
    fake_vector = [0.0] * cfg.embedding_dim

    def fake_batch(
        model_id: str,
        corpus: Path,
        *,
        slide_ids: list[int] | None = None,
    ) -> tuple[list[tuple[int, list[float]]], float, float, int]:
        return [(1, fake_vector), (2, fake_vector)], 2.5, 0.0, 2

    with (
        patch("indexers.c_unified.run_embed_batch", side_effect=fake_batch),
        patch("indexers.c_unified.QdrantClient") as client_cls,
    ):
        client = MagicMock()
        client.collection_exists.return_value = False
        client.get_collection.return_value = MagicMock(points_count=2)
        client_cls.return_value = client

        cost = indexer.build_index(corpus_dir)

    assert cost.collection == "test_multimodal_unified_unit"
    assert cost.build_time_s >= 2.5
    assert cost.est_cost_usd == 0.0
    assert cost.api_calls == 2
    assert cost.is_multivector is False
    assert indexer.indexed_slides == 2
    assert indexer.corpus_stats[1] == 1
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
