# MCP server

The agents use mcaligner's MCP server (`mcaligner.mcp`) in-process: MCParser's
server with alignment exploration tools added. The same server can be run for
Claude Desktop or other MCP clients:

```bash
uv run mcaligner mcp config -s ar=data/A.conllu -s grc=data/B.conllu \
    -a pred=ar,grc,out/pred.jsonl -a silver=ar,grc,data/silver.jsonl:ro
uv run mcaligner mcp serve ...    # stdio, or --transport streamable-http
```

`mcp config` prints the `mcpServers` entry for `claude_desktop_config.json`.
The alignment tools are `list_alignments`, `get_parallel`,
`translation_candidates`, `low_confidence_links`, `set_links` (with `dry_run`)
and `remove_links`, next to MCParser's monolingual tools (`analyse_form`,
`find_tokens`, ...). See MCParser's documentation for the full list.

## Exploration tools (mcaligner)

These read-only tools help decide how to align a pair. Pass `exclude_sentence`
with the pair being aligned so that its own links are not used as evidence.

| Tool | Answers |
|---|---|
| `similar_pairs` | Linked pairs sharing the most lemmas with a pair, and how those lemmas were linked there |
| `lemma_links` | Every occurrence of a lemma with its links, linked lemmas by count, and where it is unlinked |
| `link_examples` | Pairs where lemma A and lemma B are linked, and pairs where both occur but are not |
| `pair_words` | Every column (lemma, UPOS, XPOS, FEATS, head, deprel) of a pair's words, with the ids each is linked to |
| `category_links` | How words of a category (UPOS, XPOS, FEATS such as `Case=Gen`, deprel) are linked: partner UPOS, XPOS and lemmas, and how often they are unlinked |
| `alignment_stats` | Links (sure/probable), unlinked words, one-to-many words, crossings, confidence, agents; per pair or per set |

The aligner and scorer prompts show only lemma, UPOS, head and deprel; the agents fetch XPOS and FEATS with `pair_words` and
`category_links` when the grammar decides a link. They can call these tools as well as `get_parallel`,
`translation_candidates`, `analyse_form`, `find_tokens` and `get_context`.
