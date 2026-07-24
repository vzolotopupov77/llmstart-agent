"""Настройка логирования."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str) -> None:
    """Stdout, human-readable формат для dev."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
        force=True,
    )
