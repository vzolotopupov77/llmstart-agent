"""Host wrapper for OCR docker batch (used by Makefile)."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from indexers.config import REPO_ROOT
from indexers.ocr.factory import run_ocr_batch

logger = logging.getLogger(__name__)

DEFAULT_CORPUS = REPO_ROOT / "data" / "multimodal-rag"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OCR batch via docker or local runtime")
    parser.add_argument("engine", choices=["tesseract", "easyocr", "rapidocr"])
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="defaults to evals/artifacts/ocr/{engine}",
    )
    args = parser.parse_args()

    artifact_dir = args.artifact_dir or (REPO_ROOT / "evals" / "artifacts" / "ocr" / args.engine)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_ocr_batch(args.engine, args.corpus_dir, artifact_dir)
    logger.info("Artifacts: %s", artifact_dir)


if __name__ == "__main__":
    main()
