"""Tests for OCR CER calculation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ocr_cer import compute_cer, normalize_for_cer, score_engine


def test_normalize_lowercase_and_whitespace() -> None:
    assert normalize_for_cer("  Hello   World  ") == "hello world"


def test_normalize_keeps_punctuation_and_percent() -> None:
    assert normalize_for_cer("72% — HR") == "72% — hr"


def test_compute_cer_identical() -> None:
    assert compute_cer("тест", "тест") == 0.0


def test_compute_cer_partial() -> None:
    cer = compute_cer("abc", "abX")
    assert cer == pytest.approx(1 / 3)


def test_compute_cer_can_exceed_one() -> None:
    cer = compute_cer("ab", "abcdefgh")
    assert cer > 1.0


def test_score_engine_with_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "tesseract"
    artifact_dir.mkdir()
    slide_ids = (2, 6, 9, 10, 11, 15, 37, 44, 45, 49)
    for slide_id in slide_ids:
        (artifact_dir / f"slide-{slide_id:02d}.txt").write_text(
            f"# slide-{slide_id:02d}\n# meta\nocr text {slide_id}",
            encoding="utf-8",
        )
    report = score_engine(artifact_dir, engine="tesseract")
    assert report.engine == "tesseract"
    assert len(report.scores) == 10
    assert all(score.cer >= 0.0 for score in report.scores)
