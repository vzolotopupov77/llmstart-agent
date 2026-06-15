"""Integrity tests for eval dataset manifests (E-15)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.dataset_models import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_V001 = REPO_ROOT / "evals" / "datasets" / "e2e" / "e2e-qa" / "v001_2026-06-14.yaml"
MANIFEST_V002 = REPO_ROOT / "evals" / "datasets" / "e2e" / "e2e-qa" / "v002_2026-06-15.yaml"
V002_CHANGED_IDS = {
    "e2e-qa-0003",
    "e2e-qa-0005",
    "e2e-qa-0011",
    "e2e-qa-0017",
    "e2e-qa-0021",
    "e2e-qa-0023",
    "e2e-qa-0024",
}


def test_e2e_qa_v001_structure() -> None:
    manifest = load_manifest(MANIFEST_V001)
    assert manifest.dataset == "e2e-qa"
    assert manifest.group == "e2e"
    assert manifest.version == "v001"
    assert len(manifest.items) >= 20
    assert len({item.id for item in manifest.items}) == len(manifest.items)


def test_e2e_qa_item_metadata_enums() -> None:
    manifest = load_manifest(MANIFEST_V001)
    for item in manifest.items:
        assert item.metadata.segment in ("b2c", "b2b")
        assert item.metadata.source in ("real_dialog", "synthetic")
        assert item.metadata.gt_quality in ("verified", "approximate")
        assert item.metadata.turn_mode in ("single", "multi")
        assert item.metadata.reviewed_by
        assert item.expected_output.answer_key_points, f"{item.id}: empty answer_key_points"


def test_version_filename_match() -> None:
    load_manifest(MANIFEST_V001)
    load_manifest(MANIFEST_V002)


def test_e2e_qa_v002_same_ids_and_seven_criteria_changes() -> None:
    v1 = load_manifest(MANIFEST_V001)
    v2 = load_manifest(MANIFEST_V002)
    assert v2.version == "v002"
    assert len(v2.items) == len(v1.items) == 26
    ids_v1 = {item.id for item in v1.items}
    ids_v2 = {item.id for item in v2.items}
    assert ids_v1 == ids_v2

    changed = 0
    for a, b in zip(v1.items, v2.items, strict=True):
        assert a.id == b.id
        if a.expected_output.model_dump() != b.expected_output.model_dump():
            changed += 1
            assert a.id in V002_CHANGED_IDS, f"unexpected change: {a.id}"
    assert changed == len(V002_CHANGED_IDS)

    v2_0017 = next(i for i in v2.items if i.id == "e2e-qa-0017")
    assert any("confirm_payment" in r for r in v2_0017.expected_output.must_not)
    v2_0005 = next(i for i in v2.items if i.id == "e2e-qa-0005")
    assert any("vibe-coding-intensive" in kp for kp in v2_0005.expected_output.answer_key_points)


def test_reviewed_by_gate_fails_without_reviewer(tmp_path: Path) -> None:
    """E-13: full validation rejects manifest without reviewed_by."""
    data = yaml.safe_load(MANIFEST_V001.read_text(encoding="utf-8"))
    data["items"][0]["metadata"]["reviewed_by"] = None
    bad_path = tmp_path / "v001_bad.yaml"
    bad_path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match="reviewed_by"):
        load_manifest(bad_path)


def test_all_items_have_reviewed_by() -> None:
    for path in (MANIFEST_V001, MANIFEST_V002):
        manifest = load_manifest(path)
        assert all(item.metadata.reviewed_by for item in manifest.items)
