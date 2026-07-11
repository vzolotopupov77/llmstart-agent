"""Indexer contract and corpus validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ALLOWED_CORPUS_SUFFIXES = frozenset({".pdf", ".png"})


@dataclass(frozen=True)
class IndexCost:
    """Cost and size metrics for one indexing run."""

    collection: str
    index_size_mb: float | None
    build_time_s: float
    api_calls: int
    est_cost_usd: float
    is_multivector: bool


class Indexer(Protocol):
    """Builds a Qdrant collection from a source corpus directory."""

    def build_index(self, corpus_dir: Path) -> IndexCost:
        """Validate corpus, ingest, upsert vectors; return indexing cost."""
        ...


def validate_corpus_dir(corpus_dir: Path) -> None:
    """Fail fast if corpus_dir contains anything other than PDF or PNG files."""
    if not corpus_dir.is_dir():
        msg = f"corpus_dir is not a directory: {corpus_dir}"
        raise ValueError(msg)

    invalid: list[str] = []
    for path in sorted(corpus_dir.iterdir()):
        if not path.is_file():
            invalid.append(f"{path.name}/ (not a file)")
            continue
        if path.suffix.lower() not in ALLOWED_CORPUS_SUFFIXES:
            invalid.append(path.name)

    if invalid:
        allowed = ", ".join(sorted(ALLOWED_CORPUS_SUFFIXES))
        listed = ", ".join(invalid)
        msg = f"corpus_dir must contain only {allowed}; found: {listed}"
        raise ValueError(msg)
