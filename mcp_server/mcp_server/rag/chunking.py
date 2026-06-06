"""Markdown chunking utilities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """Single knowledge chunk with metadata."""

    text: str
    source: str
    segment: str


def chunk_markdown(
    content: str,
    *,
    source: str,
    segment: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Split markdown by headings, then fixed-size windows."""
    sections = _split_by_headings(content)
    chunks: list[TextChunk] = []
    for section in sections:
        cleaned = section.strip()
        if not cleaned:
            continue
        windows = _window_text(cleaned, chunk_size=chunk_size, overlap=chunk_overlap)
        chunks.extend(TextChunk(text=window, source=source, segment=segment) for window in windows)
    return chunks


def _split_by_headings(content: str) -> list[str]:
    lines = content.splitlines()
    sections: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("## ") and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current))
    if not sections:
        return [content]
    return sections


def _window_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    windows: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        windows.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return windows
