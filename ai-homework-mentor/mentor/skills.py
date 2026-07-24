"""Загрузка публичных навыков из .agents/skills/."""

from __future__ import annotations

from pathlib import Path

SKILL_FILENAME = "SKILL.md"


def skill_search_roots() -> tuple[Path, ...]:
    """Каталоги для поиска навыков (repo → глобальный ~/.agents)."""
    mentor_root = Path(__file__).resolve().parents[1]
    repo_root = mentor_root.parent
    return (
        repo_root / ".agents" / "skills",
        Path.home() / ".agents" / "skills",
        Path.home() / ".codex" / "skills",
    )


def resolve_skill(skill_name: str | None) -> str | None:
    """Прочитать SKILL.md по имени навыка; None если не найден."""
    if not skill_name or not skill_name.strip():
        return None
    clean_name = skill_name.strip()
    for root in skill_search_roots():
        skill_path = root / clean_name / SKILL_FILENAME
        if skill_path.is_file():
            return skill_path.read_text(encoding="utf-8")
    return None


def resolve_skill_path(skill_name: str | None) -> Path | None:
    """Путь к SKILL.md или None."""
    if not skill_name or not skill_name.strip():
        return None
    clean_name = skill_name.strip()
    for root in skill_search_roots():
        skill_path = root / clean_name / SKILL_FILENAME
        if skill_path.is_file():
            return skill_path
    return None
