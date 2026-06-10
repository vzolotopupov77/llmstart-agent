"""Flatten Telegram-style JSON dialog exports to plain text for Level-1 analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path

INPUT_DIR = Path(__file__).resolve().parents[2] / "dialogs"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "flat"

ROLE_LABELS = {"peer": "USER", "me": "EXPERT"}


def flatten_chat(chat_path: Path) -> str:
    data = json.loads(chat_path.read_text(encoding="utf-8"))
    lines: list[str] = [f"# Chat: {chat_path.stem}", ""]
    for msg in data.get("messages", []):
        role = ROLE_LABELS.get(msg.get("from", ""), msg.get("from", "UNKNOWN").upper())
        date = msg.get("date", "")
        text = msg.get("text", "")
        if isinstance(text, list):
            parts = []
            for part in text:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    parts.append(str(part["text"]))
            text = "".join(parts)
        text = re.sub(r"\n{3,}", "\n\n", str(text).strip())
        lines.append(f"[{date}] {role}:")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chats = sorted(INPUT_DIR.glob("CHAT_*.json"))
    if not chats:
        raise SystemExit(f"No chats found in {INPUT_DIR}")
    for chat_path in chats:
        out_path = OUTPUT_DIR / f"{chat_path.stem}.txt"
        out_path.write_text(flatten_chat(chat_path), encoding="utf-8")
        print(f"Wrote {out_path.name} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
