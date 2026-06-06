"""FastAPI application entrypoint."""

from app.factory import create_app

app = create_app()
