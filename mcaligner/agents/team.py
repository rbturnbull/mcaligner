"""The pydantic-ai agents (aligner, scorer), sharing one MCP connection to the store."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mcparser.corpus import CorpusStore
from mcparser.pricing import estimate
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.usage import RunUsage, UsageLimits

from ..mcp import build_server
from ..settings import Settings
from .outputs import Alignment, Applier, Scores, TaskBatch
from .prompts import instructions
from .toolset import read_toolset

Answer = Alignment | Scores
USAGE_FIELDS = ("tasks", "requests", "input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens")


class ModelUsage(BaseModel):
    """Token use of one model over a run."""

    tasks: int = 0
    requests: int = 0
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = Field(None, description="Estimated US dollars (see mcparser.pricing).")

    def add(self, usage: RunUsage, model: str) -> None:
        self.tasks += 1
        self.requests += usage.requests
        self.input_tokens += usage.input_tokens
        self.cache_read_tokens += usage.cache_read_tokens
        self.cache_write_tokens += usage.cache_write_tokens
        self.output_tokens += usage.output_tokens
        self.cost = estimate(model, self.input_tokens, self.cache_read_tokens, self.cache_write_tokens, self.output_tokens)


class AlignerTeam:
    """Builds and runs the agents for one writable alignment set (``target``).

    By default the agents reach the store through an in-process MCP server;
    pass ``toolset`` to use another MCP connection. ``models`` maps a role (or
    ``"*"``) to a model name or instance, overriding the settings; tests use it
    for scripted models.
    """

    def __init__(
        self,
        store: CorpusStore,
        target: str,
        settings: Settings,
        models: Mapping[str, Model | str] | None = None,
        toolset: AbstractToolset[Any] | None = None,
    ):
        self.store = store
        self.target = target
        self.settings = settings
        self.models = dict(models or {})
        self.toolset = toolset or MCPToolset(build_server(store))
        self.applier = Applier(store)
        self._agents: dict[str, Agent[TaskBatch, Answer]] = {}
        self.usage: dict[str, ModelUsage] = {}
        """Token use and estimated cost per model."""

    def model(self, role: str) -> Model | str:
        return self.models.get(role) or self.models.get("*") or self.settings.model_for(role)

    @staticmethod
    def model_name(model: Model | str) -> str:
        return model if isinstance(model, str) else model.model_name

    def model_settings(self, role: str) -> ModelSettings:
        settings = ModelSettings(cache=self.settings.cache)
        thinking = self.settings.thinking_for(role)
        if thinking is not None:
            settings["thinking"] = thinking
        return settings

    def agent(self, role: str) -> Agent[TaskBatch, Answer]:
        if role not in self._agents:
            aset = self.store.alignment(self.target)
            agent = Agent(
                self.model(role),
                name=role,
                deps_type=TaskBatch,
                instructions=instructions(
                    role, aset.source_a.name, aset.source_b.name, self.target, self.settings.threshold,
                    self.settings.role(role).instructions,
                ),  # fmt: skip
                output_type=Alignment if role == "aligner" else Scores,
                toolsets=[read_toolset(self.toolset)],
                retries=3,
                model_settings=self.model_settings(role),
                defer_model_check=True,
            )
            apply = self.applier.alignment if role == "aligner" else self.applier.scores

            @agent.output_validator
            def check_and_apply(ctx: RunContext[TaskBatch], answer: Answer) -> Answer:
                return apply(answer, ctx.deps)  # type: ignore[arg-type]

            self._agents[role] = agent
        return self._agents[role]

    async def __aenter__(self) -> AlignerTeam:
        await self.toolset.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.toolset.__aexit__(*args)

    async def run(self, role: str, prompt: str, batch: TaskBatch) -> Answer:
        """Run ``role`` on a task; the answer is applied when it is accepted."""
        result = await self.agent(role).run(
            prompt, deps=batch, usage_limits=UsageLimits(request_limit=self.settings.request_limit)
        )
        name = self.model_name(self.model(role))
        self.usage.setdefault(name, ModelUsage()).add(result.usage, name)
        return result.output

    def total(self) -> ModelUsage:
        """Usage summed over all models (cost is None if any model has no price)."""
        total = ModelUsage(cost=0.0)
        for usage in self.usage.values():
            for name in USAGE_FIELDS:
                setattr(total, name, getattr(total, name) + getattr(usage, name))
            total.cost = None if total.cost is None or usage.cost is None else total.cost + usage.cost
        return total
