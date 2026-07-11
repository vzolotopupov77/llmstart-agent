"""OCR batch runner for RapidOCR (ONNX, CPU, Cyrillic via multilingual model)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from preprocess import preprocess_for_ocr
from rapidocr_onnxruntime import RapidOCR

CORPUS_DIR = Path("/corpus")
OUT_DIR = Path("/out")
ENGINE = "rapidocr"


def write_artifact(out_path: Path, slide_id: int, png_name: str, text: str) -> None:
    header = (
        f"# slide-{slide_id:02d}\n"
        f"# source: OCR {ENGINE} ({png_name})\n"
        f"# engine: {ENGINE} | backend: onnxruntime | lang: ru+en\n"
    )
    out_path.write_text(header + text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_files = sorted(CORPUS_DIR.glob("slide-*.png"))
    if not png_files:
        print(f"No PNG files in {CORPUS_DIR}", file=sys.stderr)
        return 1

    engine = RapidOCR()
    for png_path in png_files:
        slide_id = int(png_path.stem.split("-")[1])
        processed = preprocess_for_ocr(png_path)
        array = np.array(processed)
        result, _ = engine(array)
        lines: list[str] = []
        if result:
            lines = [str(item[1]).strip() for item in result if item[1]]
        text = "\n".join(line for line in lines if line)
        write_artifact(OUT_DIR / f"slide-{slide_id:02d}.txt", slide_id, png_path.name, text)
        print(f"slide-{slide_id:02d}: {len(text)} chars")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
