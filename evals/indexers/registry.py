"""Indexer registry."""

from __future__ import annotations

from indexers.a_ocr import AOcrIndexer
from indexers.b_caption import BCaptionIndexer
from indexers.baseline import BaselineIndexer
from indexers.c_unified import CUnifiedIndexer
from indexers.d_multivector import DMultivectorIndexer

INDEXER_REGISTRY: dict[str, type] = {
    "baseline": BaselineIndexer,
    "a_ocr": AOcrIndexer,
    "b_caption": BCaptionIndexer,
    "c_unified": CUnifiedIndexer,
    "d_multivector": DMultivectorIndexer,
}
