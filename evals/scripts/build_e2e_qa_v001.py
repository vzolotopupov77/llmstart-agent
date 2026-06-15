"""One-off builder: legacy b2c/v2 items -> e2e-qa v001 manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_PATH = REPO_ROOT / "datasets" / "b2c" / "v2" / "dataset.jsonl"
OUT_PATH = REPO_ROOT / "evals" / "datasets" / "e2e" / "e2e-qa" / "v001_2026-06-14.yaml"
REVIEWED_BY = "product-owner"

SELECTED_LEGACY_IDS = [
    "b2c-rag-001",
    "b2c-rag-002",
    "b2c-rag-003",
    "b2c-rag-006",
    "b2c-product-001",
    "b2c-product-003",
    "b2c-product-004",
    "b2c-objection-001",
    "b2c-objection-004",
    "b2c-objection-m02",
    "b2c-objection-m03",
    "b2c-product-002",
    "b2c-rag-010",
    "b2c-segment-001",
    "b2c-segment-002",
    "b2c-syn-tools-001",
    "b2c-syn-tools-002",
    "b2c-syn-rag-001",
    "b2c-syn-product-001",
    "b2c-syn-segment-001",
    "b2c-syn-objection-001",
    "b2c-syn-rag-003",
    "b2c-objection-m01",
    "b2c-objection-m04",
    "b2c-objection-m05",
    "b2c-syn-tools-m01",
]


def _load_legacy() -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for line in LEGACY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        by_id[record["id"]] = record
    return by_id


def _gt_quality(meta: dict[str, Any]) -> str:
    if meta.get("kb_verified"):
        return "verified"
    if meta.get("source") == "synthetic" and meta.get("dataset_type") == "b2c-tools":
        return "verified"
    return "approximate"


def _to_manifest_item(index: int, legacy: dict[str, Any]) -> dict[str, Any]:
    meta = legacy["metadata"]
    exp = legacy["expected_output"]
    expected: dict[str, Any] = {
        "segment": exp.get("segment"),
        "product_codes": exp.get("product_codes", []),
        "answer_key_points": exp.get("answer_key_points", []),
    }
    if "should_clarify" in exp:
        expected["should_clarify"] = exp["should_clarify"]
    if exp.get("acceptable_clarifications"):
        expected["acceptable_clarifications"] = exp["acceptable_clarifications"]
    if exp.get("must_not"):
        expected["must_not"] = exp["must_not"]
    if exp.get("tools"):
        expected["tools"] = exp["tools"]

    source = "real_dialog" if meta.get("source") == "extraction" else "synthetic"
    return {
        "id": f"e2e-qa-{index:04d}",
        "input": legacy["input"],
        "expected_output": expected,
        "metadata": {
            "segment": exp.get("segment", "b2c"),
            "intent": meta.get("category") or meta.get("group", "unknown"),
            "source": source,
            "source_chat": meta.get("source_chat"),
            "turn_mode": meta.get("turn_mode", "single"),
            "gt_quality": _gt_quality(meta),
            "reviewed_by": REVIEWED_BY,
            "difficulty": meta.get("difficulty"),
            "legacy_id": legacy["id"],
        },
    }


def main() -> None:
    legacy_by_id = _load_legacy()
    missing = [item_id for item_id in SELECTED_LEGACY_IDS if item_id not in legacy_by_id]
    if missing:
        msg = f"missing legacy ids: {missing}"
        raise SystemExit(msg)

    items = [
        _to_manifest_item(index + 1, legacy_by_id[legacy_id])
        for index, legacy_id in enumerate(SELECTED_LEGACY_IDS)
    ]

    manifest = {
        "dataset": "e2e-qa",
        "group": "e2e",
        "version": "v001",
        "created": "2026-06-14",
        "description": (
            "End-to-end pre-purchase QA: RAG, product, segment, objections (vertical slice)"
        ),
        "items": items,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.dump(
        manifest,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )
    OUT_PATH.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote {len(items)} items to {OUT_PATH}")


if __name__ == "__main__":
    main()
