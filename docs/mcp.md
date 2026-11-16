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
| `alignment_stats` | Links (sure/probable), unlinked words, one-to-many words, crossings, confidence, agents; per pair or per set |

The aligner and scorer agents can call these as well as `get_parallel`,
`translation_candidates`, `analyse_form`, `find_tokens` and `get_context`.
