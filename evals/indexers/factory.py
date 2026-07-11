"""Load multimodal eval config and construct indexers."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from indexers.config import REPO_ROOT, MultimodalEvalConfig


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_multimodal_config(path: Path) -> MultimodalEvalConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    indexer = raw["indexer"]
    retrieval = raw["retrieval"]
    method = indexer["method"]

    artifact_raw = indexer.get("artifact_dir")
    artifact_dir = _resolve_path(artifact_raw) if artifact_raw else None

    ocr_engine = os.environ.get("OCR_ENGINE", indexer.get("ocr_engine"))
    ocr_runtime = os.environ.get("OCR_RUNTIME", indexer.get("ocr_runtime"))
    caption_model = os.environ.get("CAPTION_MODEL", indexer.get("caption_model"))
    if method == "d_multivector":
        embedding_model = os.environ.get("JINA_EMBED_MODEL", retrieval.get("embedding_model"))
    else:
        embedding_model = os.environ.get("EMBED_VL_MODEL", retrieval.get("embedding_model"))
    d_max_side_raw = os.environ.get("D_MAX_SIDE", str(indexer.get("d_max_side", "")))
    d_max_side = int(d_max_side_raw) if d_max_side_raw else None

    return MultimodalEvalConfig(
        config_id=raw["config_id"],
        dataset_path=_resolve_path(raw["dataset"]),
        indexer_method=method,
        corpus_dir=_resolve_path(indexer["corpus_dir"]),
        artifact_dir=artifact_dir,
        pdf_name=indexer.get("pdf"),
        ocr_engine=ocr_engine,
        ocr_runtime=ocr_runtime,
        caption_model=caption_model,
        d_max_side=d_max_side,
        collection=retrieval["collection"],
        embedding_model=embedding_model,
        embedding_dim=int(retrieval["embedding_dim"]),
        top_k=int(retrieval["top_k"]),
        qdrant_url=retrieval.get("qdrant_url", "http://localhost:6333"),
        is_multivector=bool(retrieval.get("is_multivector", method == "d_multivector")),
    )


def make_indexer(cfg: MultimodalEvalConfig):
    """Return indexer instance for config method."""
    from indexers.registry import INDEXER_REGISTRY  # noqa: PLC0415

    try:
        indexer_cls = INDEXER_REGISTRY[cfg.indexer_method]
    except KeyError as exc:
        allowed = ", ".join(sorted(INDEXER_REGISTRY))
        msg = f"unknown indexer.method {cfg.indexer_method!r}; expected one of: {allowed}"
        raise ValueError(msg) from exc
    return indexer_cls(cfg)
