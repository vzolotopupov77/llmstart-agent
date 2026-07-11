"""Hallucination check for VLM captions on S2 chart slides."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from indexers.caption.pricing import model_slug
from indexers.config import EVALS_ROOT, REPO_ROOT
from scripts.multimodal_retrieval import strip_corpus_header

MANIFEST_PATH = (
    EVALS_ROOT / "datasets" / "multimodal" / "caption-hallucination" / "v001_2026-07-10.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "evals" / "artifacts" / "captions" / "hallucination-check.md"

MODEL_ARTIFACT_DIRS: dict[str, Path] = {
    "nemotron": EVALS_ROOT / "artifacts" / "captions" / "nemotron-nano-12b-v2-vl",
    "gemini": EVALS_ROOT / "artifacts" / "captions" / "gemini-2.5-flash-lite",
}


@dataclass(frozen=True)
class NumberCheck:
    value: str
    label: str
    found: bool
    matched_text: str | None
    note: str | None = None


@dataclass(frozen=True)
class SlideCheck:
    slide_id: int
    segment: str
    model_key: str
    model_id: str
    verdict: str
    numbers: list[NumberCheck]
    silent_fixes: list[str]


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_number(text: str) -> str:
    return text.replace("−", "-").replace("–", "-").replace("—", "-").strip().lower()


def _extract_percentages(body: str) -> set[str]:
    found: set[str] = set()
    for match in re.finditer(r"-?\d+(?:[.,]\d+)?(?:\s*[-–—]\s*\d+(?:[.,]\d+)?)?\s*%", body):
        found.add(_normalize_number(match.group(0)))
    return found


def _number_present(
    body: str, expected: str, alternatives: list[str] | None = None
) -> tuple[bool, str | None]:
    norm_body = _normalize_number(body)
    candidates = [_normalize_number(expected)]
    if alternatives:
        candidates.extend(_normalize_number(alt) for alt in alternatives)

    for candidate in candidates:
        if candidate in norm_body:
            return True, candidate
        # Allow minor spacing variants like "72 %" vs "72%"
        compact = candidate.replace(" ", "")
        if compact in norm_body.replace(" ", ""):
            return True, candidate

    # Check extracted percentages for close matches (silent fix detection)
    extracted = _extract_percentages(body)
    expected_norm = _normalize_number(expected)
    for pct in extracted:
        if expected_norm.replace(" ", "") == pct.replace(" ", ""):
            return True, pct
        # Silent fix: 39% expected but 40% found
        if expected_norm.endswith("%") and pct.endswith("%"):
            try:
                exp_val = float(expected_norm.rstrip("%").replace(",", "."))
                found_val = float(pct.rstrip("%").replace(",", "."))
                if abs(exp_val - found_val) == 1.0:
                    return False, pct
            except ValueError:
                pass

    return False, None


def _detect_silent_fixes(body: str, key_numbers: list[dict]) -> list[str]:
    fixes: list[str] = []
    extracted = _extract_percentages(body)
    for entry in key_numbers:
        expected = _normalize_number(entry["value"])
        if not expected.endswith("%"):
            continue
        try:
            exp_val = float(expected.rstrip("%").replace(",", "."))
        except ValueError:
            continue
        for pct in extracted:
            try:
                found_val = float(pct.rstrip("%").replace(",", "."))
            except ValueError:
                continue
            if abs(exp_val - found_val) == 1.0 and expected.replace(" ", "") not in body.replace(
                " ", ""
            ):
                fixes.append(f"{entry['value']} → {pct} ({entry.get('label', '')})")
    return fixes


def check_slide(
    *,
    slide_id: int,
    segment: str,
    model_key: str,
    model_id: str,
    artifact_dir: Path,
    key_numbers: list[dict],
) -> SlideCheck:
    artifact_path = artifact_dir / f"slide-{slide_id:02d}.txt"
    if not artifact_path.exists():
        msg = f"Missing artifact: {artifact_path}"
        raise FileNotFoundError(msg)

    body = strip_corpus_header(artifact_path.read_text(encoding="utf-8"))
    numbers: list[NumberCheck] = []
    missing: list[str] = []

    for entry in key_numbers:
        found, matched = _number_present(
            body,
            entry["value"],
            alternatives=entry.get("alternatives"),
        )
        note = None
        if not found and matched:
            note = f"возможная молчаливая правка: ожидалось {entry['value']}, в тексте {matched}"
            missing.append(entry["value"])
        elif not found:
            missing.append(entry["value"])
        numbers.append(
            NumberCheck(
                value=entry["value"],
                label=entry.get("label", ""),
                found=found,
                matched_text=matched,
                note=note,
            ),
        )

    silent_fixes = _detect_silent_fixes(body, key_numbers)
    if missing:
        verdict = "расхождение"
        if silent_fixes:
            verdict = "расхождение (молчаливая правка чисел)"
    else:
        verdict = "совпадает"

    return SlideCheck(
        slide_id=slide_id,
        segment=segment,
        model_key=model_key,
        model_id=model_id,
        verdict=verdict,
        numbers=numbers,
        silent_fixes=silent_fixes,
    )


def run_checks(
    artifact_dirs: dict[str, Path] | None = None,
    manifest_path: Path = MANIFEST_PATH,
) -> list[SlideCheck]:
    manifest = load_manifest(manifest_path)
    dirs = artifact_dirs or MODEL_ARTIFACT_DIRS
    results: list[SlideCheck] = []

    for slide_entry in manifest["slides"]:
        slide_id = int(slide_entry["slide_id"])
        segment = slide_entry["segment"]
        key_numbers = slide_entry["key_numbers"]

        for model_key, artifact_dir in dirs.items():
            model_id = model_slug(
                "nvidia/nemotron-nano-12b-v2-vl:free"
                if model_key == "nemotron"
                else "google/gemini-2.5-flash-lite",
            )
            results.append(
                check_slide(
                    slide_id=slide_id,
                    segment=segment,
                    model_key=model_key,
                    model_id=model_id,
                    artifact_dir=artifact_dir,
                    key_numbers=key_numbers,
                ),
            )

    return results


def write_hallucination_report(
    path: Path,
    checks: list[SlideCheck],
    *,
    timestamp: str,
) -> None:
    lines = [
        "# VLM Caption — Hallucination Check (S2 slides 10–11)",
        "",
        f"> **Дата:** {timestamp[:10]}",
        "> **Manifest:** `evals/datasets/multimodal/caption-hallucination/v001_2026-07-10.json`",
        "",
        "Проверка ключевых чисел на chart-слайдах. Эталон — PNG-verified refs из OCR golden-set.",
        "",
        "## Сводка",
        "",
        "| Слайд | Модель | Вердикт | Пропущено/искажено |",
        "|---:|---|---|---|",
    ]

    for check in checks:
        missing = [n.value for n in check.numbers if not n.found]
        missing_cell = ", ".join(missing) if missing else "—"
        lines.append(
            f"| {check.slide_id} | {check.model_key} | **{check.verdict}** | {missing_cell} |",
        )

    lines.extend(["", "## Детали по числам", ""])

    for check in checks:
        lines.append(f"### Слайд {check.slide_id} — {check.model_key} (`{check.model_id}`)")
        lines.append("")
        lines.append(f"**Вердикт:** {check.verdict}")
        lines.append("")
        lines.append("| Число | Метка | Найдено | Примечание |")
        lines.append("|---|---|:---:|---|")
        for num in check.numbers:
            found_cell = "да" if num.found else "нет"
            note = num.note or (num.matched_text or "—")
            lines.append(f"| {num.value} | {num.label} | {found_cell} | {note} |")
        if check.silent_fixes:
            lines.append("")
            lines.append("**Молчалые правки:** " + "; ".join(check.silent_fixes))
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    from datetime import UTC, datetime

    parser = argparse.ArgumentParser(description="VLM caption hallucination check")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    checks = run_checks()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_hallucination_report(args.output, checks, timestamp=timestamp)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
