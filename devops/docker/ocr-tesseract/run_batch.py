"""OCR batch runner for Tesseract (rus+eng, PSM 6) via CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from preprocess import preprocess_for_ocr

CORPUS_DIR = Path("/corpus")
OUT_DIR = Path("/out")
LANG = "rus+eng"
PSM = 6
ENGINE = "tesseract"


def write_artifact(out_path: Path, slide_id: int, png_name: str, text: str) -> None:
    header = (
        f"# slide-{slide_id:02d}\n"
        f"# source: OCR {ENGINE} ({png_name})\n"
        f"# engine: {ENGINE} | lang: {LANG} | psm: {PSM}\n"
    )
    out_path.write_text(header + text, encoding="utf-8")


def recognize_tesseract(image_path: Path) -> str:
    processed = preprocess_for_ocr(image_path)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        processed.save(tmp_path)
        result = subprocess.run(
            [
                "tesseract",
                str(tmp_path),
                "stdout",
                "-l",
                LANG,
                "--psm",
                str(PSM),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or "tesseract failed"
            raise RuntimeError(stderr)
        return result.stdout.strip()
    finally:
        tmp_path.unlink(missing_ok=True)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_files = sorted(CORPUS_DIR.glob("slide-*.png"))
    if not png_files:
        print(f"No PNG files in {CORPUS_DIR}", file=sys.stderr)
        return 1

    for png_path in png_files:
        slide_id = int(png_path.stem.split("-")[1])
        text = recognize_tesseract(png_path)
        write_artifact(OUT_DIR / f"slide-{slide_id:02d}.txt", slide_id, png_path.name, text)
        print(f"slide-{slide_id:02d}: {len(text)} chars")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
