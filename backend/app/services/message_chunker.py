"""Split assistant messages into SSE delta chunks."""

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def chunk_message(text: str, *, chunk_size: int = 100) -> list[str]:
    """Split text into chunks for SSE message events."""
    stripped = text.strip()
    if not stripped:
        return [""]

    sentences = _SENTENCE_SPLIT.split(stripped)
    chunks: list[str] = []
    buffer = ""

    for sentence in sentences:
        candidate = f"{buffer} {sentence}".strip() if buffer else sentence
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            chunks.append(buffer)
            buffer = sentence
        elif len(sentence) <= chunk_size:
            buffer = sentence
        else:
            chunks.extend(_split_long_segment(sentence, chunk_size))
            buffer = ""

    if buffer:
        chunks.append(buffer)

    return chunks or [stripped]


def _split_long_segment(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    words = text.split()
    if not words:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    parts: list[str] = []
    current = ""

    for word in words:
        if len(word) > chunk_size:
            if current:
                parts.append(current)
                current = ""
            parts.extend(word[i : i + chunk_size] for i in range(0, len(word), chunk_size))
            continue

        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            parts.append(current)
        current = word

    if current:
        parts.append(current)

    return parts or [text]
