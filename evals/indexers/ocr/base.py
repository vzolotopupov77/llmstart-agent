"""OCR engine protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class OcrEngine(Protocol):
    """Recognize visible text from a slide image."""

    name: str

    def recognize(self, image_path: Path) -> str: ...
