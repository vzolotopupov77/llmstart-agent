"""Multimodal eval configuration model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MultimodalEvalConfig:
    """Unified eval config: indexer params + shared retrieval block."""

    config_id: str
    dataset_path: Path
    indexer_method: str
    corpus_dir: Path
    artifact_dir: Path | None
    pdf_name: str | None
    ocr_engine: str | None
    ocr_runtime: str | None
    caption_model: str | None
    d_max_side: int | None
    collection: str
    embedding_model: str
    embedding_dim: int
    top_k: int
    qdrant_url: str
    is_multivector: bool
