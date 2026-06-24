"""Judge LLM factory for eval metrics (E-17)."""

from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING

from app.agent.run_config import JudgeConfigBlock
from deepeval.models.llms.openrouter_model import OpenRouterModel
from deepeval.models.llms.utils import trim_and_load_json

from scripts.langfuse_helpers import load_env_file

if TYPE_CHECKING:
    from pydantic import BaseModel


class SyncOpenRouterJudge(OpenRouterModel):
    """OpenRouter judge via sync OpenAI client — avoids asyncio event-loop noise."""

    def _generate(
        self,
        prompt: str,
        schema: BaseModel | None = None,
    ) -> tuple[str | BaseModel, float | None]:
        client = self.load_model(async_mode=False)
        messages = self._build_messages(prompt)

        if schema:
            try:
                completion = client.chat.completions.create(
                    model=self.name,
                    messages=messages,
                    response_format=self._schema_response_format(schema),
                    temperature=self.temperature,
                    **self.generation_kwargs,
                )
                json_output = trim_and_load_json(completion.choices[0].message.content)
                cost = self.calculate_cost(
                    completion.usage.prompt_tokens,
                    completion.usage.completion_tokens,
                    response=completion,
                )
                return schema.model_validate(json_output), cost
            except Exception as exc:
                warnings.warn(
                    f"Structured outputs not supported for model '{self.name}'. "
                    f"Falling back to regular generation with JSON parsing. "
                    f"Error: {exc!s}",
                    UserWarning,
                    stacklevel=3,
                )

        completion = client.chat.completions.create(
            model=self.name,
            messages=messages,
            temperature=self.temperature,
            **self.generation_kwargs,
        )
        output = completion.choices[0].message.content
        cost = self.calculate_cost(
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
            response=completion,
        )
        if schema:
            return schema.model_validate(trim_and_load_json(output)), cost
        return output, cost


def create_judge_model(judge: JudgeConfigBlock) -> SyncOpenRouterJudge:
    """Build DeepEval judge model via OpenRouter (project uses OPENAI_* env)."""
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        msg = "Missing OPENAI_API_KEY for judge (set in .env)"
        raise RuntimeError(msg)
    base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").strip()
    return SyncOpenRouterJudge(
        model=judge.name,
        api_key=api_key,
        base_url=base_url,
        temperature=judge.temperature,
    )


def require_openrouter_key() -> None:
    load_env_file()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        msg = "Missing OPENAI_API_KEY (set in .env)"
        raise RuntimeError(msg)
