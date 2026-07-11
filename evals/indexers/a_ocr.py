"""Method A indexer: OCR → artifact txt → e5 → Qdrant."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from indexers.base import IndexCost, validate_corpus_dir
from indexers.config import MultimodalEvalConfig
from indexers.ocr.factory import run_ocr_batch
from scripts.multimodal_retrieval import E5Embedder, stable_point_id, strip_corpus_header

logger = logging.getLogger(__name__)


class AOcrIndexer:
    """OCR all PNG slides, embed with e5, upsert to Qdrant."""

    def __init__(self, cfg: MultimodalEvalConfig) -> None:
        self._cfg = cfg
        self.ocr_engine = os.environ.get("OCR_ENGINE", cfg.ocr_engine or "tesseract")
        self.corpus_stats: dict[int, int] = {}
        self.indexed_slides: int = 0
        self.ocr_time_s: float = 0.0
        self.embed_time_s: float = 0.0

    def build_index(self, corpus_dir: Path) -> IndexCost:
        validate_corpus_dir(corpus_dir)
        if self._cfg.artifact_dir is None:
            msg = "a_ocr indexer requires artifact_dir in config"
            raise ValueError(msg)

        ocr_start = time.perf_counter()
        run_ocr_batch(
            self.ocr_engine,
            corpus_dir,
            self._cfg.artifact_dir,
            runtime=self._cfg.ocr_runtime,
        )
        self.ocr_time_s = time.perf_counter() - ocr_start
        logger.info("OCR (%s) finished in %.2fs", self.ocr_engine, self.ocr_time_s)

        slide_files = sorted(self._cfg.artifact_dir.glob("slide-*.txt"))
        texts: list[str] = []
        slide_ids: list[int] = []
        for path in slide_files:
            slide_id = int(path.stem.split("-")[1])
            body = path.read_text(encoding="utf-8")
            stripped = strip_corpus_header(body)
            texts.append(stripped)
            slide_ids.append(slide_id)
            self.corpus_stats[slide_id] = len(stripped)

        embed_start = time.perf_counter()
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

        method_tag = f"ocr_{self.ocr_engine}"
        points = [
            PointStruct(
                id=stable_point_id(method_tag, slide_id),
                vector=vector,
                payload={
                    "slide_id": slide_id,
                    "text": text,
                    "source": f"slide-{slide_id:02d}.txt",
                    "method": method_tag,
                    "ocr_engine": self.ocr_engine,
                },
            )
            for slide_id, text, vector in zip(slide_ids, texts, vectors, strict=True)
        ]
        client.upsert(collection_name=self._cfg.collection, points=points)
        self.embed_time_s = time.perf_counter() - embed_start
        build_time_s = self.ocr_time_s + self.embed_time_s
        self.indexed_slides = len(points)

        index_size_mb: float | None = None
        try:
            info = client.get_collection(self._cfg.collection)
            if info.points_count:
                index_size_mb = (self._cfg.embedding_dim * 4 * info.points_count) / (1024 * 1024)
        except Exception:  # noqa: BLE001
            index_size_mb = None

        logger.info(
            "Indexed %d slides (embed/upsert %.2fs, total %.2fs)",
            self.indexed_slides,
            self.embed_time_s,
            build_time_s,
        )

        return IndexCost(
            collection=self._cfg.collection,
            index_size_mb=index_size_mb,
            build_time_s=build_time_s,
            api_calls=0,
            est_cost_usd=0.0,
            is_multivector=False,
        )
