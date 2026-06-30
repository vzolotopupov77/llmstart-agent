"""FastAPI application entrypoint."""

import logging
import os

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(levelname)s:     %(name)s — %(message)s",
)

from app.factory import create_app  # noqa: E402

app = create_app()
