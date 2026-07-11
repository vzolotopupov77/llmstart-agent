"""Shared OCR image preprocessing for dark-theme slides."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

LUMINANCE_THRESHOLD = 128
CONTRAST_FACTOR = 1.5


def preprocess_for_ocr(image_path: Path) -> Image.Image:
    """Adaptive invert for dark backgrounds, then boost contrast."""
    image = Image.open(image_path).convert("RGB")
    gray = ImageOps.grayscale(image)
    pixels = gray.getdata()
    mean_luminance = sum(pixels) / max(len(pixels), 1)
    if mean_luminance < LUMINANCE_THRESHOLD:
        gray = ImageOps.invert(gray)
    return ImageEnhance.Contrast(gray).enhance(CONTRAST_FACTOR)
