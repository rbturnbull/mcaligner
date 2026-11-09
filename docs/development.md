# Development

```bash
uv sync --all-groups --python /opt/homebrew/opt/python@3.13/bin/python3.13
uv run pytest        # 100% line and branch coverage required
./mkdocs.sh          # these docs (sphinx-build -W)
```

- Tests never call a real model: `pydantic_ai.models.ALLOW_MODEL_REQUESTS` is
  off in `tests/conftest.py`. The agents are tested with scripted
  `FunctionModel`s (`tests/scripted.py`), on three verses of Ephesians
  (`tests/data/sample.yaml`) and small synthetic sentence pairs.
- New store or MCP features belong in MCParser (generic, with tests), not here.
- Implementation notes, design decisions, measurements and environment gotchas
  are in `AGENTS.md` at the repository root.

## Layout

```text
llmaligner/
  convert.py    old YAML → CoNLL-U + JSONL
  lexicon.py    translation table, lexicon export
  rules.py      code-only links, precision measurement
  evaluate.py   P/R/F1, AER
  settings.py   models and run settings
  agents/       prompts, compact answers, read-only toolset, agent team
  pipeline.py   rules → align → score rounds
  cli.py        typer command line
```
