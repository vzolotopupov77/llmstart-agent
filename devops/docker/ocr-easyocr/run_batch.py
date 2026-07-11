"""OCR batch runner for EasyOCR (ru+en, CPU)."""

from __future__ import annotations

import sys
from pathlib import Path

import easyocr
import numpy as np
from PIL import Image

from preprocess import preprocess_for_ocr

CORPUS_DIR = Path("/corpus")
OUT_DIR = Path("/out")
ENGINE = "easyocr"
LANGUAGES = ["ru", "en"]


def write_artifact(out_path: Path, slide_id: int, png_name: str, text: str) -> None:
    header = (
        f"# slide-{slide_id:02d}\n"
        f"# source: OCR {ENGINE} ({png_name})\n"
        f"# engine: {ENGINE} | lang: ru+en | gpu: false\n"
    )
    out_path.write_text(header + text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_files = sorted(CORPUS_DIR.glob("slide-*.png"))
    if not png_files:
        print(f"No PNG files in {CORPUS_DIR}", file=sys.stderr)
        return 1

    reader = easyocr.Reader(LANGUAGES, gpu=False)
    for png_path in png_files:
        slide_id = int(png_path.stem.split("-")[1])
        processed = preprocess_for_ocr(png_path)
        array = np.array(processed)
        lines = reader.readtext(array, detail=0, paragraph=True)
        text = "\n".join(line.strip() for line in lines if line.strip())
        write_artifact(OUT_DIR / f"slide-{slide_id:02d}.txt", slide_id, png_path.name, text)
        print(f"slide-{slide_id:02d}: {len(text)} chars")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
