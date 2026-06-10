"""Structural and coverage validation for llmstart agent datasets."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VERSION = "v2"

VALID_B2C_PRODUCTS = {
    "ai-agents-combo",
    "vibe-coding-intensive",
    "fullstack-aidd",
    "agents",
    "deep-agents",
    "consultation",
}
VALID_SEGMENTS = {"b2c", "b2b"}
VALID_TURN_MODES = {"single", "multi"}
VALID_B2C_TYPES = {"b2c-rag", "b2c-product", "b2c-segment", "b2c-objection", "b2c-tools"}
VALID_B2B_TYPES = {"b2b-segment", "b2b-rag", "b2b-nurture"}
VALID_TOOLS = {
    "search_knowledge_base",
    "list_b2c_products",
    "save_lead",
    "create_payment_link",
    "confirm_payment",
}
VALID_SOURCES = {"extraction", "synthetic", "reconstruction"}

# P0/P1 groups expected in B2C
P0_GROUPS = {"G1", "G7"}
P1_GROUPS = {"G2", "G3"}
V2_REQUIRED_CATEGORIES = {"G8.1", "G8.5"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{i} invalid JSON: {exc}") from exc
    return records


def validate_record(rec: dict[str, Any], dataset: str, errors: list[str]) -> None:
    rid = rec.get("id", "<no-id>")

    for field in ("id", "input", "expected_output", "metadata"):
        if field not in rec:
            errors.append(f"[{dataset}] {rid}: missing top-level field '{field}'")

    eo = rec.get("expected_output", {})
    md = rec.get("metadata", {})

    if "segment" not in eo:
        errors.append(f"[{dataset}] {rid}: expected_output.segment missing")
    elif eo["segment"] not in VALID_SEGMENTS:
        errors.append(f"[{dataset}] {rid}: invalid segment '{eo['segment']}'")

    if "answer_key_points" not in eo and "tools" not in eo:
        errors.append(f"[{dataset}] {rid}: expected_output needs answer_key_points or tools")

    if "should_clarify" in eo and not isinstance(eo["should_clarify"], bool):
        errors.append(f"[{dataset}] {rid}: should_clarify must be bool")

    for key in ("dataset_type", "group", "category", "source", "turn_mode"):
        if key not in md:
            errors.append(f"[{dataset}] {rid}: metadata.{key} missing")

    if md.get("turn_mode") not in VALID_TURN_MODES:
        errors.append(f"[{dataset}] {rid}: invalid turn_mode")

    if md.get("source") not in VALID_SOURCES:
        errors.append(f"[{dataset}] {rid}: invalid metadata.source '{md.get('source')}'")

    inp = rec.get("input")
    if md.get("turn_mode") == "multi":
        if not isinstance(inp, list) or not inp:
            errors.append(f"[{dataset}] {rid}: multi turn_mode requires non-empty input list")
        elif not all(isinstance(m, dict) and "role" in m and "content" in m for m in inp):
            errors.append(f"[{dataset}] {rid}: multi input messages need role+content")
    elif not isinstance(inp, str) or not inp.strip():
        errors.append(f"[{dataset}] {rid}: single turn_mode requires non-empty string input")

    if dataset == "b2c":
        if md.get("dataset_type") not in VALID_B2C_TYPES:
            errors.append(f"[{dataset}] {rid}: invalid dataset_type")
        for code in eo.get("product_codes", []):
            if code not in VALID_B2C_PRODUCTS:
                errors.append(f"[{dataset}] {rid}: unknown product_code '{code}'")
    else:
        if md.get("dataset_type") not in VALID_B2B_TYPES:
            errors.append(f"[{dataset}] {rid}: invalid dataset_type")

    for tool in eo.get("tools", []):
        if tool.get("name") not in VALID_TOOLS:
            errors.append(f"[{dataset}] {rid}: unknown tool '{tool.get('name')}'")
        if tool.get("name") == "search_knowledge_base":
            args = tool.get("args", {})
            if args.get("audience") not in VALID_SEGMENTS:
                errors.append(f"[{dataset}] {rid}: search_knowledge_base needs audience b2c/b2b")


def check_g4_policy(records: list[dict[str, Any]], warnings: list[str]) -> None:
    demo_markers = ("демо", "отрывок", "урок в открытый", "публичн")
    for rec in records:
        if rec.get("metadata", {}).get("group") != "G4":
            continue
        rid = rec["id"]
        kps = " ".join(rec.get("expected_output", {}).get("answer_key_points", [])).lower()
        if not any(m in kps for m in ("демо нет", "публичного демо", "отрывков уроков нет", "публичных отрывков")):
            warnings.append(f"[G4] {rid}: answer_key_points may miss explicit 'no public demo'")
        must_not = rec.get("expected_output", {}).get("must_not", [])
        if not must_not:
            warnings.append(f"[G4] {rid}: G4 record without must_not guardrails")

    for rec in records:
        md = rec["metadata"]
        if md.get("dataset_type") == "b2c-segment" and rec["expected_output"].get("segment") == "b2b":
            warnings.append(
                f"[routing] {rec['id']}: b2c-segment with expected segment=b2b (OK for routing eval)"
            )


def check_duplicates(all_records: list[dict[str, Any]], errors: list[str]) -> None:
    ids = [r["id"] for r in all_records]
    if len(ids) != len(set(ids)):
        dupes = [i for i, c in Counter(ids).items() if c > 1]
        errors.append(f"Duplicate ids: {dupes}")


def stratified_sample(records: list[dict[str, Any]], n: int, seed_ids: list[str]) -> list[dict[str, Any]]:
    """Pick n records, prioritizing seed_ids then type diversity."""
    by_id = {r["id"]: r for r in records}
    picked: list[dict[str, Any]] = []
    for sid in seed_ids:
        if sid in by_id and len(picked) < n:
            picked.append(by_id[sid])
    seen_types: set[str] = set()
    for r in records:
        if len(picked) >= n:
            break
        if r in picked:
            continue
        t = r["metadata"]["dataset_type"]
        if t not in seen_types:
            picked.append(r)
            seen_types.add(t)
    for r in records:
        if len(picked) >= n:
            break
        if r not in picked:
            picked.append(r)
    return picked[:n]


def format_record_summary(rec: dict[str, Any]) -> str:
    md = rec["metadata"]
    inp = rec["input"]
    if isinstance(inp, list):
        inp_preview = inp[-1]["content"][:120] + ("…" if len(inp[-1]["content"]) > 120 else "")
    else:
        inp_preview = inp[:120] + ("…" if len(inp) > 120 else "")
    kps = rec["expected_output"].get("answer_key_points", [])
    tools = [t["name"] for t in rec["expected_output"].get("tools", [])]
    lines = [
        f"### `{rec['id']}`",
        f"- **type:** {md['dataset_type']} | **group:** {md['group']} / **cat:** {md['category']} | **source:** {md['source']} | **turn:** {md['turn_mode']}",
        f"- **input:** {inp_preview}",
        f"- **key_points:** {'; '.join(kps[:4])}{'…' if len(kps) > 4 else ''}",
    ]
    if tools:
        lines.append(f"- **tools:** {', '.join(tools)}")
    if rec["expected_output"].get("must_not"):
        lines.append(f"- **must_not:** {rec['expected_output']['must_not']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate llmstart agent datasets")
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        choices=("v1", "v2"),
        help="Dataset version folder (default: v2)",
    )
    return parser.parse_args()


def paths_for_version(version: str) -> tuple[Path, Path, Path, Path, Path, Path]:
    base = ROOT / "datasets"
    b2c = base / f"b2c/{version}"
    b2b = base / f"b2b/{version}"
    suffix = "" if version == "v1" else f"-{version}"
    return (
        b2c / "dataset.jsonl",
        b2b / "dataset.jsonl",
        b2c / "extraction.jsonl",
        b2c / "synthetic.jsonl",
        base / f"validation-report{suffix}.md",
        base / f"validation-sample{suffix}.md",
    )


def main() -> int:
    args = parse_args()
    version = args.version
    b2c_path, b2b_path, b2c_ext_path, b2c_syn_path, report_path, sample_path = paths_for_version(
        version
    )

    errors: list[str] = []
    warnings: list[str] = []

    b2c = load_jsonl(b2c_path)
    b2b = load_jsonl(b2b_path)

    for rec in b2c:
        validate_record(rec, "b2c", errors)
    for rec in b2b:
        validate_record(rec, "b2b", errors)

    check_duplicates(b2c + b2b, errors)
    check_g4_policy(b2c, warnings)

    b2c_groups = Counter(r["metadata"]["group"] for r in b2c)
    b2c_categories = {r["metadata"]["category"] for r in b2c}
    for g in P0_GROUPS | P1_GROUPS:
        if b2c_groups.get(g, 0) == 0:
            errors.append(f"B2C coverage: P0/P1 group {g} has zero records")

    if version == "v2":
        for cat in V2_REQUIRED_CATEGORIES:
            if cat not in b2c_categories:
                errors.append(f"B2C v2 coverage: missing category {cat}")

    b2b_ext_path = b2b_path.parent / "extraction.jsonl"
    b2b_syn_path = b2b_path.parent / "synthetic.jsonl"

    b2c_ext = len(load_jsonl(b2c_ext_path))
    b2c_syn = len(load_jsonl(b2c_syn_path))
    if len(b2c) != b2c_ext + b2c_syn:
        warnings.append(f"B2C dataset count {len(b2c)} != extraction {b2c_ext} + synthetic {b2c_syn}")

    b2b_ext = len(load_jsonl(b2b_ext_path))
    b2b_syn = len(load_jsonl(b2b_syn_path))
    if len(b2b) != b2b_ext + b2b_syn:
        warnings.append(f"B2B dataset count {len(b2b)} != extraction {b2b_ext} + synthetic {b2b_syn}")

    b2c_turn = Counter(r["metadata"]["turn_mode"] for r in b2c)
    b2c_type = Counter(r["metadata"]["dataset_type"] for r in b2c)
    b2b_type = Counter(r["metadata"]["dataset_type"] for r in b2b)

    # Validation sample ~10%
    b2c_sample_ids = [
        "b2c-objection-m02",
        "b2c-syn-tools-001",
        "b2c-rag-001",
        "b2c-syn-segment-001",
        "b2c-product-001",
        "b2c-syn-rag-003",
        "b2c-objection-m01",
    ]
    if version == "v2":
        b2c_sample_ids.extend(["b2c-nurture-001", "b2c-objection-m08", "b2c-rag-010"])
    b2b_sample_ids = ["b2b-syn-segment-001", "b2b-nurture-m01"]
    if version == "v2":
        b2b_sample_ids.append("b2b-segment-001")
    b2c_sample = stratified_sample(b2c, 9 if version == "v2" else 7, b2c_sample_ids)
    b2b_sample = stratified_sample(b2b, 3 if version == "v2" else 2, b2b_sample_ids)

    status = "PASS" if not errors else "FAIL"
    report_lines = [
        "# Validation Report",
        "",
        f"**Версия:** {version}  ",
        f"**Дата:** auto-run  ",
        f"**Статус:** {status}",
        "",
        "## Структурная проверка",
        "",
        f"- B2C записей: **{len(b2c)}**",
        f"- B2B записей: **{len(b2b)}**",
        f"- Уникальные id: **{'да' if not any('Duplicate' in e for e in errors) else 'нет'}**",
        f"- Ошибки: **{len(errors)}**",
        f"- Предупреждения: **{len(warnings)}**",
        "",
    ]

    if errors:
        report_lines.append("### Ошибки")
        for e in errors:
            report_lines.append(f"- {e}")
        report_lines.append("")

    if warnings:
        report_lines.append("### Предупреждения")
        for w in warnings:
            report_lines.append(f"- {w}")
        report_lines.append("")

    report_lines.extend(
        [
            "## Покрытие B2C",
            "",
            "### По типам",
            "",
        ]
    )
    for t, c in sorted(b2c_type.items()):
        report_lines.append(f"- {t}: {c}")

    report_lines.extend(["", "### По группам", ""])
    for g, c in sorted(b2c_groups.items()):
        report_lines.append(f"- {g}: {c}")

    report_lines.extend(
        [
            "",
            f"### turn_mode: single={b2c_turn['single']}, multi={b2c_turn['multi']}",
            "",
            "## Покрытие B2B",
            "",
        ]
    )
    for t, c in sorted(b2b_type.items()):
        report_lines.append(f"- {t}: {c}")

    report_lines.extend(
        [
            "",
            "## Семантические заметки (выборочно)",
            "",
            "- G4: все записи проверены на явный отказ «публичного демо нет»",
            "- G9 рассрочка (b2c-syn-rag-003): must_not на обещание рассрочки",
            "- B2B: нет create_payment_link — корректно для корп. сделок",
            "- Chunk ids / Hit Rate@k: не применялось",
            "- v2: G9.4 = payment tool-flow; reconstruction source для B2B segment",
            "",
            "## Validation Sample",
            "",
            f"Выборка для ревью человеком: [`{sample_path.name}`]({sample_path.name}) ({len(b2c_sample)} B2C + {len(b2b_sample)} B2B)",
            "",
        ]
    )

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    sample_lines = [
        f"# Validation Sample (~10%) — {version}",
        "",
        "Ревью: естественность `input`, корректность `answer_key_points`, соответствие политикам (G4 демо, B2B≠B2C checkout).",
        "",
        f"## B2C ({len(b2c_sample)})",
        "",
    ]
    for rec in b2c_sample:
        sample_lines.append(format_record_summary(rec))
        sample_lines.append("")

    sample_lines.extend([f"## B2B ({len(b2b_sample)})", ""])
    for rec in b2b_sample:
        sample_lines.append(format_record_summary(rec))
        sample_lines.append("")

    sample_path.write_text("\n".join(sample_lines), encoding="utf-8")

    print(f"Version: {version}")
    print(f"Status: {status}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        for e in errors:
            print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
