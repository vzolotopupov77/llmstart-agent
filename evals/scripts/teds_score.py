"""Tree Edit Distance based Similarity for chart slide structure (Task 07)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from indexers.config import REPO_ROOT

DEFAULT_GOLDEN_MANIFEST = REPO_ROOT / "evals/datasets/multimodal/teds-golden/v001_2026-07-11.json"


@dataclass(frozen=True)
class TedSlideScore:
    slide_id: int
    segment: str
    teds: float


@dataclass(frozen=True)
class TedReport:
    scores: tuple[TedSlideScore, ...]

    @property
    def mean_teds(self) -> float:
        if not self.scores:
            return 0.0
        return sum(score.teds for score in self.scores) / len(self.scores)


def load_golden_manifest(path: Path | None = None) -> dict[str, object]:
    manifest_path = path or DEFAULT_GOLDEN_MANIFEST
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _compute_teds(ref_html: str, hyp_html: str) -> float:
    from table_recognition_metric import TEDS  # noqa: PLC0415

    metric = TEDS(structure_only=False)
    return float(metric(ref_html, hyp_html))


def score_teds(
    hyp_dir: Path,
    *,
    manifest_path: Path | None = None,
) -> TedReport:
    manifest = load_golden_manifest(manifest_path)
    golden_root = (manifest_path or DEFAULT_GOLDEN_MANIFEST).parent
    slides = manifest.get("slides")
    if not isinstance(slides, list):
        msg = "TEDS manifest missing slides array"
        raise ValueError(msg)

    scores: list[TedSlideScore] = []
    for entry in slides:
        if not isinstance(entry, dict):
            continue
        slide_id = int(entry["slide_id"])
        segment = str(entry.get("segment", ""))
        ref_file = str(entry["ref_file"])
        ref_path = golden_root / ref_file
        hyp_path = hyp_dir / f"slide-{slide_id:02d}.html"
        if not ref_path.is_file():
            msg = f"TEDS reference missing: {ref_path}"
            raise FileNotFoundError(msg)
        if not hyp_path.is_file():
            msg = f"TEDS hypothesis missing: {hyp_path}"
            raise FileNotFoundError(msg)
        ref_html = ref_path.read_text(encoding="utf-8")
        hyp_html = hyp_path.read_text(encoding="utf-8")
        teds = _compute_teds(ref_html, hyp_html)
        scores.append(TedSlideScore(slide_id=slide_id, segment=segment, teds=teds))

    return TedReport(scores=tuple(scores))
