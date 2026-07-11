"""Run OCR batch via Docker or local engines."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from indexers.config import REPO_ROOT
from indexers.ocr.base import OcrEngine

logger = logging.getLogger(__name__)

OCR_COMPOSE_FILE = REPO_ROOT / "devops" / "docker-compose.ocr.yml"
SUPPORTED_ENGINES = frozenset({"tesseract", "easyocr", "rapidocr"})


def _artifact_header(engine: str, slide_id: int, png_name: str) -> str:
    if engine == "tesseract":
        meta = "# engine: tesseract | lang: rus+eng | psm: 6"
    elif engine == "easyocr":
        meta = "# engine: easyocr | lang: ru+en | gpu: false"
    else:
        meta = "# engine: rapidocr | backend: onnxruntime | lang: ru+en"
    return (
        f"# slide-{slide_id:02d}\n"
        f"# source: OCR {engine} ({png_name})\n"
        f"{meta}\n"
    )


def write_ocr_artifact(
    artifact_dir: Path,
    *,
    engine: str,
    slide_id: int,
    png_name: str,
    text: str,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / f"slide-{slide_id:02d}.txt"
    out_path.write_text(_artifact_header(engine, slide_id, png_name) + text, encoding="utf-8")


class LocalTesseractEngine:
    name = "tesseract"

    def recognize(self, image_path: Path) -> str:
        import pytesseract  # noqa: PLC0415

        from indexers.ocr.preprocess import preprocess_for_ocr  # noqa: PLC0415

        processed = preprocess_for_ocr(image_path)
        config = "--psm 6 -l rus+eng"
        return pytesseract.image_to_string(processed, config=config).strip()


class LocalEasyocrEngine:
    name = "easyocr"

    def __init__(self) -> None:
        import easyocr  # noqa: PLC0415

        self._reader = easyocr.Reader(["ru", "en"], gpu=False)

    def recognize(self, image_path: Path) -> str:
        import numpy as np  # noqa: PLC0415

        from indexers.ocr.preprocess import preprocess_for_ocr  # noqa: PLC0415

        processed = preprocess_for_ocr(image_path)
        array = np.array(processed)
        lines = self._reader.readtext(array, detail=0, paragraph=True)
        return "\n".join(line.strip() for line in lines if line.strip())


class LocalRapidocrEngine:
    name = "rapidocr"

    def __init__(self) -> None:
        from rapidocr_onnxruntime import RapidOCR  # noqa: PLC0415

        self._engine = RapidOCR()

    def recognize(self, image_path: Path) -> str:
        import numpy as np  # noqa: PLC0415

        from indexers.ocr.preprocess import preprocess_for_ocr  # noqa: PLC0415

        processed = preprocess_for_ocr(image_path)
        array = np.array(processed)
        result, _ = self._engine(array)
        if not result:
            return ""
        return "\n".join(str(item[1]).strip() for item in result if item[1])


def make_ocr_engine(engine: str, *, runtime: str | None = None) -> OcrEngine:
    runtime_value = runtime or os.environ.get("OCR_RUNTIME", "docker")
    if engine not in SUPPORTED_ENGINES:
        allowed = ", ".join(sorted(SUPPORTED_ENGINES))
        msg = f"unsupported OCR engine {engine!r}; expected one of: {allowed}"
        raise ValueError(msg)
    if runtime_value == "docker":
        msg = "make_ocr_engine with runtime=docker is not supported; use run_ocr_batch()"
        raise ValueError(msg)
    if engine == "tesseract":
        return LocalTesseractEngine()
    if engine == "easyocr":
        return LocalEasyocrEngine()
    return LocalRapidocrEngine()


def _ensure_docker() -> None:
    if shutil.which("docker") is None:
        msg = "docker not found; install Docker or set OCR_RUNTIME=local"
        raise RuntimeError(msg)


def run_docker_ocr_batch(engine: str, corpus_dir: Path, artifact_dir: Path) -> None:
    if engine not in SUPPORTED_ENGINES:
        allowed = ", ".join(sorted(SUPPORTED_ENGINES))
        msg = f"unsupported OCR engine {engine!r}; expected one of: {allowed}"
        raise ValueError(msg)

    _ensure_docker()
    service = f"ocr-{engine}"
    env = os.environ.copy()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker",
        "compose",
        "-f",
        str(OCR_COMPOSE_FILE),
        "run",
        "--rm",
        service,
    ]
    logger.info("Running OCR batch: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=OCR_COMPOSE_FILE.parent,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown docker error"
        msg = f"OCR docker batch failed for {engine}: {stderr}"
        raise RuntimeError(msg)


def run_local_ocr_batch(engine: str, corpus_dir: Path, artifact_dir: Path) -> None:
    ocr = make_ocr_engine(engine, runtime="local")
    png_files = sorted(corpus_dir.glob("slide-*.png"))
    for png_path in png_files:
        slide_id = int(png_path.stem.split("-")[1])
        text = ocr.recognize(png_path)
        write_ocr_artifact(
            artifact_dir,
            engine=engine,
            slide_id=slide_id,
            png_name=png_path.name,
            text=text,
        )


def run_ocr_batch(
    engine: str,
    corpus_dir: Path,
    artifact_dir: Path,
    *,
    runtime: str | None = None,
) -> None:
    runtime_value = runtime or os.environ.get("OCR_RUNTIME", "docker")
    if runtime_value == "docker":
        run_docker_ocr_batch(engine, corpus_dir, artifact_dir)
    elif runtime_value == "local":
        run_local_ocr_batch(engine, corpus_dir, artifact_dir)
    else:
        msg = f"invalid OCR runtime={runtime_value!r}; expected docker or local"
        raise ValueError(msg)
