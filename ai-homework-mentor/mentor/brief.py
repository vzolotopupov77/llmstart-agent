"""Формирование брифов для Reviewer-субагентов."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

from mentor.config import CONFIG_DIR
from mentor.skills import resolve_skill

DOCUMENTATION_FILES = ("README.md", "readme.md", "README.rst", "docs/")
STRUCTURE_HINTS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Makefile",
    "main.py",
    "__init__.py",
    "cli.py",
)
ERROR_HANDLING_HINTS = ("cli.py", "client.py", "api.py", "http", "request", "openrouter")
MAX_FILES_PER_BRIEF = 12


@dataclass(frozen=True)
class RubricAspect:
    """Один аспект рубрики."""

    id: str
    name: str
    criteria: tuple[str, ...]
    skill: str | None = None
    prompt: str | None = None


class BriefError(Exception):
    """Ошибка формирования или разбора брифа."""


def estimate_tokens(text: str) -> int:
    """Грубая оценка токенов (≈4 символа на токен)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 4)


def parse_aspect_from_brief_path(brief_path: Path | str) -> str:
    """Извлечь aspect-id из brief-<aspect>.md."""
    name = Path(brief_path).name
    if not name.startswith("brief-") or not name.endswith(".md"):
        msg = f"неверный формат брифа: {name} (ожидается brief-<aspect>.md)"
        raise BriefError(msg)
    return name.removeprefix("brief-").removesuffix(".md")


def resolve_aspect_id(raw_aspect: str, rubric_path: Path) -> str:
    """Сопоставить aspect-id с rubric.md; нормализовать underscore → дефис."""
    aspects = load_rubric_aspects(rubric_path)
    known_ids = {aspect.id for aspect in aspects}
    if raw_aspect in known_ids:
        return raw_aspect

    hyphenated = raw_aspect.replace("_", "-")
    if hyphenated in known_ids:
        return hyphenated

    for aspect_id in known_ids:
        if aspect_id.replace("-", "_") == raw_aspect:
            return aspect_id

    allowed = ", ".join(sorted(known_ids))
    msg = f"неизвестный aspect-id `{raw_aspect}`; используй id из rubric.md: {allowed}"
    raise BriefError(msg)


def expected_brief_filename(aspect_id: str) -> str:
    """Имя файла брифа для aspect-id из рубрики."""
    return f"brief-{aspect_id}.md"


def expected_review_filename(aspect_id: str) -> str:
    """Имя файла ReviewNote для aspect-id из рубрики."""
    return f"review-{aspect_id}.md"


def load_rubric_aspects(rubric_path: Path) -> list[RubricAspect]:
    """Загрузить аспекты из rubric.md (YAML)."""
    if not rubric_path.exists():
        msg = f"рубрика не найдена: {rubric_path.as_posix()}"
        raise BriefError(msg)
    with rubric_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        msg = f"неверный формат рубрики: {rubric_path.as_posix()}"
        raise BriefError(msg)
    aspects_raw = raw.get("aspects")
    if not isinstance(aspects_raw, list):
        msg = "в рубрике отсутствует секция aspects"
        raise BriefError(msg)

    aspects: list[RubricAspect] = []
    for item in aspects_raw:
        if not isinstance(item, dict):
            continue
        aspect_id = str(item.get("id", "")).strip()
        name = str(item.get("name", aspect_id)).strip()
        criteria_raw = item.get("criteria", [])
        criteria = tuple(str(c).strip() for c in criteria_raw if str(c).strip())
        skill_raw = item.get("skill")
        skill = str(skill_raw).strip() if skill_raw else None
        if skill in {"", "null", "none"}:
            skill = None
        prompt_raw = item.get("prompt")
        prompt = str(prompt_raw).strip() if prompt_raw else None
        if prompt in {"", "null", "none"}:
            prompt = None
        if aspect_id:
            aspects.append(
                RubricAspect(
                    id=aspect_id,
                    name=name,
                    criteria=criteria,
                    skill=skill,
                    prompt=prompt,
                ),
            )
    if not aspects:
        msg = "рубрика не содержит аспектов"
        raise BriefError(msg)
    return aspects


def _parse_code_index_paths(code_index_path: Path) -> list[str]:
    if not code_index_path.exists():
        return []
    paths: list[str] = []
    for line in code_index_path.read_text(encoding="utf-8").splitlines():
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
        paths.append(f"code/{relative}")
    return paths


def _score_file_for_aspect(path: str, aspect_id: str) -> int:
    lower = path.lower()
    normalized = aspect_id.replace("_", "-")
    if normalized == "api-design":
        for hint in ("routes", "router", "api.py", "main.py", "schemas", "models"):
            if hint in lower:
                return 90
        if lower.endswith(".py"):
            return 50
        return 10
    if normalized == "cli-design":
        for hint in ("cli.py", "main.py", "__main__", "commands", "typer", "click"):
            if hint in lower:
                return 90
        if lower.endswith(".py"):
            return 45
        return 10
    if normalized in {"testing", "security"}:
        if "test" in lower or lower.endswith("_test.py"):
            return 95 if normalized == "testing" else 40
        if normalized == "security" and any(
            h in lower for h in ("auth", "security", "cors", "middleware")
        ):
            return 85
        if lower.endswith(".py"):
            return 35
        return 5
    if normalized == "documentation":
        if lower.endswith("readme.md") or "/readme.md" in lower:
            return 100
        if "/docs/" in lower or lower.endswith(".md"):
            return 80
        return 0
    if normalized == "structure":
        for hint in STRUCTURE_HINTS:
            if hint in lower:
                return 90
        if lower.endswith(".py"):
            return 40
        return 10
    if normalized == "error-handling":
        for hint in ERROR_HANDLING_HINTS:
            if hint in lower:
                return 85
        if lower.endswith(".py"):
            return 50
        return 5
    if normalized == "code-quality":
        if lower.endswith(".py"):
            return 70
        if lower.endswith((".toml", ".yaml", ".yml", ".cfg")):
            return 30
        return 0
    return 30 if lower.endswith(".py") else 10


def select_files_for_aspect(aspect_id: str, code_index_path: Path) -> list[str]:
    """Выбрать релевантные файлы из code-index.md для аспекта."""
    all_paths = _parse_code_index_paths(code_index_path)
    if not all_paths:
        return []

    scored = sorted(
        ((path, _score_file_for_aspect(path, aspect_id)) for path in all_paths),
        key=lambda item: item[1],
        reverse=True,
    )
    selected = [path for path, score in scored if score > 0][:MAX_FILES_PER_BRIEF]

    if aspect_id.replace("_", "-") == "documentation":
        readme_paths = [path for path in all_paths if path.lower().endswith("readme.md")]
        for readme in readme_paths:
            if readme not in selected:
                selected.insert(0, readme)

    if not selected:
        py_files = [path for path in all_paths if path.endswith(".py")]
        selected = py_files[:MAX_FILES_PER_BRIEF]

    return selected


def build_brief(
    aspect: RubricAspect,
    *,
    workspace: Path,
    topic: str,
    relevant_files: list[str] | None = None,
    skill_content: str | None = None,
    skill_name: str | None = None,
) -> Path:
    """Сформировать workspace/briefs/brief-<aspect>.md."""
    code_index_path = workspace / "code-index.md"
    files = relevant_files or select_files_for_aspect(aspect.id, code_index_path)
    normalized_files = []
    for path in files:
        clean = path.replace("\\", "/").lstrip("./")
        if not clean.startswith("code/"):
            clean = f"code/{clean.removeprefix('code/')}"
        normalized_files.append(clean)
    normalized_files = list(dict.fromkeys(normalized_files))

    criteria_lines = "\n".join(f"- {item}" for item in aspect.criteria)
    files_lines = "\n".join(f"- `{path}`" for path in normalized_files) or "- см. `code-index.md`"

    skill_section = ""
    resolved_skill_name = skill_name or aspect.skill
    if skill_content and resolved_skill_name:
        skill_section = (
            f"\n## Экспертный контекст (навык: {resolved_skill_name})\n\n{skill_content.strip()}\n"
        )

    content = (
        f"# Brief: {aspect.name}\n\n"
        f"**Aspect ID:** `{aspect.id}`\n"
        f"**Тема задания:** {topic}\n\n"
        "## Контекст workspace\n\n"
        "- Код студента — **только** в каталоге `code/` (пути с префиксом `code/`)\n"
        "- Корень workspace — служебные артефакты (`submission.md`, `rubric.md`, `code-index.md`)\n"
        "- README студента: `code/README.md`, **не** `README.md` в корне workspace\n"
        "- Перед утверждением «файл отсутствует» — сверься с `code-index.md`\n\n"
        "## Критерии рубрики\n\n"
        f"{criteria_lines}\n"
        f"{skill_section}\n"
        "## Файлы для анализа\n\n"
        f"{files_lines}\n\n"
        "## Результат\n\n"
        f"Запиши ReviewNote в `notes/review-{aspect.id}.md` с секциями "
        "`## findings` и `## recommendations`.\n"
    )

    briefs_dir = workspace / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    target = briefs_dir / f"brief-{aspect.id}.md"
    target.write_text(content, encoding="utf-8")
    return target


def load_default_aspects() -> list[RubricAspect]:
    """Загрузить аспекты дефолтной рубрики из config."""
    return load_rubric_aspects(CONFIG_DIR / "rubrics" / "default.yaml")


def build_all_briefs(
    workspace: Path,
    *,
    topic: str,
    on_skill: Callable[[str, str | None, bool], None] | None = None,
) -> list[Path]:
    """Сформировать брифы для всех аспектов рубрики с подключением навыков."""
    rubric_path = workspace / "rubric.md"
    aspects = load_rubric_aspects(rubric_path)
    paths: list[Path] = []
    for aspect in aspects:
        skill_content = resolve_skill(aspect.skill)
        skill_found = skill_content is not None
        if on_skill is not None:
            on_skill(aspect.id, aspect.skill, skill_found)
        paths.append(
            build_brief(
                aspect,
                workspace=workspace,
                topic=topic,
                skill_content=skill_content,
                skill_name=aspect.skill,
            ),
        )
    return paths
