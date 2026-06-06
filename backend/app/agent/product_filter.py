"""Filter catalog items to those recommended in the agent's final message."""

import re


def filter_recommended_products(
    items: list[dict[str, str | int]],
    final_message: str,
    *,
    max_items: int = 3,
) -> list[dict[str, str | int]] | None:
    """Keep products explicitly referenced in the assistant reply."""
    if not items or not final_message.strip():
        return None

    text = final_message.lower()
    matched: list[dict[str, str | int]] = []
    seen_codes: set[str] = set()

    sorted_items = sorted(
        items,
        key=lambda item: len(str(item.get("code", ""))),
        reverse=True,
    )

    for item in sorted_items:
        code = item.get("code")
        title = item.get("title")
        if not isinstance(code, str) or code in seen_codes:
            continue

        title_str = title.lower() if isinstance(title, str) else ""
        if _code_in_text(code.lower(), text) or (title_str and title_str in text):
            matched.append(item)
            seen_codes.add(code)

    if not matched:
        return None

    return matched[:max_items]


def _code_in_text(code: str, text: str) -> bool:
    pattern = rf"(?<![a-z0-9-]){re.escape(code)}(?![a-z0-9-])"
    return re.search(pattern, text) is not None
