"""Stub indexers for methods not yet implemented."""

from __future__ import annotations

from pathlib import Path

from indexers.base import IndexCost, validate_corpus_dir
from indexers.config import MultimodalEvalConfig


class _StubIndexer:
    """Base for not-yet-implemented indexing methods."""

    task_id: str = ""

    def __init__(self, cfg: MultimodalEvalConfig) -> None:
        self._cfg = cfg

    def build_index(self, corpus_dir: Path) -> IndexCost:
        validate_corpus_dir(corpus_dir)
        msg = f"{self.__class__.__name__} is not implemented yet (Sprint-10 {self.task_id})"
        raise NotImplementedError(msg)
