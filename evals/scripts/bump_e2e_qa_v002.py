"""One-off helper: build e2e-qa v002 from v001 (eval-03 Task 02)."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from scripts.dataset_models import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "evals/datasets/e2e/e2e-qa/v001_2026-06-14.yaml"
DST = REPO_ROOT / "evals/datasets/e2e/e2e-qa/v002_2026-06-15.yaml"


def _add_kp(eo: dict, *points: str) -> None:
    for point in points:
        if point not in eo["answer_key_points"]:
            eo["answer_key_points"].append(point)


def _add_must_not(eo: dict, *rules: str) -> None:
    bucket = eo.setdefault("must_not", [])
    for rule in rules:
        if rule not in bucket:
            bucket.append(rule)


def build_v002() -> None:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    v2 = copy.deepcopy(data)
    v2["version"] = "v002"
    v2["created"] = "2026-06-15"
    v2["description"] = (
        "End-to-end pre-purchase QA (v002): sharpened criteria from error analysis eval-03 Task 02"
    )

    by_id = {item["id"]: item for item in v2["items"]}

    _add_kp(
        by_id["e2e-qa-0003"]["expected_output"],
        "при TBD расписания — всё равно назвать ориентир вечер/выходные",
    )
    _add_must_not(
        by_id["e2e-qa-0003"]["expected_output"],
        "полный отказ без упоминания длительности (~2 ч) и доступности записей",
    )

    _add_kp(
        by_id["e2e-qa-0005"]["expected_output"],
        "явно назвать code vibe-coding-intensive",
        "даже при TBD расписании — дать структуру семинары, практика, чат-поддержка",
    )
    _add_must_not(
        by_id["e2e-qa-0005"]["expected_output"],
        "отказ «нет данных о расписании» без описания структуры intensive",
    )

    _add_must_not(
        by_id["e2e-qa-0011"]["expected_output"],
        "повторный вопрос про цель или опыт после явного отказа пользователя",
    )

    _add_kp(
        by_id["e2e-qa-0017"]["expected_output"],
        "поблагодарить за оплату и перейти к сбору контактов для save_lead",
    )
    _add_must_not(
        by_id["e2e-qa-0017"]["expected_output"],
        "только запрос email/телефона без попытки confirm_payment",
    )

    _add_kp(
        by_id["e2e-qa-0021"]["expected_output"],
        "кратко перечислить 1–2 программы из каталога (agents, fullstack, intensive)",
    )
    _add_must_not(
        by_id["e2e-qa-0021"]["expected_output"],
        "обещать прислать урок или демо-URL",
    )

    _add_kp(
        by_id["e2e-qa-0023"]["expected_output"],
        "ответить на последний user turn про вечерние созвоны после работы",
    )
    _add_must_not(
        by_id["e2e-qa-0023"]["expected_output"],
        "предлагать другой продукт или intensive без ответа на sync-objection",
    )

    _add_kp(
        by_id["e2e-qa-0024"]["expected_output"],
        "если точное время неизвестно — дать ориентир из KB (выходной слот, MSK)",
    )
    _add_must_not(
        by_id["e2e-qa-0024"]["expected_output"],
        "«расписание неизвестно» без ориентиров из KB",
    )

    DST.write_text(
        yaml.dump(v2, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    manifest = load_manifest(DST)
    print(f"Wrote {DST.name}: {len(manifest.items)} items, version={manifest.version}")


if __name__ == "__main__":
    build_v002()
