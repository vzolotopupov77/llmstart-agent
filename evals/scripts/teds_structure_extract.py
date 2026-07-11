"""Extract chart slide structure as HTML via VLM (TEDS hypothesis for method D)."""

from __future__ import annotations

import logging
from pathlib import Path

from indexers.caption.factory import make_caption_client
from indexers.caption.pricing import model_slug
from indexers.config import REPO_ROOT

logger = logging.getLogger(__name__)

STRUCTURE_PROMPT = (
    "Convert this presentation slide into semantic HTML that preserves layout structure.\n"
    "Rules:\n"
    "- Output ONLY valid HTML (no markdown fences, no commentary).\n"
    '- Use <div class="slide"> root, headings, <table class="bar-chart"> for charts, '
    '<span class="stat"> for big numbers.\n'
    "- Include all visible Russian text and percentages exactly as shown.\n"
    "- Preserve left/center/right panel grouping if present.\n"
)

DEFAULT_MODEL = "google/gemini-2.5-flash-lite"
DEFAULT_SLIDES = (10, 11)
CORPUS_DIR = REPO_ROOT / "data" / "multimodal-rag"
DEFAULT_OUT_DIR = REPO_ROOT / "evals" / "artifacts" / "multivector" / "teds-hyp"


def extract_structure_html(
    image_path: Path,
    *,
    model_id: str = DEFAULT_MODEL,
) -> str:
    from indexers.caption.openrouter import OpenRouterCaptionClient  # noqa: PLC0415

    client = make_caption_client(model_id)
    if not isinstance(client, OpenRouterCaptionClient):
        msg = f"Structure extract requires OpenRouterCaptionClient, got {type(client)}"
        raise TypeError(msg)

    from openai import OpenAI  # noqa: PLC0415

    openai_client = OpenAI(
        api_key=client._api_key,
        base_url=client._base_url,
        timeout=client._timeout_s,
    )
    from indexers.openrouter_common import image_to_data_url  # noqa: PLC0415

    data_url = image_to_data_url(image_path)
    response = openai_client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": STRUCTURE_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        max_tokens=2000,
    )
    content = response.choices[0].message.content or ""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def run_structure_extract(
    *,
    slide_ids: tuple[int, ...] = DEFAULT_SLIDES,
    corpus_dir: Path = CORPUS_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    model_id: str = DEFAULT_MODEL,
) -> dict[int, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[int, Path] = {}
    for slide_id in slide_ids:
        image_path = corpus_dir / f"slide-{slide_id:02d}.png"
        if not image_path.is_file():
            msg = f"Slide PNG missing: {image_path}"
            raise FileNotFoundError(msg)
        logger.info(
            "TEDS structure extract slide-%02d model=%s",
            slide_id,
            model_slug(model_id),
        )
        html = extract_structure_html(image_path, model_id=model_id)
        out_path = out_dir / f"slide-{slide_id:02d}.html"
        out_path.write_text(html, encoding="utf-8")
        written[slide_id] = out_path
        logger.info("Wrote %s (%d chars)", out_path, len(html))
    return written


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract slide structure HTML for TEDS")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_structure_extract(out_dir=args.out_dir, model_id=args.model)


if __name__ == "__main__":
    main()
