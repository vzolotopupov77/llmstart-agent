"""Получение кода студента в workspace/code/."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mentor.parser import Submission

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    # Dogfooding: служебные каталоги проекта, не код студента
    "workspace",
    "sprints",
    "concept",
}

SKIP_FILE_NAMES = {".env", ".env.local", ".env.production"}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pyc",
    ".pyo",
    ".class",
    ".jar",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".sqlite",
    ".db",
}

GIT_CLONE_TIMEOUT_SECONDS = 60


class CodeRetrievalError(Exception):
    """Ошибка получения кода студента."""


def _should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES


def _should_skip_file(path: Path) -> bool:
    return path.name in SKIP_FILE_NAMES or _is_binary_file(path)


def _is_binary_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return True
    return b"\0" in chunk


def _copy_local_source(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)

    def ignore_names(_directory: str, names: list[str]) -> list[str]:
        return [name for name in names if _should_skip_dir(name)]

    shutil.copytree(source, target, ignore=ignore_names, dirs_exist_ok=False)

    for path in list(target.rglob("*")):
        if path.is_dir() and _should_skip_dir(path.name):
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and _should_skip_file(path):
            path.unlink(missing_ok=True)


def _clone_github_repo(url: str, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "git",
        "clone",
        "--depth=1",
        url,
        str(target),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=GIT_CLONE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"timeout: git clone не завершился за {GIT_CLONE_TIMEOUT_SECONDS} с"
        raise CodeRetrievalError(msg) from exc
    except FileNotFoundError as exc:
        msg = "git не найден в PATH — установите Git для клонирования репозиториев"
        raise CodeRetrievalError(msg) from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "неизвестная ошибка"
        lowered = stderr.lower()
        if "not found" in lowered or "does not exist" in lowered:
            msg = f"репозиторий не найден: {url}"
            raise CodeRetrievalError(msg)
        if "permission" in lowered or "authentication" in lowered:
            msg = f"нет доступа к репозиторию: {url}"
            raise CodeRetrievalError(msg)
        msg = f"git clone завершился с ошибкой: {stderr}"
        raise CodeRetrievalError(msg)


def _count_text_lines(path: Path) -> int:
    if _is_binary_file(path):
        return 0
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
    except OSError:
        return 0


def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def build_code_index(code_dir: Path, workspace: Path) -> Path:
    """Построить code-index.md с деревом файлов и статистикой."""
    files: list[Path] = []
    total_lines = 0
    total_bytes = 0

    if code_dir.exists():
        for path in sorted(code_dir.rglob("*")):
            if not path.is_file():
                continue
            if _should_skip_dir(path.name) or _is_binary_file(path):
                continue
            if path.name in SKIP_FILE_NAMES:
                continue
            files.append(path)
            total_lines += _count_text_lines(path)
            try:
                total_bytes += path.stat().st_size
            except OSError:
                continue

    lines: list[str] = [
        "# Code Index",
        "",
        "> Пути в дереве ниже — относительно каталога `code/`. "
        "Полный путь в workspace: `code/<path>`.",
        "",
        f"- **files:** {len(files)}",
        f"- **lines:** ~{total_lines:,}",
        f"- **size:** {_format_size(total_bytes)}",
        "",
        "## Tree",
        "",
    ]

    for path in files:
        relative = path.relative_to(code_dir).as_posix()
        file_lines = _count_text_lines(path)
        line = f"- `{relative}` ({file_lines} lines)"
        if relative.lower() == "readme.md":
            line += " — полный путь: `code/README.md`"
        lines.append(line)

    target = workspace / "code-index.md"
    workspace.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def retrieve_code(submission: Submission, workspace: Path) -> Path:
    """Получить код в workspace/code/ и записать code-index.md."""
    workspace.mkdir(parents=True, exist_ok=True)
    code_dir = workspace / "code"

    if submission.source_type == "github":
        _clone_github_repo(submission.source, code_dir)
    else:
        source_path = Path(submission.source)
        if not source_path.is_dir():
            msg = f"локальный путь не является директорией: {submission.source}"
            raise CodeRetrievalError(msg)
        _copy_local_source(source_path, code_dir)

    build_code_index(code_dir, workspace)
    return code_dir
