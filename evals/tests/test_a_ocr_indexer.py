"""Tests for AOcrIndexer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from indexers.a_ocr import AOcrIndexer
from indexers.config import EVALS_ROOT
from indexers.factory import load_multimodal_config


def test_a_ocr_indexer_build_index_mocked(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    artifact_dir = tmp_path / "artifacts"
    corpus_dir.mkdir()
    artifact_dir.mkdir()
    (corpus_dir / "slide-01.png").write_bytes(b"png")
    (artifact_dir / "slide-01.txt").write_text(
        "# slide-01\n# source: OCR tesseract (slide-01.png)\n# engine: tesseract\nhello ocr",
        encoding="utf-8",
    )

    cfg = load_multimodal_config(EVALS_ROOT / "configs" / "multimodal-a-ocr-tesseract.yaml")
    cfg.corpus_dir = corpus_dir
    cfg.artifact_dir = artifact_dir
    cfg.collection = "test_multimodal_ocr_unit"

    indexer = AOcrIndexer(cfg)
    fake_vector = [0.0] * cfg.embedding_dim

    with (
        patch("indexers.a_ocr.run_ocr_batch") as run_batch,
        patch("indexers.a_ocr.E5Embedder") as embedder_cls,
        patch("indexers.a_ocr.QdrantClient") as client_cls,
    ):
        run_batch.side_effect = lambda *_args, **_kwargs: None
        embedder_cls.return_value.embed_passages.return_value = [fake_vector]
        client = MagicMock()
        client.collection_exists.return_value = False
        client.get_collection.return_value = MagicMock(points_count=1)
        client_cls.return_value = client

        cost = indexer.build_index(corpus_dir)

    run_batch.assert_called_once()
    assert cost.collection == "test_multimodal_ocr_unit"
    assert cost.est_cost_usd == 0.0
    assert cost.is_multivector is False
    assert indexer.indexed_slides == 1
    assert indexer.corpus_stats[1] == len("hello ocr")
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
