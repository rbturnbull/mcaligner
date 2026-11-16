"""Run settings: which model each agent uses, thresholds, batching and rules.

There are two agents: the **aligner** (links words; strong tier by default)
and the optional **scorer** (rates the aligner's links; efficient tier). The
tiers are a strong, an efficient and a light model, as in MCParser. Settings
can be loaded from YAML, e.g.::

    strong_model: anthropic:claude-opus-5-5
    efficient_model: anthropic:claude-sonnet-5-5
    light_model: anthropic:claude-haiku-5-5
    efficient_roles: [scorer]
    threshold: 0.8             # links below this are revisited
    rounds: 2
    batch_sentences: 5         # sentence pairs per agent task
    rules:
      min_count: 5
      min_share: 0.95
    roles:
      aligner:
        thinking: low
        instructions: Link Arabic clitic prepositions to the Greek preposition.
      scorer:
        enabled: false
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from .rules import RuleSettings

ROLES = ("aligner", "scorer")
DEFAULT_STRONG_MODEL = "anthropic:claude-opus-5-5"
DEFAULT_EFFICIENT_MODEL = "anthropic:claude-sonnet-5-5"
DEFAULT_LIGHT_MODEL = "anthropic:claude-haiku-5-5"
Tier = Literal["strong", "efficient", "light"]
THINKING_LEVELS = ("minimal", "low", "medium", "high", "xhigh")
Thinking = bool | Literal["minimal", "low", "medium", "high", "xhigh"]
"""Reasoning effort: ``False`` (off), ``True`` (provider default) or a level."""


def parse_thinking(value: str) -> Thinking:
    """Parse a command-line thinking value: off, on, or a level."""
    text = value.strip().lower()
    if text in ("off", "false", "no", "none"):
        return False
    if text in ("on", "true", "yes"):
        return True
    if text in THINKING_LEVELS:
        return text  # type: ignore[return-value]
    raise ValueError(f"Thinking must be off, on or one of {', '.join(THINKING_LEVELS)}; got {value!r}.")


def _known(names: list[str] | dict) -> list[str] | dict:
    unknown = set(names) - set(ROLES)
    if unknown:
        raise ValueError(f"Unknown roles {sorted(unknown)}; expected some of {list(ROLES)}.")
    return names


class RoleSettings(BaseModel):
    model: str | None = Field(None, description="Model for this role; overrides its tier.")
    thinking: Thinking | None = Field(None, description="Reasoning effort for this role; overrides its tier.")
    enabled: bool = Field(True, description="Run this role (the scorer can be switched off).")
    instructions: str | None = Field(None, description="Extra instructions appended to the role's prompt.")


COLUMNS = ("lemma", "upos", "xpos", "feats", "head", "deprel")
"""Word columns that can be shown in the prompt, in this order."""
DEFAULT_COLUMNS = ("lemma", "upos", "head", "deprel")
TOOL_NAMES = frozenset(
    {
        "get_parallel", "translation_candidates", "analyse_form", "find_tokens", "get_context",
        "similar_pairs", "lemma_links", "link_examples", "alignment_stats", "pair_words", "category_links",
    }
)  # fmt: skip
"""The read tools the agents may be given (see :mod:`mcaligner.mcp`)."""

GUIDELINES = Path(__file__).parent / "guidelines"
"""Bundled annotation guidelines (``<name>.md``)."""


def guideline_path(name: str) -> Path | None:
    """The file for a bundled guideline name or a path, or None."""
    for path in (GUIDELINES / f"{name}.md", Path(name).expanduser()):
        if path.is_file():
            return path
    return None


class Settings(BaseModel):
    strong_model: str = Field(DEFAULT_STRONG_MODEL, description="Model for the strong tier (the aligner).")
    efficient_model: str = Field(DEFAULT_EFFICIENT_MODEL, description="Model for the roles in efficient_roles.")
    light_model: str = Field(DEFAULT_LIGHT_MODEL, description="Model for the roles in light_roles.")
    efficient_roles: list[str] = Field(["scorer"], description="Roles that use efficient_model.")
    light_roles: list[str] = Field(default_factory=list, description="Roles that use light_model.")
    strong_thinking: Thinking | None = Field(None, description="Reasoning effort for strong roles; None = model default.")
    efficient_thinking: Thinking | None = Field(None, description="Reasoning effort for efficient roles.")
    light_thinking: Thinking | None = Field(None, description="Reasoning effort for light roles.")
    model: str | None = Field(None, description="If set, one model for every role (overrides the tiers).")
    threshold: float = Field(0.8, ge=0, le=1, description="Links below this confidence go back to the aligner.")
    rounds: int = Field(2, ge=1, description="Maximum number of align/score rounds.")
    concurrency: int = Field(1, ge=1, description="Agent tasks run at the same time.")
    request_limit: int = Field(30, ge=1, description="Maximum model requests per agent task.")
    cache: bool = Field(True, description="Use prompt caching (tool definitions, instructions, conversation).")
    batch_sentences: int = Field(5, ge=1, description="Maximum sentence pairs per agent task.")
    batch_words: int = Field(150, ge=1, description="Maximum words (both sides) per agent task; one pair may exceed it.")
    candidates: int = Field(3, ge=0, description="Translation candidates shown per unlinked word.")
    evidence_confidence: float = Field(0.8, ge=0, le=1, description="Links count as prompt evidence from this confidence.")
    misc_keys: list[str] = Field(["Gloss"], description="MISC attributes shown with each word (e.g. Gloss).")
    columns: list[str] = Field(
        list(DEFAULT_COLUMNS),
        description=f"Columns shown for each word after id and form ({', '.join(COLUMNS)}); [] shows only the forms.",
    )
    tools: list[str] | None = Field(
        None, description="Read tools the agents may call (default: all; [] for none; see TOOL_NAMES in settings.py)."
    )
    guidelines: str | None = Field(
        "grc-lat",
        description=(
            "Annotation guidelines added to the aligner's and scorer's instructions: the name of a bundled file "
            f"({', '.join(sorted(path.stem for path in GUIDELINES.glob('*.md')))}) or the path of a text file; null for none."
        ),
    )
    rules: RuleSettings = Field(default_factory=RuleSettings, description="When code links words without a model.")
    roles: dict[str, RoleSettings] = Field(default_factory=dict)

    @field_validator("columns")
    @classmethod
    def known_columns(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if name not in COLUMNS]
        if unknown:
            raise ValueError(f"Unknown columns {unknown}; expected some of {list(COLUMNS)}.")
        return [name for name in COLUMNS if name in value]

    @field_validator("tools")
    @classmethod
    def known_tools(cls, value: list[str] | None) -> list[str] | None:
        unknown = [name for name in value or [] if name not in TOOL_NAMES]
        if unknown:
            raise ValueError(f"Unknown tools {unknown}; expected some of {sorted(TOOL_NAMES)}.")
        return value

    @field_validator("guidelines")
    @classmethod
    def known_guidelines(cls, value: str | None) -> str | None:
        if value in (None, "", "none"):
            return None
        if guideline_path(value) is None:
            raise ValueError(f"No guidelines {value!r}: give a bundled name or the path of a file.")
        return value

    @property
    def guidelines_text(self) -> str | None:
        path = guideline_path(self.guidelines) if self.guidelines else None
        return path.read_text(encoding="utf-8").strip() if path else None

    @field_validator("roles", "efficient_roles", "light_roles")
    @classmethod
    def known_roles(cls, value: list[str] | dict) -> list[str] | dict:
        return _known(value)

    @classmethod
    def from_file(cls, path: Path | str) -> Settings:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.model_validate(data)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(exclude_none=True), sort_keys=False, allow_unicode=True)

    def role(self, name: str) -> RoleSettings:
        return self.roles.get(name, RoleSettings())

    def tier(self, name: str) -> Tier:
        if name in self.light_roles:
            return "light"
        return "efficient" if name in self.efficient_roles else "strong"

    def model_for(self, name: str) -> str:
        return self.role(name).model or self.model or getattr(self, f"{self.tier(name)}_model")

    def thinking_for(self, name: str) -> Thinking | None:
        override = self.role(name).thinking
        return override if override is not None else getattr(self, f"{self.tier(name)}_thinking")

    def enabled(self, name: str) -> bool:
        return self.role(name).enabled

    def with_overrides(self, model: str | None = None, role_models: dict[str, str | None] | None = None,
                       scorer: bool | None = None, link_punctuation: bool | None = None, **fields: object) -> Settings:
        """A copy with command-line overrides applied (``None`` values are ignored)."""
        updated = self.model_copy(deep=True, update={key: value for key, value in fields.items() if value is not None})
        if model:
            updated.model = model
        for name, role_model in (role_models or {}).items():
            if role_model:
                updated.roles.setdefault(name, RoleSettings()).model = role_model
        if scorer is not None:
            updated.roles.setdefault("scorer", RoleSettings()).enabled = scorer
        if link_punctuation is not None:
            updated.rules.link_punctuation = link_punctuation
        return Settings.model_validate(updated.model_dump())
