"""Scripted pydantic-ai models for testing the agents without an LLM."""

from __future__ import annotations

import re
from collections.abc import Callable

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

PAIR = re.compile(r"^## Pair (\S+)$")
TO_SCORE = re.compile(r"^(\d+-\d+)[SP] ")

ToolCalls = list[tuple[str, dict]]


def prompt_of(messages: list[ModelMessage]) -> str:
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""


def pairs(prompt: str) -> list[str]:
    return [match.group(1) for line in prompt.splitlines() if (match := PAIR.match(line))]


def links_to_score(prompt: str) -> list[tuple[str, str]]:
    """``(sent_id, A-B)`` for every link listed under "Links to score"."""
    found, sent_id = [], None
    for line in prompt.splitlines():
        if header := PAIR.match(line):
            sent_id = header.group(1)
        elif match := TO_SCORE.match(line):
            found.append((sent_id, match.group(1)))
    return found


def scripted(answer: Callable[[str], dict], tools: Callable[[str], ToolCalls] | None = None) -> FunctionModel:
    """A model that optionally calls ``tools(prompt)`` once, then answers ``answer(prompt)``.

    Tool results and retry messages are recorded on the model (``.returns``,
    ``.retries``); after a retry the answer is sent again, so ``answer`` can
    depend on ``len(model.retries)``. ``.prompts`` collects the task prompts.
    """
    model: FunctionModel

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        last = messages[-1]
        prompt = prompt_of(messages)
        model.retries[:] = [
            str(part.content) for m in messages if isinstance(m, ModelRequest) for part in m.parts if isinstance(part, RetryPromptPart)
        ]
        first = isinstance(last, ModelRequest) and any(isinstance(p, UserPromptPart) for p in last.parts)
        if first:
            model.prompts.append(prompt)
            calls = tools(prompt) if tools is not None else []
            if calls:
                return ModelResponse(parts=[ToolCallPart(name, args) for name, args in calls])
        else:
            model.returns.extend(str(getattr(part, "content", "")) for part in last.parts)
        output = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(output.name, {"summary": "done", **answer(prompt)})])

    model = FunctionModel(respond)
    model.returns = []  # type: ignore[attr-defined]
    model.retries = []  # type: ignore[attr-defined]
    model.prompts = []  # type: ignore[attr-defined]
    return model


def align(*links: str) -> Callable[[str], dict]:
    """An aligner answer giving ``links`` ("A-B S 0.9") to every pair in the prompt."""

    def answer(prompt: str) -> dict:
        return {"links": "\n".join(f"{sent_id} {link}" for sent_id in pairs(prompt) for link in links)}

    return answer


def score(confidence: float | Callable[[str, str], float] = 0.9) -> Callable[[str], dict]:
    """A scorer answer rating every listed link."""

    def answer(prompt: str) -> dict:
        lines = [
            f"{sent_id} {key} {confidence(sent_id, key) if callable(confidence) else confidence}"
            for sent_id, key in links_to_score(prompt)
        ]
        return {"scores": "\n".join(lines)}

    return answer
