"""Загрузка промптов из YAML."""

from __future__ import annotations

from pathlib import Path

import yaml


class PromptLoadError(Exception):
    """Ошибка загрузки промпта."""


def load_yaml_prompt(path: Path, *, key: str = "prompt") -> str:
    """Загрузить текст промпта из YAML."""
    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    msg = f"Не удалось загрузить промпт из {path.as_posix()}"
    raise PromptLoadError(msg)
