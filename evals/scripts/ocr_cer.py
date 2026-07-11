"""Character Error Rate for OCR ingestion-quality diagnostics."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from indexers.config import REPO_ROOT
from scripts.multimodal_retrieval import strip_corpus_header

DEFAULT_GOLDEN_MANIFEST = (
    REPO_ROOT / "evals/datasets/multimodal/ocr-cer-golden/v001_2026-07-05.json"
)

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_for_cer(text: str) -> str:
    """Lowercase and collapse whitespace; keep punctuation and %."""
    collapsed = _WHITESPACE_RE.sub(" ", text.strip().lower())
    return collapsed


def compute_cer(ref: str, hyp: str) -> float:
    """CER = Levenshtein(ref, hyp) / len(ref); no clamp when hyp is longer."""
    ref_norm = normalize_for_cer(ref)
    hyp_norm = normalize_for_cer(hyp)
    if not ref_norm:
        return 0.0 if not hyp_norm else float("inf")
    distance = Levenshtein.distance(ref_norm, hyp_norm)
    return distance / len(ref_norm)


@dataclass(frozen=True)
class CerSlideScore:
    slide_id: int
    segment: str
    cer: float
    ref_chars: int
    hyp_chars: int


@dataclass(frozen=True)
class CerEngineReport:
    engine: str
    scores: tuple[CerSlideScore, ...]

    @property
    def mean_cer(self) -> float:
        if not self.scores:
            return 0.0
        return sum(score.cer for score in self.scores) / len(self.scores)

    @property
    def median_cer(self) -> float:
        if not self.scores:
            return 0.0
        values = sorted(score.cer for score in self.scores)
        mid = len(values) // 2
        if len(values) % 2:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2


def load_golden_manifest(path: Path | None = None) -> dict[str, object]:
    manifest_path = path or DEFAULT_GOLDEN_MANIFEST
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def read_hypothesis(artifact_dir: Path, slide_id: int) -> str:
    artifact_path = artifact_dir / f"slide-{slide_id:02d}.txt"
    if not artifact_path.is_file():
        msg = f"OCR artifact missing: {artifact_path}"
        raise FileNotFoundError(msg)
    body = artifact_path.read_text(encoding="utf-8")
    return strip_corpus_header(body)


def score_engine(
    artifact_dir: Path,
    *,
    engine: str,
    manifest_path: Path | None = None,
) -> CerEngineReport:
    manifest = load_golden_manifest(manifest_path)
    golden_root = (manifest_path or DEFAULT_GOLDEN_MANIFEST).parent
    slides = manifest["slides"]
    scores: list[CerSlideScore] = []

    for entry in slides:
        slide_id = int(entry["slide_id"])
        segment = str(entry["segment"])
        ref_file = golden_root / str(entry["ref_file"])
        ref_text = ref_file.read_text(encoding="utf-8")
        hyp_text = read_hypothesis(artifact_dir, slide_id)
        ref_norm = normalize_for_cer(ref_text)
        hyp_norm = normalize_for_cer(hyp_text)
        scores.append(
            CerSlideScore(
                slide_id=slide_id,
                segment=segment,
                cer=compute_cer(ref_text, hyp_text),
                ref_chars=len(ref_norm),
                hyp_chars=len(hyp_norm),
            ),
        )

    return CerEngineReport(engine=engine, scores=tuple(scores))
