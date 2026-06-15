"""Smoke: GEval comments on 3 representative items (requires OPENROUTER_API_KEY)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from scripts.evaluators import get_e2e_evaluators
from scripts.judge_client import load_env_file, require_openrouter_key

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    load_env_file(REPO_ROOT / ".env")
    try:
        require_openrouter_key()
    except SystemExit:
        print("smoke_evaluators: SKIP (no OPENROUTER_API_KEY)", file=sys.stderr)
        return 0

    judge = SimpleNamespace(
        name="google/gemini-2.5-flash-lite",
        provider="openrouter",
        temperature=0.0,
    )
    answer_correctness = get_e2e_evaluators(judge).item_evaluators[2]

    cases = [
        {
            "name": "installment",
            "input": "Есть ли рассрочка на комбо?",
            "message": "На MVP оплата через демо-ссылку; рассрочка пока недоступна.",
            "expected": {
                "answer_key_points": ["не обещать реальную рассрочку"],
                "must_not": ["обещать рассрочку сейчас"],
            },
            "forbidden_in_comment": ["payment link for agents"],
        },
        {
            "name": "september",
            "input": [
                {"role": "user", "content": "Есть курс в записях?"},
                {"role": "assistant", "content": "agents подходит."},
                {"role": "user", "content": "Следующий поток когда?"},
            ],
            "message": "Точной даты набора в сентябре в KB нет; могу напомнить позже.",
            "expected": {
                "answer_key_points": [
                    "признать временной барьер",
                    "не обещать точную дату без KB",
                ],
            },
            "forbidden_in_comment": ["payment link for agents", "create a payment link"],
        },
        {
            "name": "payment",
            "input": [
                {"role": "user", "content": "Посоветуйте agents."},
                {"role": "assistant", "content": "Рекомендую agents."},
                {"role": "user", "content": "Дайте ссылку на оплату."},
            ],
            "message": "Вот ссылка на оплату agents: https://pay.mock/example",
            "expected": {
                "answer_key_points": ["создать payment link для agents"],
            },
            "forbidden_in_comment": [],
        },
    ]

    failed = 0
    for case in cases:
        result = answer_correctness(
            input=case["input"],
            output={"message": case["message"]},
            expected_output=case["expected"],
        )
        comment_lower = result.comment.lower()
        bad = any(f.lower() in comment_lower for f in case["forbidden_in_comment"])
        status = "BAD" if bad else "OK"
        if bad:
            failed += 1
        print(f"--- {case['name']} score={result.value} [{status}] ---")
        print(result.comment[:400])
        print()

    if failed:
        print(f"smoke_evaluators: {failed} case(s) with irrelevant comments", file=sys.stderr)
        return 1
    print("smoke_evaluators: all comments relevant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
