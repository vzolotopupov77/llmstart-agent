"""Tests for multimodal indexer registry and corpus validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from indexers.a_ocr import AOcrIndexer
from indexers.b_caption import BCaptionIndexer
from indexers.base import validate_corpus_dir
from indexers.baseline import BaselineIndexer
from indexers.c_unified import CUnifiedIndexer
from indexers.config import EVALS_ROOT
from indexers.d_multivector import DMultivectorIndexer
from indexers.factory import load_multimodal_config, make_indexer

CONFIGS = [
    ("multimodal-baseline.yaml", BaselineIndexer),
    ("multimodal-a-ocr-tesseract.yaml", AOcrIndexer),
    ("multimodal-a-ocr-modern.yaml", AOcrIndexer),
    ("multimodal-b-caption-nemotron.yaml", BCaptionIndexer),
    ("multimodal-b-caption-gemini.yaml", BCaptionIndexer),
    ("multimodal-c-unified.yaml", CUnifiedIndexer),
    ("multimodal-d-multivector.yaml", DMultivectorIndexer),
]


@pytest.mark.parametrize(("filename", "expected_cls"), CONFIGS)
def test_make_indexer_from_config(filename: str, expected_cls: type) -> None:
    cfg = load_multimodal_config(EVALS_ROOT / "configs" / filename)
    indexer = make_indexer(cfg)
    assert isinstance(indexer, expected_cls)


def test_validate_corpus_dir_rejects_txt(tmp_path: Path) -> None:
    (tmp_path / "slide-01.png").write_bytes(b"png")
    (tmp_path / "notes.txt").write_text("forbidden", encoding="utf-8")
    with pytest.raises(ValueError, match="notes.txt"):
        validate_corpus_dir(tmp_path)


def test_validate_corpus_dir_accepts_pdf_and_png(tmp_path: Path) -> None:
    (tmp_path / "slide-01.png").write_bytes(b"png")
    (tmp_path / "slide-01.pdf").write_bytes(b"pdf")
    validate_corpus_dir(tmp_path)


def test_baseline_indexer_build_index_mocked(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    artifact_dir = tmp_path / "artifacts"
    corpus_dir.mkdir()
    pdf_path = corpus_dir / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 minimal")

    cfg = load_multimodal_config(EVALS_ROOT / "configs" / "multimodal-baseline.yaml")
    cfg.corpus_dir = corpus_dir
    cfg.artifact_dir = artifact_dir
    cfg.pdf_name = "deck.pdf"
    cfg.collection = "test_multimodal_baseline_unit"

    indexer = BaselineIndexer(cfg)
    fake_vector = [0.0] * cfg.embedding_dim

    with (
        patch("indexers.baseline.extract_pdf_pages", return_value={1: "hello", 2: ""}),
        patch("indexers.baseline.E5Embedder") as embedder_cls,
        patch("indexers.baseline.QdrantClient") as client_cls,
    ):
        embedder_cls.return_value.embed_passages.return_value = [fake_vector, fake_vector]
        client = MagicMock()
        client.collection_exists.return_value = False
        client.get_collection.return_value = MagicMock(points_count=2)
        client_cls.return_value = client

        cost = indexer.build_index(corpus_dir)

    assert cost.collection == "test_multimodal_baseline_unit"
    assert cost.build_time_s >= 0
    assert cost.est_cost_usd == 0.0
    assert cost.is_multivector is False
    assert indexer.indexed_slides == 2
    assert indexer.corpus_stats[1] == 5
    assert (artifact_dir / "slide-01.txt").exists()
    client.create_collection.assert_called_once()
    client.upsert.assert_called_once()
