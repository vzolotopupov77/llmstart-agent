"""Method C indexer: PNG → VL image embed → Qdrant."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from indexers.base import IndexCost, validate_corpus_dir
from indexers.caption.pricing import model_slug
from indexers.config import MultimodalEvalConfig
from indexers.vl_embed.factory import run_embed_batch
from scripts.multimodal_retrieval import stable_point_id

logger = logging.getLogger(__name__)


class CUnifiedIndexer:
    """Embed slide PNGs directly via VL model and upsert to Qdrant."""

    def __init__(self, cfg: MultimodalEvalConfig) -> None:
        self._cfg = cfg
        self.embed_model = os.environ.get("EMBED_VL_MODEL", cfg.embedding_model)
        self.corpus_stats: dict[int, int] = {}
        self.indexed_slides: int = 0
        self.embed_time_s: float = 0.0
        self.upsert_time_s: float = 0.0
        self.api_calls: int = 0

    def build_index(self, corpus_dir: Path) -> IndexCost:
        validate_corpus_dir(corpus_dir)

        slide_vectors, embed_time_s, est_cost_usd, api_calls = run_embed_batch(
            self.embed_model,
            corpus_dir,
        )
        self.embed_time_s = embed_time_s
        self.api_calls = api_calls
        logger.info(
            "VL embed (%s) finished in %.2fs, cost=$%.6f, calls=%d",
            model_slug(self.embed_model),
            self.embed_time_s,
            est_cost_usd,
            api_calls,
        )

        upsert_start = time.perf_counter()
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

        slug = model_slug(self.embed_model)
        method_tag = f"unified_{slug}"
        points = [
            PointStruct(
                id=stable_point_id(method_tag, slide_id),
                vector=vector,
                payload={
                    "slide_id": slide_id,
                    "source": f"slide-{slide_id:02d}.png",
                    "method": method_tag,
                    "embed_model": self.embed_model,
                },
            )
            for slide_id, vector in slide_vectors
        ]
        client.upsert(collection_name=self._cfg.collection, points=points)
        self.upsert_time_s = time.perf_counter() - upsert_start
        build_time_s = self.embed_time_s + self.upsert_time_s
        self.indexed_slides = len(points)
        self.corpus_stats = {slide_id: 1 for slide_id, _ in slide_vectors}

        index_size_mb: float | None = None
        try:
            info = client.get_collection(self._cfg.collection)
            if info.points_count:
                index_size_mb = (self._cfg.embedding_dim * 4 * info.points_count) / (1024 * 1024)
        except Exception:  # noqa: BLE001
            index_size_mb = None

        logger.info(
            "Indexed %d slides (upsert %.2fs, total %.2fs)",
            self.indexed_slides,
            self.upsert_time_s,
            build_time_s,
        )

        return IndexCost(
            collection=self._cfg.collection,
            index_size_mb=index_size_mb,
            build_time_s=build_time_s,
            api_calls=api_calls,
            est_cost_usd=est_cost_usd,
            is_multivector=False,
        )
