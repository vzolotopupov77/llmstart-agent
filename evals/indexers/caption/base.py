"""VLM caption client protocol."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

CAPTION_PROMPT = """Ты анализируешь слайд презентации (изображение PNG).

Задача:
1. Перечисли ВЕСЬ видимый текст: заголовки, подписи, легенды, подписи к диаграммам.
2. Явно выпиши ВСЕ числа и проценты ТОЧНО как на слайде (без округления и «исправлений»).
3. Кратко опиши визуальную структуру (диаграмма, схема, таблица, список).

Запреты:
- Не додумывай данные, которых нет на изображении.
- Не заменяй числа «более правдоподобными».
- Не пиши общие фразы вместо конкретного содержимого.

Ответ на русском языке, структурированный текст."""


@dataclass(frozen=True)
class CaptionResult:
    """One VLM caption call result."""

    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    est_cost_usd: float


class CaptionClient(Protocol):
    """Generate a text caption for one slide image."""

    model_id: str

    def caption_image(self, image_path: Path) -> CaptionResult: ...
