"""Registry of eval run configs → ReactRunner instances (E-6)."""

import logging
from pathlib import Path

import yaml
from langchain_core.tools import BaseTool

from app.agent.prompts import get_system_prompt
from app.agent.react_runner import ReactRunner
from app.agent.run_config import RunConfig, load_run_config
from app.core.config import Settings
from app.core.exceptions import ConfigNotFoundError

logger = logging.getLogger(__name__)


class AgentConfigRegistry:
    """Loads eval YAML configs and caches ReactRunner per config_id."""

    def __init__(
        self,
        settings: Settings,
        tools: list[BaseTool],
        configs_dir: Path,
    ) -> None:
        """Load YAML configs from disk and prepare runner cache."""
        self._settings = settings
        self._tools = tools
        self._configs_dir = configs_dir
        self._configs: dict[str, RunConfig] = {}
        self._runners: dict[str, ReactRunner] = {}
        self._default_runner = ReactRunner(settings, tools)
        self._load_configs()

    @property
    def default_runner(self) -> ReactRunner:
        """Production runner from environment settings (no config_id)."""
        return self._default_runner

    def list_config_ids(self) -> list[str]:
        """Return loaded config_id values."""
        return sorted(self._configs)

    def get_config(self, config_id: str) -> RunConfig:
        """Return validated config or raise KeyError."""
        try:
            return self._configs[config_id]
        except KeyError as exc:
            msg = f"Unknown config_id: {config_id}"
            raise KeyError(msg) from exc

    def get_runner(self, config_id: str) -> ReactRunner:
        """Return cached runner for config_id."""
        if config_id not in self._configs:
            msg = f"Unknown config_id: {config_id}"
            raise KeyError(msg)
        if config_id not in self._runners:
            config = self._configs[config_id]
            self._runners[config_id] = ReactRunner(
                self._settings,
                self._tools,
                model_name=config.model.name,
                temperature=config.model.temperature,
                system_prompt=get_system_prompt(config.prompt.name),
            )
            logger.info(
                "Created ReactRunner for config_id=%s model=%s prompt=%s",
                config_id,
                config.model.name,
                config.prompt.name,
            )
        return self._runners[config_id]

    def resolve_runner(self, config_id: str | None) -> tuple[ReactRunner, str | None, str]:
        """Pick runner; return (runner, config_id or None, model name for metadata)."""
        if config_id is None:
            return (
                self._default_runner,
                None,
                self._settings.openai_model,
            )
        try:
            config = self.get_config(config_id)
        except KeyError as exc:
            raise ConfigNotFoundError(str(exc)) from exc
        return (
            self.get_runner(config_id),
            config_id,
            config.model.name,
        )

    def _load_configs(self) -> None:
        if not self._configs_dir.is_dir():
            logger.warning("Eval configs directory missing: %s", self._configs_dir)
            return
        for path in sorted(self._configs_dir.glob("*.yaml")):
            if not _is_agent_run_config(path):
                logger.debug(
                    "Skipping non-agent config (different schema, e.g. indexer config): %s",
                    path,
                )
                continue
            try:
                config = load_run_config(path)
            except (OSError, TypeError, ValueError):
                logger.exception("Failed to load eval config: %s", path)
                continue
            self._configs[config.config_id] = config
            logger.info("Loaded eval config: %s", config.config_id)


def _is_agent_run_config(path: Path) -> bool:
    """Cheap pre-check for RunConfig shape.

    evals/configs/ also hosts non-RunConfig YAML (e.g. sprint-10 multimodal indexer
    configs), which share the directory but not the schema. Skipping them here avoids
    noisy ERROR tracebacks for files this registry was never meant to load.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return True  # let load_run_config raise and log the real error
    return isinstance(raw, dict) and "agent" in raw and "model" in raw
