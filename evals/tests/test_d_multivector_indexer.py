"""Tests for DMultivectorIndexer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from indexers.config import EVALS_ROOT
from indexers.d_multivector import DMultivectorIndexer
from indexers.factory import load_multimodal_config


def test_d_multivector_indexer_build_index_mocked(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "slide-01.png").write_bytes(b"png")
    (corpus_dir / "slide-02.png").write_bytes(b"png")

    cfg = load_multimodal_config(EVALS_ROOT / "configs" / "multimodal-d-multivector.yaml")
    cfg.corpus_dir = corpus_dir
    cfg.collection = "test_multimodal_d_unit"

    indexer = DMultivectorIndexer(cfg)
    fake_vectors = [[0.0] * cfg.embedding_dim, [0.1] * cfg.embedding_dim]

    def fake_batch(
        model_id: str,
        corpus: Path,
        *,
        max_side: int,
        token_dim: int = 128,
        slide_ids: list[int] | None = None,
    ) -> tuple[list[tuple[int, list[list[float]]]], float, float, int]:
        return [(1, fake_vectors), (2, fake_vectors)], 3.0, 0.01, 2

    with (
        patch("indexers.d_multivector.run_embed_batch", side_effect=fake_batch),
        patch("indexers.d_multivector.QdrantClient") as client_cls,
    ):
        client = MagicMock()
        client.collection_exists.return_value = False
        client_cls.return_value = client

        cost = indexer.build_index(corpus_dir)

    assert cost.collection == "test_multimodal_d_unit"
    assert cost.build_time_s >= 3.0
    assert cost.est_cost_usd == 0.01
    assert cost.api_calls == 2
    assert cost.is_multivector is True
    assert cost.index_size_mb is not None
    assert indexer.indexed_slides == 2
    assert indexer.total_tokens == 4
    client.create_collection.assert_called_once()
    assert client.upsert.call_count == 2
