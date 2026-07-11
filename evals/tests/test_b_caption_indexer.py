"""Tests for BCaptionIndexer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from indexers.b_caption import BCaptionIndexer
from indexers.config import EVALS_ROOT
from indexers.factory import load_multimodal_config


def test_b_caption_indexer_build_index_mocked(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    artifact_dir = tmp_path / "artifacts"
    corpus_dir.mkdir()
    (corpus_dir / "slide-01.png").write_bytes(b"png")
    (corpus_dir / "slide-02.png").write_bytes(b"png")

    cfg = load_multimodal_config(
        EVALS_ROOT / "configs" / "multimodal-b-caption-nemotron.yaml",
    )
    cfg.corpus_dir = corpus_dir
    cfg.artifact_dir = artifact_dir
    cfg.collection = "test_multimodal_caption_unit"

    indexer = BCaptionIndexer(cfg)
    fake_vector = [0.0] * cfg.embedding_dim

    def fake_batch(
        model_id: str,
        corpus: Path,
        out_dir: Path,
        *,
        slide_ids: list[int] | None = None,
    ) -> tuple[float, float, int]:
        out_dir.mkdir(parents=True, exist_ok=True)
        for slide_id in (1, 2):
            out_dir.joinpath(f"slide-{slide_id:02d}.txt").write_text(
                f"# slide-{slide_id:02d}\n# model: {model_id}\nSlide {slide_id} caption",
                encoding="utf-8",
            )
        return 1.5, 0.0, 2

    with (
        patch("indexers.b_caption.run_caption_batch", side_effect=fake_batch),
        patch("indexers.b_caption.E5Embedder") as embedder_cls,
        patch("indexers.b_caption.QdrantClient") as client_cls,
    ):
        embedder_cls.return_value.embed_passages.return_value = [fake_vector, fake_vector]
        client = MagicMock()
        client.collection_exists.return_value = False
        client.get_collection.return_value = MagicMock(points_count=2)
        client_cls.return_value = client

        cost = indexer.build_index(corpus_dir)

    assert cost.collection == "test_multimodal_caption_unit"
    assert cost.build_time_s >= 1.5
    assert cost.est_cost_usd == 0.0
    assert cost.api_calls == 2
    assert cost.is_multivector is False
    assert indexer.indexed_slides == 2
    assert indexer.corpus_stats[1] > 0
    assert (artifact_dir / "slide-01.txt").exists()
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()


def test_b_caption_requires_artifact_dir(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "slide-01.png").write_bytes(b"png")

    cfg = load_multimodal_config(
        EVALS_ROOT / "configs" / "multimodal-b-caption-nemotron.yaml",
    )
    cfg.corpus_dir = corpus_dir
    cfg.artifact_dir = None

    indexer = BCaptionIndexer(cfg)
    with pytest.raises(ValueError, match="artifact_dir"):
        indexer.build_index(corpus_dir)
