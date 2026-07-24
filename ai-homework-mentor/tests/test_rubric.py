"""Unit-тесты выбора рубрики и детектора темы."""

from __future__ import annotations

from pathlib import Path

from mentor.agent import AgentRunContext, _ask_user_impl, _reset_workspace_after_topic_change
from mentor.config import AppConfig
from mentor.parser import Submission
from mentor.rubric import detect_topic, normalize_topic_label, prepare_rubric, select_rubric


def _submission(topic: str | None = None) -> Submission:
    return Submission(source_type="local", source="/tmp/project", topic=topic)


def test_detect_topic_mentor_like_project_prefers_cli(tmp_path: Path) -> None:
    """Регрессия: meta-строки fastapi в rubric.py не должны побеждать typer в cli.py."""
    code_dir = tmp_path / "code"
    (code_dir / "mentor").mkdir(parents=True)
    (code_dir / "tests").mkdir()
    (code_dir / "mentor" / "cli.py").write_text(
        "import typer\napp = typer.Typer()\n",
        encoding="utf-8",
    )
    (code_dir / "mentor" / "rubric.py").write_text(
        'TOPIC_FASTAPI = "fastapi"\nFASTAPI_TOPIC_KEYWORDS = ("fastapi",)\n',
        encoding="utf-8",
    )
    (code_dir / "tests" / "test_rubric.py").write_text(
        "from fastapi import FastAPI\n",
        encoding="utf-8",
    )
    code_index = (
        "# Code Index\n\n## Tree\n\n"
        "- `mentor/cli.py` (50 lines)\n"
        "- `mentor/rubric.py` (80 lines)\n"
        "- `tests/test_rubric.py` (20 lines)\n"
    )
    topic = detect_topic(_submission(), code_index, code_dir=code_dir)
    assert topic == "python-cli"


def test_detect_topic_fastapi_requires_real_import(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "meta.py").write_text('label = "fastapi"\n', encoding="utf-8")
    (code_dir / "main.py").write_text("from fastapi import FastAPI\n", encoding="utf-8")
    code_index = "# Code Index\n\n## Tree\n\n- `meta.py` (5 lines)\n- `main.py` (10 lines)\n"
    topic = detect_topic(_submission(), code_index, code_dir=code_dir)
    assert topic == "fastapi"


def test_detect_topic_cli_from_typer_import(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "cli.py").write_text("import typer\n", encoding="utf-8")
    code_index = "# Code Index\n\n## Tree\n\n- `cli.py` (30 lines)\n"
    topic = detect_topic(_submission(), code_index, code_dir=code_dir)
    assert topic == "python-cli"


def test_detect_topic_from_submission_text() -> None:
    code_index = "# Code Index\n\n## Tree\n\n- `main.py` (10 lines)\n"
    topic = detect_topic(_submission("REST API на FastAPI"), code_index)
    assert topic == "fastapi"


def test_detect_topic_returns_none_when_ambiguous(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")
    code_index = "# Code Index\n\n## Tree\n\n- `main.py` (10 lines)\n"
    topic = detect_topic(_submission(), code_index, code_dir=code_dir)
    assert topic is None


def test_detect_topic_ignores_fastapi_in_yaml_paths(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "cli.py").write_text("import typer\n", encoding="utf-8")
    code_index = (
        "# Code Index\n\n## Tree\n\n"
        "- `mentor/config/rubrics/fastapi-service.yaml` (40 lines)\n"
        "- `cli.py` (30 lines)\n"
    )
    topic = detect_topic(_submission(), code_index, code_dir=code_dir)
    assert topic == "python-cli"


def test_select_rubric_none_returns_default() -> None:
    path = select_rubric(None)
    assert path.name == "default.yaml"


def test_select_rubric_fastapi() -> None:
    path = select_rubric("fastapi")
    assert path.name == "fastapi-service.yaml"


def test_select_rubric_cli() -> None:
    path = select_rubric("python-cli")
    assert path.name == "python-cli.yaml"


def test_normalize_topic_label_user_answer() -> None:
    assert normalize_topic_label("FastAPI-сервис") == "fastapi"
    assert normalize_topic_label("CLI-утилита") == "python-cli"


def test_prepare_rubric_writes_workspace_file(tmp_path: Path) -> None:
    _, rubric_file, display_topic = prepare_rubric(tmp_path, "fastapi")
    assert rubric_file == "fastapi-service.yaml"
    assert "FastAPI" in display_topic or display_topic
    assert (tmp_path / "rubric.md").exists()
    content = (tmp_path / "rubric.md").read_text(encoding="utf-8")
    assert "api-design" in content


def test_ask_user_uses_pending_answer_without_callback(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code").mkdir()
    (workspace / "code-index.md").write_text("# Code Index\n\n- **files:** 0\n", encoding="utf-8")
    (workspace / "plan.md").write_text("# old default plan\n", encoding="utf-8")
    (workspace / "notes").mkdir()
    (workspace / "notes" / "review-structure.md").write_text("stale", encoding="utf-8")
    submission = Submission(source_type="local", source="/tmp", topic=None)
    ctx = AgentRunContext(
        workspace=workspace,
        config=AppConfig(openrouter_api_key="test-key"),
        submission=submission,
        pending_user_answer="CLI-утилита на Python",
    )
    prompts = 0

    def callback(_question: str) -> str:
        nonlocal prompts
        prompts += 1
        return "should-not-be-called"

    ctx.user_answer_callback = callback

    result = _ask_user_impl("Какой тип проекта?", ctx)

    assert prompts == 0
    assert result == "CLI-утилита на Python"
    assert not (workspace / "plan.md").exists()
    assert not (workspace / "notes" / "review-structure.md").exists()
    assert ctx.plan_needs_rebuild is True
    assert ctx.topic_needs_clarification is False
    assert (workspace / "rubric.md").exists()
    assert "cli-design" in (workspace / "rubric.md").read_text(encoding="utf-8")


def test_reset_workspace_after_topic_change_removes_plan_and_notes(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "plan.md").write_text("plan", encoding="utf-8")
    (workspace / "notes").mkdir()
    (workspace / "notes" / "review-structure.md").write_text("note", encoding="utf-8")
    (workspace / "notes" / "review-code-quality.md").write_text("note", encoding="utf-8")

    _reset_workspace_after_topic_change(workspace)

    assert not (workspace / "plan.md").exists()
    assert not list((workspace / "notes").glob("review-*.md"))


def test_ask_user_rejected_when_auto_topic_detected(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    submission = Submission(source_type="local", source="/tmp", topic=None)
    ctx = AgentRunContext(
        workspace=workspace,
        config=AppConfig(openrouter_api_key="test-key"),
        submission=submission,
        auto_topic="python-cli",
    )

    result = _ask_user_impl("Какой тип?", ctx)

    assert "автоматически" in result
    assert "ask_user не нужен" in result
