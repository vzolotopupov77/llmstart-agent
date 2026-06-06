"""Unit tests for message chunking."""

from app.services.message_chunker import chunk_message


def test_chunk_message_splits_long_text() -> None:
    """Long text is split into multiple chunks."""
    text = "x" * 250
    chunks = chunk_message(text, chunk_size=100)
    assert len(chunks) > 1
    assert "".join(chunks) == text


def test_chunk_message_keeps_short_text_single() -> None:
    """Short text stays in one chunk."""
    text = "Короткий ответ."
    assert chunk_message(text) == [text]
