.PHONY: dev lint format typecheck test test-backend ci

dev:
	uv sync
	uv tool install -e . --force
	@echo.
	@echo CLI ready: mentor check . --verbose
	@echo Or without global install: uv run mentor check . --verbose

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy mentor

test: test-backend

test-backend:
	uv run pytest

ci: lint typecheck test
