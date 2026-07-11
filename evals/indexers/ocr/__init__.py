"""OCR engine adapters for method A indexing."""

from indexers.ocr.base import OcrEngine
from indexers.ocr.factory import make_ocr_engine, run_ocr_batch

__all__ = ["OcrEngine", "make_ocr_engine", "run_ocr_batch"]
