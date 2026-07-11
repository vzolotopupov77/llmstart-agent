"""Baseline indexer: PDF text layer → artifact txt → e5 → Qdrant."""

from __future__ import annotations

import time
from pathlib import Path

from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from indexers.base import IndexCost, validate_corpus_dir
from indexers.config import MultimodalEvalConfig
from scripts.multimodal_retrieval import E5Embedder, stable_point_id, strip_corpus_header


def extract_pdf_pages(pdf_path: Path) -> dict[int, str]:
    reader = PdfReader(str(pdf_path))
    pages: dict[int, str] = {}
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages[index] = text
    return pages


def write_text_naive_artifacts(
    pdf_path: Path,
    artifact_dir: Path,
) -> dict[int, int]:
    """Write slide-NN.txt files; return slide_id -> char count (body only)."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pages = extract_pdf_pages(pdf_path)
    stats: dict[int, int] = {}
    for slide_id in range(1, len(pages) + 1):
        text = pages.get(slide_id, "")
        out_path = artifact_dir / f"slide-{slide_id:02d}.txt"
        header = (
            f"# slide-{slide_id:02d}\n# source: PDF text layer ({pdf_path.name}, page {slide_id})\n"
        )
        if not text:
            header += "# status: empty (image-only slide)\n"
        out_path.write_text(header + text, encoding="utf-8")
        stats[slide_id] = len(text)
    return stats


class BaselineIndexer:
    """Naive PDF text-layer extraction (not OCR) + dense e5 indexing."""

    def __init__(self, cfg: MultimodalEvalConfig) -> None:
        self._cfg = cfg
        self.corpus_stats: dict[int, int] = {}
        self.indexed_slides: int = 0

    def build_index(self, corpus_dir: Path) -> IndexCost:
        validate_corpus_dir(corpus_dir)
        if self._cfg.artifact_dir is None:
            msg = "baseline indexer requires artifact_dir in config"
            raise ValueError(msg)
        if self._cfg.pdf_name is None:
            msg = "baseline indexer requires pdf in config"
            raise ValueError(msg)

        pdf_path = corpus_dir / self._cfg.pdf_name
        if not pdf_path.is_file():
            msg = f"PDF not found in corpus_dir: {pdf_path.name}"
            raise FileNotFoundError(msg)

        self.corpus_stats = write_text_naive_artifacts(pdf_path, self._cfg.artifact_dir)

        slide_files = sorted(self._cfg.artifact_dir.glob("slide-*.txt"))
        texts: list[str] = []
        slide_ids: list[int] = []
        for path in slide_files:
            slide_id = int(path.stem.split("-")[1])
            body = path.read_text(encoding="utf-8")
            texts.append(strip_corpus_header(body))
            slide_ids.append(slide_id)

        start = time.perf_counter()
        embedder = E5Embedder(self._cfg.embedding_model)
        vectors = embedder.embed_passages(texts)
        client = QdrantClient(url=self._cfg.qdrant_url)

        if client.collection_exists(self._cfg.collection):
            client.delete_collection(self._cfg.collection)
        client.create_collection(
            collection_name=self._cfg.collection,
            vectors_config=VectorParams(
                size=self._cfg.embedding_dim,
                distance=Distance.COSINE,
            ),
        )

        points = [
            PointStruct(
                id=stable_point_id("naive", slide_id),
                vector=vector,
                payload={
                    "slide_id": slide_id,
                    "text": text,
                    "source": f"slide-{slide_id:02d}.txt",
                    "method": "text_naive",
                },
            )
            for slide_id, text, vector in zip(slide_ids, texts, vectors, strict=True)
        ]
        client.upsert(collection_name=self._cfg.collection, points=points)
        build_time_s = time.perf_counter() - start
        self.indexed_slides = len(points)

        index_size_mb: float | None = None
        try:
            info = client.get_collection(self._cfg.collection)
            if info.points_count:
                index_size_mb = (self._cfg.embedding_dim * 4 * info.points_count) / (1024 * 1024)
        except Exception:  # noqa: BLE001
            index_size_mb = None

        return IndexCost(
            collection=self._cfg.collection,
            index_size_mb=index_size_mb,
            build_time_s=build_time_s,
            api_calls=0,
            est_cost_usd=0.0,
            is_multivector=False,
        )
