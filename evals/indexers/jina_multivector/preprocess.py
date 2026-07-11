"""Image preprocessing for Jina v4 multivector indexing."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image


def resize_max_side(image_path: Path, max_side: int) -> Image.Image:
    """Resize so the longest side is at most max_side; preserve aspect ratio."""
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image
    scale = max_side / longest
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def image_to_base64_data_url(image: Image.Image, *, suffix: str = "png") -> str:
    """Encode PIL image as data URL for Jina API."""
    buffer = io.BytesIO()
    mime = "image/png" if suffix.lower() == "png" else f"image/{suffix.lower()}"
    image.save(buffer, format=suffix.upper() if suffix.upper() in {"PNG", "JPEG"} else "PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def png_to_jina_image_input(image_path: Path, max_side: int) -> dict[str, str]:
    """Resize PNG and return Jina input object with base64 image."""
    suffix = image_path.suffix.lower().lstrip(".") or "png"
    image = resize_max_side(image_path, max_side)
    return {"image": image_to_base64_data_url(image, suffix=suffix)}
