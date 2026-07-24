"""Unit-тесты загрузки навыков."""

from __future__ import annotations

from pathlib import Path

from mentor.skills import resolve_skill, resolve_skill_path, skill_search_roots


def test_resolve_skill_modern_python() -> None:
    content = resolve_skill("modern-python")
    assert content is not None
    assert "modern-python" in content.lower() or "uv" in content


def test_resolve_skill_missing_returns_none() -> None:
    assert resolve_skill("nonexistent-skill-xyz") is None


def test_resolve_skill_path_for_existing() -> None:
    path = resolve_skill_path("modern-python")
    assert path is not None
    assert path.name == "SKILL.md"
    assert path.is_file()


def test_skill_search_roots_includes_global_agents() -> None:
    roots = skill_search_roots()
    assert any("skills" in root.as_posix() for root in roots)
    assert any(root == Path.home() / ".agents" / "skills" for root in roots)
