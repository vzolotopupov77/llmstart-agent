"""Build merged item table from two eval runs for error analysis (K-3)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.failure_analysis import analyze_items

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "evals" / "reports" / "runs"
MANIFEST_PATH = REPO_ROOT / "evals" / "datasets" / "e2e" / "e2e-qa" / "v001_2026-06-14.yaml"

DELTA_THRESHOLD = 0.05
FAIL_THRESHOLD = 0.75


@dataclass(frozen=True)
class MergedItem:
    index: int
    item_id: str
    intent: str
    ac_baseline: float
    ac_candidate: float
    delta: float
    faithfulness: float
    task_completion: float
    segment_match: float
    failure_layer: str
    tools: str
    has_retrieval: bool
    input_preview: str
    judge_comment: str
    key_points: list[str]


def _score(item: dict[str, Any], name: str, default: float = 0.0) -> float:
    for score in item.get("scores", []):
        if score.get("name") == name and score.get("value") is not None:
            return float(score["value"])
    return default


def _score_comment(item: dict[str, Any], name: str) -> str:
    for score in item.get("scores", []):
        if score.get("name") == name:
            return str(score.get("comment") or "")
    return ""


def _input_preview(item: dict[str, Any], max_len: int = 100) -> str:
    output = item.get("output") or {}
    if isinstance(output, dict) and output.get("input_text"):
        text = str(output["input_text"])
    else:
        raw = item.get("input")
        if isinstance(raw, str):
            text = raw
        elif isinstance(raw, list):
            parts = [f"{m.get('role')}: {str(m.get('content', ''))[:30]}" for m in raw[:2]]
            text = " | ".join(parts)
        else:
            text = str(raw)
    text = " ".join(text.split())
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _normalize_input_key(raw: Any) -> str:
    if isinstance(raw, str):
        text = raw
    elif isinstance(raw, list):
        parts = [f"{m.get('role', '')}:{m.get('content', '')}" for m in raw]
        text = "\n".join(parts)
    else:
        text = str(raw)
    return " ".join(text.split()).lower()


def _run_input_key(item: dict[str, Any]) -> str:
    output = item.get("output") or {}
    if isinstance(output, dict) and output.get("input_text"):
        return _normalize_input_key(output["input_text"])
    return _normalize_input_key(item.get("input"))


def _manifest_lookup_keys(raw: Any) -> list[str]:
    keys = [_normalize_input_key(raw)]
    if isinstance(raw, list):
        for message in raw:
            if message.get("role") == "user" and message.get("content"):
                keys.append(_normalize_input_key(message["content"]))
    seen: set[str] = set()
    unique: list[str] = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def _run_lookup_keys(item: dict[str, Any]) -> list[str]:
    keys = [_run_input_key(item)]
    output = item.get("output") or {}
    if isinstance(output, dict) and output.get("input_text"):
        text = str(output["input_text"])
        for line in text.splitlines():
            if line.lower().startswith("user:"):
                keys.append(_normalize_input_key(line[5:]))
        if "user:" in text.lower():
            last_user = text.lower().rsplit("user:", maxsplit=1)[-1]
            if "assistant:" in last_user:
                last_user = last_user.split("assistant:")[0]
            keys.append(_normalize_input_key(last_user))
    keys.extend(_manifest_lookup_keys(item.get("input")))
    seen: set[str] = set()
    unique: list[str] = []
    for key in keys:
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def load_manifest_by_input() -> dict[str, dict[str, Any]]:
    if not MANIFEST_PATH.is_file():
        return {}
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_input: dict[str, dict[str, Any]] = {}
    for item in data.get("items", []):
        for key in _manifest_lookup_keys(item["input"]):
            by_input.setdefault(key, item)
    return by_input


def load_manifest_index() -> dict[int, dict[str, Any]]:
    if not MANIFEST_PATH.is_file():
        return {}
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {i: item for i, item in enumerate(data.get("items", []))}


def resolve_manifest_item(
    run_item: dict[str, Any],
    *,
    run_index: int,
    manifest_by_input: dict[str, dict[str, Any]],
    manifest_by_index: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    for key in _run_lookup_keys(run_item):
        if key in manifest_by_input:
            return manifest_by_input[key]
    return manifest_by_index.get(run_index, {})


def load_run(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_runs(
    baseline_path: Path,
    candidate_path: Path,
    *,
    manifest_by_index: dict[int, dict[str, Any]] | None = None,
) -> list[MergedItem]:
    baseline = load_run(baseline_path)
    candidate = load_run(candidate_path)
    b_items = baseline.get("items", [])
    c_items = candidate.get("items", [])
    if len(b_items) != len(c_items):
        msg = f"Item count mismatch: {len(b_items)} vs {len(c_items)}"
        raise ValueError(msg)

    if manifest_by_index is None:
        manifest_by_index = load_manifest_index()
    manifest_by_input = load_manifest_by_input()
    analyzed = {a.index: a for a in analyze_items(c_items)}
    merged: list[MergedItem] = []

    for i, (b, c) in enumerate(zip(b_items, c_items, strict=True)):
        manifest = resolve_manifest_item(
            c,
            run_index=i,
            manifest_by_input=manifest_by_input,
            manifest_by_index=manifest_by_index,
        )
        item_id = str(
            c.get("dataset_item_id") or c.get("item_id") or manifest.get("id") or f"idx-{i}"
        )
        intent = str((manifest.get("metadata") or {}).get("intent") or "—")
        expected = manifest.get("expected_output") or {}
        key_points = list(expected.get("answer_key_points") or [])

        out = c.get("output") or {}
        tools_raw = out.get("tools") or [] if isinstance(out, dict) else []
        tool_names = [t.get("name", "") for t in tools_raw if isinstance(t, dict) and t.get("name")]
        retrieval_ctx = out.get("retrieval_context") if isinstance(out, dict) else None

        ac_b = _score(b, "answer_correctness")
        ac_c = _score(c, "answer_correctness")
        analysis = analyzed[i]

        merged.append(
            MergedItem(
                index=i,
                item_id=item_id,
                intent=intent,
                ac_baseline=ac_b,
                ac_candidate=ac_c,
                delta=ac_c - ac_b,
                faithfulness=analysis.faithfulness,
                task_completion=analysis.task_completion,
                segment_match=analysis.segment_match,
                failure_layer=analysis.failure_layer,
                tools=", ".join(tool_names) or "—",
                has_retrieval=bool(retrieval_ctx),
                input_preview=_input_preview(c),
                judge_comment=_score_comment(c, "answer_correctness")[:200],
                key_points=key_points,
            )
        )
    return merged


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def build_open_coding_table(items: list[MergedItem]) -> str:
    lines = [
        "| idx | item_id | intent | AC base | AC cand | Δ | layer | tools | rc | input |",
        "|----:|---------|--------|--------:|--------:|--:|-------|-------|:--:|-------|",
    ]
    for it in items:
        lines.append(
            f"| {it.index} | `{it.item_id}` | {it.intent} | {it.ac_baseline:.2f} | "
            f"{it.ac_candidate:.2f} | {it.delta:+.2f} | {it.failure_layer} | "
            f"{it.tools} | {'Y' if it.has_retrieval else 'N'} | "
            f"{_md_escape(it.input_preview)} |"
        )
    return "\n".join(lines)


def build_fail_subset_markdown(items: list[MergedItem]) -> str:
    failing = [it for it in items if it.ac_candidate < FAIL_THRESHOLD]
    lines = [
        f"**Items с AC < {FAIL_THRESHOLD} на candidate:** {len(failing)}/26",
        "",
        "| idx | item_id | intent | AC | category (TBD) | open note |",
        "|----:|---------|--------|---:|----------------|-----------|",
    ]
    for it in sorted(failing, key=lambda x: x.ac_candidate):
        lines.append(f"| {it.index} | `{it.item_id}` | {it.intent} | {it.ac_candidate:.2f} | | |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge two eval runs for error analysis")
    parser.add_argument("--baseline", required=True, help="Baseline run name (no .json)")
    parser.add_argument("--candidate", required=True, help="Candidate run name (no .json)")
    parser.add_argument(
        "--out",
        default="reports/error-analysis-open-coding.md",
        help="Output markdown path relative to evals/",
    )
    args = parser.parse_args()

    baseline_path = RUNS_DIR / f"{args.baseline}.json"
    candidate_path = RUNS_DIR / f"{args.candidate}.json"
    if not baseline_path.is_file() or not candidate_path.is_file():
        print("build_error_analysis: run JSON not found", file=sys.stderr)
        return 1

    manifest = load_manifest_index()
    merged = merge_runs(baseline_path, candidate_path, manifest_by_index=manifest)

    improved = sum(1 for it in merged if it.delta >= DELTA_THRESHOLD)
    regressed = sum(1 for it in merged if it.delta <= -DELTA_THRESHOLD)
    failing = sum(1 for it in merged if it.ac_candidate < FAIL_THRESHOLD)

    body = "\n".join(
        [
            "# Open coding table (generated)",
            "",
            f"- Baseline: `{args.baseline}`",
            f"- Candidate: `{args.candidate}`",
            f"- Failing (AC<{FAIL_THRESHOLD}): **{failing}**",
            f"- Improved Δ≥{DELTA_THRESHOLD}: **{improved}** · Regressed: **{regressed}**",
            "",
            build_open_coding_table(merged),
            "",
            build_fail_subset_markdown(merged),
            "",
        ]
    )

    out_path = REPO_ROOT / "evals" / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
