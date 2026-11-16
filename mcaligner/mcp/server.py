"""The MCP server for alignment: MCParser's tools plus the exploration tools of :mod:`.tools`."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from mcparser.corpus import CorpusStore
from mcparser.mcp import build_server as build_corpus_server
from mcparser.mcp.server import _guard
from pydantic import Field

from . import tools

INSTRUCTIONS = """

Alignment exploration (mcaligner): to decide how to align a pair, call
similar_pairs for verses with many of the same lemmas and see how they were
linked; lemma_links for every link of one lemma and its context; link_examples
for how one lemma pair was linked (or not) where both occur; alignment_stats
for link counts, unlinked words, crossings and confidence. Pass
exclude_sentence with the pair you are aligning so its own links are not used
as evidence. A lemma is the word's lemma, or its form if it has none.
"""

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

Alignment = Annotated[str, Field(description="Name of an alignment set (see list_alignments).")]
SentId = Annotated[str, Field(description="The sentence pair's sent_id.")]
Lemma = Annotated[str, Field(description="A lemma (or the form, if the word has no lemma).")]
MinConfidence = Annotated[float, Field(ge=0, le=1, description="Ignore links below this confidence.")]
Exclude = Annotated[str | None, Field(description='Skip this pair, as "sent_id" or "alignment:sent_id".')]


def build_server(
    store: CorpusStore,
    name: str = "mcaligner",
    allow_edits: bool = True,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "WARNING",
) -> MCPServer:
    """MCParser's server over ``store`` with the alignment tools added."""
    server = build_corpus_server(store, name=name, allow_edits=allow_edits, log_level=log_level)
    return add_tools(server, store)


def add_tools(server: MCPServer, store: CorpusStore) -> MCPServer:
    server._lowlevel_server.instructions = (server.instructions or "") + INSTRUCTIONS

    def tool(function: Callable[..., Any]) -> None:
        server.tool(annotations=READ)(_guard(function))

    @tool
    def similar_pairs(
        alignment: Alignment,
        sent_id: SentId,
        limit: Annotated[int, Field(ge=1, le=50)] = 5,
        min_confidence: MinConfidence = 0.0,
    ) -> dict[str, Any]:
        """Linked pairs sharing the most lemmas with this pair, with the shared lemmas and how they were linked."""
        return tools.similar_pairs(store, alignment, sent_id, limit, min_confidence)

    @tool
    def lemma_links(
        alignment: Alignment,
        lemma: Lemma,
        side: Annotated[Literal["a", "b"], Field(description="Which source the lemma belongs to.")] = "a",
        limit: Annotated[int, Field(ge=1, le=100)] = 20,
        min_confidence: MinConfidence = 0.0,
        exclude_sentence: Exclude = None,
    ) -> dict[str, Any]:
        """Every occurrence of a lemma in the linked pairs, with what it is linked to and its sentence."""
        return tools.lemma_links(store, alignment, lemma, side, limit, min_confidence, exclude_sentence)

    @tool
    def link_examples(
        alignment: Alignment,
        lemma_a: Lemma,
        lemma_b: Lemma,
        limit: Annotated[int, Field(ge=1, le=100)] = 10,
        min_confidence: MinConfidence = 0.0,
        exclude_sentence: Exclude = None,
    ) -> dict[str, Any]:
        """Pairs where lemma_a (source A) and lemma_b (source B) are linked, and pairs where both occur but are not."""
        return tools.link_examples(store, alignment, lemma_a, lemma_b, limit, min_confidence, exclude_sentence)

    @tool
    def alignment_stats(
        alignment: Alignment,
        sent_id: Annotated[str | None, Field(description="Omit for the whole set.")] = None,
        threshold: MinConfidence = 0.8,
    ) -> dict[str, Any]:
        """Links, sure/probable, unlinked words, one-to-many words, crossings, confidence and agents."""
        return tools.alignment_stats(store, alignment, sent_id, threshold)

    return server
