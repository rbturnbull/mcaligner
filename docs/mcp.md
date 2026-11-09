# MCP server

The agents use MCParser's MCP server in-process. The same server can be run
for Claude Desktop or other MCP clients:

```bash
uv run llmaligner mcp config -s ar=data/A.conllu -s grc=data/B.conllu \
    -a pred=ar,grc,out/pred.jsonl -a silver=ar,grc,data/silver.jsonl:ro
uv run llmaligner mcp serve ...    # stdio, or --transport streamable-http
```

`mcp config` prints the `mcpServers` entry for `claude_desktop_config.json`.
The alignment tools are `list_alignments`, `get_parallel`,
`translation_candidates`, `low_confidence_links`, `set_links` (with `dry_run`)
and `remove_links`, next to MCParser's monolingual tools (`analyse_form`,
`find_tokens`, ...). See MCParser's documentation for the full list.
