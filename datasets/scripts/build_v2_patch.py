"""Build datasets v2 from v1 with reviewer corrections (immutable v1 preserved)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "datasets"
V2 = ROOT / "datasets"

MULTI_TURN_EXTRACTION = {
    "b2c-objection-m01",
    "b2c-objection-m02",
    "b2c-objection-m03",
    "b2c-objection-m04",
    "b2c-objection-m05",
    "b2c-objection-m06",
    "b2c-objection-m07",
    "b2b-nurture-m01",
}

TOOL_PAYMENT_IDS = {
    "b2c-syn-tools-001",
    "b2c-syn-tools-002",
    "b2c-syn-tools-m01",
    "b2c-syn-tools-004",
    "b2c-syn-tools-005",
    "b2c-syn-tools-m03",
}

B2B_RECONSTRUCTION_IDS = {"b2b-segment-001", "b2b-segment-002"}

PERSONA_BY_ID: dict[str, str] = {
    "b2c-syn-rag-002": "hr-ld",
    "b2c-syn-segment-002": "working-dev",
    "b2c-syn-rag-004": "junior-dev",
    "b2c-syn-rag-005": "working-dev",
    "b2c-syn-rag-006": "senior-dev",
    "b2c-syn-product-003": "junior-dev",
    "b2c-syn-product-004": "founder",
    "b2c-syn-product-005": "price-sensitive",
    "b2c-syn-segment-004": "working-dev",
    "b2c-syn-objection-002": "cpo",
    "b2c-syn-objection-003": "working-dev",
    "b2c-syn-objection-004": "senior-dev",
    "b2c-syn-tools-001": "working-dev",
    "b2c-syn-tools-002": "working-dev",
    "b2c-syn-tools-004": "founder",
    "b2c-syn-tools-005": "working-dev",
    "b2c-syn-tools-007": "junior-dev",
    "b2c-syn-rag-008": "senior-dev",
    "b2c-syn-rag-009": "senior-skeptic",
    "b2c-syn-segment-005": "team-lead",
    "b2c-syn-tools-008": "junior-dev",
    "b2c-syn-objection-m03": "working-dev",
    "b2c-syn-objection-m04": "price-sensitive",
    "b2c-syn-rag-m01": "junior-dev",
    "b2c-syn-product-m01": "founder",
    "b2c-syn-tools-m01": "working-dev",
    "b2c-syn-tools-m02": "working-dev",
    "b2c-syn-tools-m03": "working-dev",
    "b2b-syn-rag-002": "platform-lead",
    "b2b-syn-rag-003": "hr-ld",
    "b2b-syn-segment-002": "team-lead",
    "b2b-syn-rag-004": "platform-lead",
    "b2b-syn-nurture-001": "team-lead",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def sha256_prefix(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:16]


def patch_b2c_extraction(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rec in copy.deepcopy(records):
        rid = rec["id"]
        md = rec.setdefault("metadata", {})
        md["dataset_version"] = 2

        if rid in MULTI_TURN_EXTRACTION:
            md["assistant_context"] = "paraphrased"

        if rid == "b2c-rag-008":
            rec["expected_output"]["answer_key_points"] = [
                "если политика возврата есть в KB — озвучить кратко",
                "если в KB нет деталей — не выдумывать сроки и комиссии; предложить consultation",
                "не подавать возврат как замену ознакомлению с программой",
                "публичного демо уроков нет",
            ]
            md["kb_verified"] = "data/b2c/faq-b2c.md"
            md["notes"] = "v2: эталон условный — зависит от наличия политики в KB"

        if rid == "b2c-rag-010":
            rec["metadata"]["dataset_type"] = "b2c-objection"
            rec["metadata"]["group"] = "G4"
            rec["metadata"]["category"] = "G4.2"
            rec["expected_output"]["must_not"] = ["давить на оплату", "обещать демо-уроки"]

        if rid == "b2c-segment-001":
            md["input_fidelity"] = "paraphrase"

        out.append(rec)

    out.append(
        {
            "id": "b2c-objection-m08",
            "input": [
                {
                    "role": "assistant",
                    "content": "Добрый день! Вы видели наш оффер на 2026 год? В нём включена веб-разработка.",
                },
                {
                    "role": "user",
                    "content": "Спасибо за предложение. Я уже разобрался, но думаю что многие заинтересуются модулем по веб-разработке.",
                },
            ],
            "expected_output": {
                "segment": "b2c",
                "product_codes": ["agents", "fullstack-aidd"],
                "answer_key_points": [
                    "принять отказ без давления",
                    "поблагодарить за feedback про веб-модуль",
                    "не настаивать на продаже после «уже разобрался»",
                    "при желании — мягко оставить дверь открытой для будущих потоков",
                ],
                "should_clarify": False,
                "tools": [],
            },
            "metadata": {
                "dataset_type": "b2c-objection",
                "group": "G8",
                "category": "G8.5",
                "source": "extraction",
                "source_chat": "CHAT_0070",
                "turn_mode": "multi",
                "difficulty": "medium",
                "assistant_context": "paraphrased",
                "dataset_version": 2,
            },
        }
    )
    return out


def patch_b2c_synthetic(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rec in copy.deepcopy(records):
        rid = rec["id"]
        md = rec.setdefault("metadata", {})
        md["dataset_version"] = 2

        if rid in PERSONA_BY_ID:
            md["persona"] = PERSONA_BY_ID[rid]

        if rid in TOOL_PAYMENT_IDS:
            md["category"] = "G9.4"

        if isinstance(rec.get("input"), list):
            md.setdefault("assistant_context", "paraphrased")

        if rec["metadata"].get("group") == "G4" and "must_not" not in rec.get("expected_output", {}):
            rec["expected_output"]["must_not"] = ["обещать демо", "выдуманная ссылка на preview"]

        out.append(rec)

    out.append(
        {
            "id": "b2c-nurture-001",
            "input": "Клиент два дня назад написал «сегодня ознакомлюсь с материалами и решу» по комбо-курсу и не отвечал.",
            "expected_output": {
                "segment": "b2c",
                "product_codes": [],
                "answer_key_points": [
                    "мягкий follow-up: удалось ли ознакомиться",
                    "предложить ответить на вопросы по программе",
                    "без давления на оплату",
                ],
                "should_clarify": False,
                "tools": [],
            },
            "metadata": {
                "dataset_type": "b2c-objection",
                "group": "G8",
                "category": "G8.1",
                "source": "synthetic",
                "source_chat": "CHAT_0014",
                "turn_mode": "single",
                "difficulty": "easy",
                "persona": "cpo",
                "seed": 42,
                "notes": "reference-free: follow-up агента по паттерну эксперта из CHAT_0014",
                "dataset_version": 2,
            },
        }
    )
    return out


def patch_b2b_extraction(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only verbatim peer messages; reconstruction moves to synthetic."""
    out: list[dict[str, Any]] = []
    moved: list[dict[str, Any]] = []

    for rec in copy.deepcopy(records):
        rid = rec["id"]
        md = rec.setdefault("metadata", {})
        md["dataset_version"] = 2

        if rid in B2B_RECONSTRUCTION_IDS:
            md["source"] = "reconstruction"
            md["notes"] = (
                "v2: входящий запрос реконструирован из исходящего CHAT_0127; "
                "перенесён в synthetic.jsonl"
            )
            moved.append(rec)
            continue

        if rid == "b2b-rag-002":
            rec["expected_output"]["must_not"] = [
                "называть точную сумму без брифа",
                "предлагать B2C checkout для команды",
            ]

        if rid in MULTI_TURN_EXTRACTION:
            md["assistant_context"] = "paraphrased"

        out.append(rec)

    return out, moved


def patch_b2b_synthetic(
    records: list[dict[str, Any]], moved: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rec in copy.deepcopy(moved):
        md = rec.setdefault("metadata", {})
        md["source"] = "reconstruction"
        md["dataset_version"] = 2
        if "перенесён" in md.get("notes", ""):
            md["notes"] = md["notes"].replace("перенесён в synthetic.jsonl", "synthetic branch")
        out.append(rec)

    for rec in copy.deepcopy(records):
        rid = rec["id"]
        md = rec.setdefault("metadata", {})
        md["dataset_version"] = 2
        if rid in PERSONA_BY_ID:
            md["persona"] = PERSONA_BY_ID[rid]
        if isinstance(rec.get("input"), list):
            md.setdefault("assistant_context", "paraphrased")
        out.append(rec)

    return out


def merge_dataset(*parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for part in parts:
        merged.extend(part)
    return merged


def main() -> None:
    b2c_ext = patch_b2c_extraction(load_jsonl(V1 / "b2c/v1/extraction.jsonl"))
    b2c_syn = patch_b2c_synthetic(load_jsonl(V1 / "b2c/v1/synthetic.jsonl"))
    b2b_ext, b2b_moved = patch_b2b_extraction(load_jsonl(V1 / "b2b/v1/extraction.jsonl"))
    b2b_syn = patch_b2b_synthetic(load_jsonl(V1 / "b2b/v1/synthetic.jsonl"), b2b_moved)

    paths = {
        "b2c_ext": V2 / "b2c/v2/extraction.jsonl",
        "b2c_syn": V2 / "b2c/v2/synthetic.jsonl",
        "b2c_ds": V2 / "b2c/v2/dataset.jsonl",
        "b2b_ext": V2 / "b2b/v2/extraction.jsonl",
        "b2b_syn": V2 / "b2b/v2/synthetic.jsonl",
        "b2b_ds": V2 / "b2b/v2/dataset.jsonl",
    }

    write_jsonl(paths["b2c_ext"], b2c_ext)
    write_jsonl(paths["b2c_syn"], b2c_syn)
    write_jsonl(paths["b2c_ds"], merge_dataset(b2c_ext, b2c_syn))
    write_jsonl(paths["b2b_ext"], b2b_ext)
    write_jsonl(paths["b2b_syn"], b2b_syn)
    write_jsonl(paths["b2b_ds"], merge_dataset(b2b_ext, b2b_syn))

    print("B2C v2:", len(b2c_ext), "extraction +", len(b2c_syn), "synthetic =", len(b2c_ext) + len(b2c_syn))
    print("B2B v2:", len(b2b_ext), "extraction +", len(b2b_syn), "synthetic =", len(b2b_ext) + len(b2b_syn))
    for name, path in paths.items():
        print(f"  {name}: {path.relative_to(ROOT)} sha256={sha256_prefix(path)}")


if __name__ == "__main__":
    main()
