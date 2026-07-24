"""Парсинг входа CLI: GitHub URL или локальный путь + тема задания."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

GITHUB_URL_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/(?P<owner>[^/\s#?]+)/(?P<repo>[^/\s#?]+)(?:\.git)?/?(?:[#?].*)?$",
    re.IGNORECASE,
)

SourceType = Literal["github", "local"]


@dataclass(frozen=True, slots=True)
class Submission:
    """Разобранный вход пользователя."""

    source_type: SourceType
    source: str
    topic: str | None


def parse_source(source: str) -> tuple[SourceType, str]:
    """Определить тип источника и нормализованное значение."""
    stripped = source.strip()
    if not stripped:
        msg = "Вход пустой. Укажите GitHub-ссылку или локальный путь к коду."
        raise ValueError(msg)

    github_match = GITHUB_URL_PATTERN.match(stripped)
    if github_match is not None:
        owner = github_match.group("owner")
        repo = github_match.group("repo").removesuffix(".git")
        normalized = f"https://github.com/{owner}/{repo}"
        return "github", normalized

    local_path = Path(stripped).expanduser()
    if local_path.exists():
        return "local", str(local_path.resolve())

    msg = (
        f"Не удалось распознать вход: {stripped!r}. "
        "Ожидается GitHub-ссылка (github.com/user/repo) или существующий локальный путь."
    )
    raise ValueError(msg)


def parse_input(source: str, topic: str | None = None) -> Submission:
    """Разобрать source и topic в Submission."""
    source_type, normalized_source = parse_source(source)
    normalized_topic = topic.strip() if topic and topic.strip() else None
    return Submission(
        source_type=source_type,
        source=normalized_source,
        topic=normalized_topic,
    )


def write_submission_md(workspace: Path, submission: Submission) -> Path:
    """Записать submission.md в workspace."""
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / "submission.md"
    topic_line = submission.topic or "_не указана_"
    content = (
        "# Submission\n\n"
        f"- **source_type:** {submission.source_type}\n"
        f"- **source:** {submission.source}\n"
        f"- **topic:** {topic_line}\n"
    )
    target.write_text(content, encoding="utf-8")
    return target
