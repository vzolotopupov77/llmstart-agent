"""Typer CLI — точка входа mentor."""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from mentor import __version__
from mentor.agent import OrchestratorError, run_orchestrator
from mentor.config import AppConfig, load_app_config
from mentor.events import AgentEvent
from mentor.feedback_validator import validate_feedback_artifacts
from mentor.logging_setup import setup_logging
from mentor.openrouter import check_openrouter_connection
from mentor.parser import parse_input, write_submission_md
from mentor.render import (
    read_code_index_stats,
    render_feedback_panel,
    render_submission_summary,
    render_todo_progress,
    render_user_question,
)
from mentor.renderer import VerboseRenderer
from mentor.retrieval import CodeRetrievalError, retrieve_code

app = typer.Typer(
    name="mentor",
    help="AI Homework Mentor — агент-ревьюер домашних заданий.",
    no_args_is_help=True,
)


def _create_console() -> Console:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if callable(reconfigure):
                reconfigure(encoding="utf-8")
    return Console()


console = _create_console()
logger = logging.getLogger(__name__)


@app.callback()
def cli() -> None:
    """Корневая команда mentor."""


def _resolve_output_mode(*, verbose: bool, compact: bool, config: AppConfig) -> str:
    if verbose:
        return "verbose"
    if compact:
        return "compact"
    return config.output_mode


def _render_startup_panel(
    config: AppConfig,
    *,
    output_mode: str,
    workspace: Path,
) -> None:
    lines = [
        f"Модель:    {config.model}",
        f"Режим:     {output_mode}",
    ]
    if output_mode == "verbose":
        lines.append(f"Context limit: {config.context_limit:,} токенов")
    lines.extend(
        [
            f"Конфиг:    {config.config_path.as_posix()}",
            f"Workspace: {workspace.as_posix()}",
        ],
    )
    console.print(
        Panel(
            "\n".join(lines),
            title=f"AI Homework Mentor v{__version__}",
            border_style="blue",
        ),
    )


def _fail(message: str) -> None:
    console.print(f"[red]✗[/red] {message}")
    raise typer.Exit(code=1)


@app.command()
def check(
    source: str = typer.Argument(
        ...,
        help="GitHub-ссылка или локальный путь к коду студента.",
    ),
    topic: str | None = typer.Argument(
        None,
        help="Тема или описание задания.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Подробный вывод событий агента.",
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        "-c",
        help="Компактный вывод: шаги плана и итоговый Feedback.",
    ),
) -> None:
    """Проверить домашнее задание по рубрике."""
    config = load_app_config()
    setup_logging(config.log_level)
    output_mode = _resolve_output_mode(verbose=verbose, compact=compact, config=config)

    workspace = Path(tempfile.mkdtemp(prefix="mentor-workspace-"))
    logger.info(
        "mentor check started",
        extra={"model": config.model, "output_mode": output_mode},
    )

    _render_startup_panel(config, output_mode=output_mode, workspace=workspace)

    ok, message = check_openrouter_connection(config.openrouter_api_key, config.model)
    if ok:
        console.print(f"[green]✓[/green] OpenRouter: {message}")
    else:
        console.print(f"[red]✗[/red] OpenRouter: {message}")
        raise typer.Exit(code=1)

    console.print()

    try:
        submission = parse_input(source, topic)
    except ValueError as exc:
        _fail(str(exc))

    write_submission_md(workspace, submission)

    try:
        retrieve_code(submission, workspace)
    except CodeRetrievalError as exc:
        _fail(str(exc))

    file_count, line_count = read_code_index_stats(workspace)
    if submission.source_type == "github":
        source_label = submission.source
    elif source in {".", "./"}:
        source_label = "./"
    else:
        source_label = f"./{Path(source).name}/"
    render_submission_summary(
        console,
        topic=submission.topic,
        source_label=source_label,
        file_count=file_count,
        line_count=line_count,
    )
    if submission.topic is None:
        console.print(
            "  [yellow]⚠[/yellow]  Тема задания не определена — возможен уточняющий вопрос.",
        )
        console.print()

    rendered_todos: set[str] = set()
    verbose_renderer: VerboseRenderer | None = None
    if output_mode == "verbose":
        verbose_renderer = VerboseRenderer(
            console=console,
            context_limit=config.context_limit,
            summarization_threshold=config.summarization_threshold,
        )

    def on_retry(attempt: int, max_attempts: int) -> None:
        console.print(
            f"[yellow]↻[/yellow] Повтор {attempt}/{max_attempts}: "
            "агент остановился раньше времени, продолжаю проверку...",
        )

    def on_todos_update(todos: list[dict[str, str]]) -> None:
        nonlocal rendered_todos
        rendered_todos = render_todo_progress(
            console,
            todos,
            last_rendered=rendered_todos,
        )

    def on_agent_event(event: AgentEvent) -> None:
        if verbose_renderer is not None:
            verbose_renderer.handle(event)

    def user_answer_callback(question: str) -> str:
        return render_user_question(
            console,
            question,
            show_panel=output_mode != "verbose",
        )

    orchestrator_error: OrchestratorError | None = None
    try:
        run_orchestrator(
            submission,
            workspace,
            config,
            on_todos_update=on_todos_update if output_mode == "compact" else None,
            on_agent_event=on_agent_event if output_mode == "verbose" else None,
            on_retry=on_retry,
            user_answer_callback=user_answer_callback,
        )
    except OrchestratorError as exc:
        orchestrator_error = exc

    if verbose_renderer is not None:
        console.print()
        verbose_renderer.on_complete()

    if orchestrator_error is not None:
        _fail(str(orchestrator_error))

    if validate_feedback_artifacts(workspace):
        logger.info("feedback sanitized against code-index")

    console.print()
    render_feedback_panel(console, workspace)

    if output_mode == "verbose":
        console.print(f"\n[dim]Workspace: {workspace.as_posix()}[/dim]")


def main() -> None:
    """Точка входа CLI."""
    app()


if __name__ == "__main__":
    main()
