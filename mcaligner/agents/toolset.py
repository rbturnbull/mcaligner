"""The MCP tools the agents see: read-only, with compact results.

Both agents answer with compact lines that code applies, so they only get read
tools. Results are rendered as short text, because every tool result is re-read
on each later model request: alignment results here, the monolingual tools with
MCParser's own compact renderings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from mcparser.agents.compact import compact_result
from mcparser.agents.roles import Role
from mcparser.corpus import parse_conllu
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool, WrapperToolset

from .prompts import word_lines

READ_TOOLS = frozenset(
    {
        "get_parallel",
        "translation_candidates",
        "analyse_form",
        "find_tokens",
        "get_context",
        "similar_pairs",
        "lemma_links",
        "link_examples",
        "alignment_stats",
        "pair_words",
        "category_links",
    }
)
"""Deliberately small: the task prompt already has the pairs, their links and the main evidence; the last six are mcaligner's exploration tools."""

LIST_ARGUMENTS = ("alignments", "sources")
"""List arguments that models sometimes send as a JSON string."""

ROLE = Role("aligner", "word alignment", ())
"""What MCParser's compact renderings need to know about the caller."""


def parallel_view(result: dict[str, Any]) -> str:
    a, b = parse_conllu(result["conllu_a"])[0], parse_conllu(result["conllu_b"])[0]
    confidence = result.get("confidence", {})
    links = " ".join(f"{link}:{confidence.get(link[:-1], 0):.2f}" for link in result["links"].split()) or "none"
    return "\n".join(
        [
            f"Pair {result['sent_id']} ({result['alignment']})",
            f"A ({result['source_a']}): {a.text}",
            *word_lines(a, ["Gloss"]),
            f"B ({result['source_b']}): {b.text}",
            *word_lines(b, ["Gloss"]),
            f"Links: {links}",
        ]
    )


def translations(result: dict[str, Any]) -> str:
    shown = ", ".join(f"{c['value']}×{c['count']}" for c in result["candidates"]) or "nothing"
    lines = [
        f"{result['lemma']} (side {result['side']}): {result['occurrences']} occurrences, "
        f"{result['unaligned']} unlinked. Linked to: {shown}."
    ]
    if result["examples"]:
        lines.append("Examples: " + "; ".join(result["examples"]))
    return "\n".join(lines)


def pair_words_view(result: dict[str, Any]) -> str:
    lines = [f"Pair {result['sent_id']} ({result['alignment']}): id form lemma UPOS XPOS FEATS head deprel -> linked ids"]
    for side in ("a", "b"):
        if side in result:
            lines.append(f"{side.upper()} ({result[side]['source']}):")
            lines += [
                f"{w['id']} {w['form']} {w['lemma']} {w['upos']} {w['xpos']} {w['feats']} {w['head']} {w['deprel']}"
                f" -> {','.join(w['linked']) or '-'}"
                for w in result[side]["words"]
            ]
    return "\n".join(lines)


def category_view(result: dict[str, Any]) -> str:
    filters = " ".join(f"{k}={v}" for k, v in result["filter"].items() if v)
    lines = [f"Words of side {result['side']} with {filters}: {result['occurrences']} occurrences, {result['unlinked']} unlinked."]
    for key in ("upos", "xpos", "lemma"):
        shown = ", ".join(f"{c['value']}×{c['count']}" for c in result[f"partner_{key}"]) or "nothing"
        lines.append(f"Linked to {key}: {shown}.")
    if result["examples"]:
        lines.append("Examples: " + "; ".join(result["examples"]))
    return "\n".join(lines)


FORMATTERS = {
    "get_parallel": parallel_view,
    "translation_candidates": translations,
    "pair_words": pair_words_view,
    "category_links": category_view,
}


def compact(name: str, result: Any) -> Any:
    formatter = FORMATTERS.get(name)
    if formatter is None:
        return compact_result(name, result, ROLE)
    try:
        return formatter(result)
    except (KeyError, TypeError, AttributeError, IndexError, ValueError):
        return result  # an unexpected shape is better shown in full than lost


@dataclass
class ReadToolset(WrapperToolset[Any]):
    """Only :data:`READ_TOOLS`, with list arguments repaired and results compacted."""

    async def get_tools(self, ctx: RunContext[Any]) -> dict[str, ToolsetTool[Any]]:
        tools = await self.wrapped.get_tools(ctx)
        return {name: tool for name, tool in tools.items() if name in READ_TOOLS}

    @staticmethod
    def normalise(args: dict[str, Any]) -> dict[str, Any]:
        """Accept list arguments sent as a JSON string (or a single name)."""
        fixed = dict(args)
        for key in LIST_ARGUMENTS:
            value = fixed.get(key)
            if isinstance(value, str):
                try:
                    decoded = json.loads(value)
                except json.JSONDecodeError:
                    decoded = [value]
                fixed[key] = decoded if isinstance(decoded, list) else [str(decoded)]
        return fixed

    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx: RunContext[Any], tool: ToolsetTool[Any]) -> Any:
        if name not in READ_TOOLS:
            raise ModelRetry(f"The tool {name!r} is not available; answer with your final result instead.")
        return compact(name, await self.wrapped.call_tool(name, self.normalise(tool_args), ctx, tool))


def read_toolset(toolset: AbstractToolset[Any]) -> ReadToolset:
    return ReadToolset(wrapped=toolset)
