"""Выбор рубрики по теме задания и сигналам в code-index."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from mentor.config import CONFIG_DIR
from mentor.parser import Submission

TOPIC_FASTAPI = "fastapi"
TOPIC_CLI = "python-cli"

FASTAPI_TOPIC_KEYWORDS = (
    "fastapi",
    "rest api",
    "restful",
    "uvicorn",
    "openapi",
    "swagger",
    "starlette",
)
CLI_TOPIC_KEYWORDS = (
    "cli",
    "typer",
    "click",
    "argparse",
    "command line",
    "command-line",
    "консоль",
    "утилита",
)
FASTAPI_CODE_PATTERNS = (
    re.compile(r"\bfrom\s+fastapi\b", re.IGNORECASE),
    re.compile(r"\bimport\s+fastapi\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+uvicorn\b", re.IGNORECASE),
    re.compile(r"\bimport\s+uvicorn\b", re.IGNORECASE),
    re.compile(r"\bFastAPI\s*\(", re.IGNORECASE),
    re.compile(r"\bAPIRouter\s*\(", re.IGNORECASE),
)
CLI_CODE_PATTERNS = (
    re.compile(r"\bimport\s+typer\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+typer\b", re.IGNORECASE),
    re.compile(r"\bimport\s+click\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+click\b", re.IGNORECASE),
    re.compile(r"\bimport\s+argparse\b", re.IGNORECASE),
    re.compile(r"\btyper\.Typer\s*\(", re.IGNORECASE),
    re.compile(r"\b@click\.(command|group)\b", re.IGNORECASE),
    re.compile(r"\btyper\.Option\b", re.IGNORECASE),
    re.compile(r"\btyper\.Argument\b", re.IGNORECASE),
)

_TOPIC_DETECTION_SKIP_PREFIXES = ("tests/", "test_", "conftest.py")
_TOPIC_DETECTION_SKIP_FILES = frozenset({"rubric.py"})

RUBRIC_FILES = {
    TOPIC_FASTAPI: "fastapi-service.yaml",
    TOPIC_CLI: "python-cli.yaml",
}


class RubricError(Exception):
    """Ошибка работы с рубрикой."""


def _rubrics_dir() -> Path:
    return CONFIG_DIR / "rubrics"


def _parse_py_paths(code_index: str) -> list[str]:
    """Извлечь пути .py из секции Tree code-index.md."""
    paths: list[str] = []
    for line in code_index.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- `"):
            continue
        start = stripped.find("`") + 1
        end = stripped.find("`", start)
        if end <= start:
            continue
        relative = stripped[start:end]
        if " lines)" in relative:
            relative = relative.rsplit(" (", maxsplit=1)[0]
        if relative.endswith(".py"):
            paths.append(relative)
    return paths


def _should_skip_for_topic_detection(relative: str) -> bool:
    """Исключить тесты и meta-модули (rubric.py содержит строки 'fastapi')."""
    normalized = relative.replace("\\", "/").lower()
    name = Path(normalized).name
    if name in _TOPIC_DETECTION_SKIP_FILES:
        return True
    return normalized.startswith(_TOPIC_DETECTION_SKIP_PREFIXES) or "/tests/" in normalized


def _load_py_sources(code_dir: Path | None, code_index: str) -> list[str]:
    """Прочитать содержимое .py из code/ для детектора импортов."""
    if code_dir is None or not code_dir.is_dir():
        return []
    sources: list[str] = []
    for relative in _parse_py_paths(code_index):
        if _should_skip_for_topic_detection(relative):
            continue
        path = code_dir / relative
        if not path.is_file():
            continue
        try:
            sources.append(path.read_text(encoding="utf-8", errors="ignore")[:8000])
        except OSError:
            continue
    return sources


def detect_topic(
    submission: Submission,
    code_index: str,
    *,
    code_dir: Path | None = None,
) -> str | None:
    """Определить тему по тексту задания и импортам в code/."""
    topic_text = (submission.topic or "").casefold()

    fastapi_score = sum(1 for kw in FASTAPI_TOPIC_KEYWORDS if kw in topic_text)
    cli_score = sum(1 for kw in CLI_TOPIC_KEYWORDS if kw in topic_text)

    for source in _load_py_sources(code_dir, code_index):
        fastapi_score += sum(1 for pat in FASTAPI_CODE_PATTERNS if pat.search(source))
        cli_score += sum(1 for pat in CLI_CODE_PATTERNS if pat.search(source))

    if fastapi_score > 0 and fastapi_score >= cli_score:
        return TOPIC_FASTAPI
    if cli_score > 0:
        return TOPIC_CLI
    return None


def normalize_topic_label(topic: str | None) -> str | None:
    """Нормализовать пользовательский ответ или тему CLI к ключу рубрики."""
    if topic is None:
        return None
    lowered = topic.casefold().strip()
    if not lowered or lowered in {"не указана", "unknown", "другое"}:
        return None
    if any(kw in lowered for kw in FASTAPI_TOPIC_KEYWORDS):
        return TOPIC_FASTAPI
    if any(kw in lowered for kw in CLI_TOPIC_KEYWORDS):
        return TOPIC_CLI
    if "api" in lowered and "rest" in lowered:
        return TOPIC_FASTAPI
    return lowered


def select_rubric(topic: str | None) -> Path:
    """Вернуть путь к YAML-рубрике; None → default.yaml."""
    rubrics_dir = _rubrics_dir()
    normalized = normalize_topic_label(topic)
    if normalized is None:
        return rubrics_dir / "default.yaml"

    filename = RUBRIC_FILES.get(normalized)
    if filename is None and normalized in RUBRIC_FILES.values():
        return rubrics_dir / normalized

    if filename is None:
        if "fastapi" in normalized or normalized.endswith("-service"):
            filename = RUBRIC_FILES[TOPIC_FASTAPI]
        elif "cli" in normalized:
            filename = RUBRIC_FILES[TOPIC_CLI]
        else:
            return rubrics_dir / "default.yaml"

    candidate = rubrics_dir / filename
    if candidate.exists():
        return candidate
    return rubrics_dir / "default.yaml"


def prepare_rubric(workspace: Path, topic: str | None) -> tuple[Path, str, str]:
    """Скопировать выбранную рубрику в workspace/rubric.md.

    Returns:
        (target_path, rubric_filename, display_topic)

    """
    source = select_rubric(topic)
    target = workspace / "rubric.md"
    if not source.exists():
        msg = f"рубрика не найдена: {source.as_posix()}"
        raise RubricError(msg)
    shutil.copyfile(source, target)
    display_topic = topic or "общий Python-проект"
    return target, source.name, display_topic


def read_code_index(workspace: Path) -> str:
    """Прочитать code-index.md или пустую строку."""
    path = workspace / "code-index.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
