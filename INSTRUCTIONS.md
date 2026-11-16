# Instructions: rebuild mcaligner on top of MCParser

> Historical handoff brief. The `convert` command it describes has since been removed (see AGENTS.md).

You are working in the `mcaligner` repository. Rebuild it as a new package that
uses **MCParser** (the sibling repository `../llmparser`) as a dependency, and
reaches its data through MCParser's corpus store and MCP server.

Read these first:

- `../llmparser/AGENTS.md`: design decisions, conventions and environment gotchas
  (most apply here too).
- `../llmparser/docs/alignment.md`: the alignment support built for this project.
- `../llmparser/mcparser/corpus/alignment.py` and the alignment section at the
  end of `../llmparser/mcparser/corpus/store.py`.

## What mcaligner does

It aligns the **words** of two parsed versions of the same text, for example an
Arabic translation of Ephesians (`ArabGr1-Arabic-Ephesians-Parsed`) and its Greek
source (`ArabGr1-GreekVorlage-Ephesians-Parsed`). Sentences (here verses) are
paired by id. Each word link joins a word id in text A to a word id in text B,
in the Ugarit style `3-5S` (S = sure) or `12-18P` (P = probable). One-to-many
and many-to-many alignments are written as several links. The output is used to
build a bilingual lexicon (which lemmas translate which).

## The old code

The old code is in `llmalignerold/`. Reuse its ideas, but do not import it.

- `align.py` + `prompt.py`: one LangChain prompt per verse with retrieved
  example verses; the LLM returns a Ugarit string.
- `lexicon.py`: builds lemma → aligned-lemma counts from the alignments.
- `database/`: retriv/chroma retrieval. Do not reuse it; MCParser has search.
- Data: `results/ArabicAligned.yaml` (untracked) holds 155 verses. Each verse has
  the CoNLL-U of both texts and an `alignment` string produced by the old LLM
  run. It is silver data, not gold. `results/ArabicLexicon.yaml` is the old
  lexicon.

## Requirements (from the project owner)

- **uv** for packaging, **typer** for the CLI, **pydantic-ai** for agents.
- All data access by the agents goes through **MCParser's MCP server**
  (in-process via `pydantic_ai.mcp.MCPToolset(build_server(store))`).
- **Fast tests with 100% line and branch coverage**, enforced with
  `--cov-fail-under=100`. No network in tests: use pydantic-ai `FunctionModel`
  scripted models (see `../llmparser/tests/scripted.py`) and set
  `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` in `conftest.py`.
- **Sphinx docs** (myst-parser + furo, as in `../llmparser/docs`), built cleanly
  with `-W`.
- Keep an `AGENTS.md` with implementation notes, and a `CLAUDE.md` containing
  `@AGENTS.md`.
- Cost matters: the owner will run thousands of sentences. Follow MCParser's
  approach:
  - code-only rules before models;
  - batches of several sentence pairs per task;
  - one model request per task, with compact line answers that code checks and
    applies;
  - model tiers (default `anthropic:claude-opus-5-5`, with Sonnet 5.5 and Haiku
    5.5 tiers) and per-role overrides;
  - prompt caching;
  - a token and cost report after every run (reuse `mcparser.pricing.estimate`).
- If the aligner needs new store or MCP functionality, **add it to MCParser**
  (with tests at 100%), not here, and keep it generic. Then use it from here.

## Set up the package

1. Create a new `pyproject.toml` (hatchling build backend; the package lives in
   `mcaligner/`; a `mcaligner` script pointing to `mcaligner.cli:app`). Depend
   on MCParser (package `mcparser`) by path, from its repository `../llmparser`
   (MCParser was called mcparser before; that PyPI name belongs to someone else):

   ```toml
   [project]
   dependencies = ["mcparser", "pydantic-ai-slim[anthropic,mcp]", "typer", "pyyaml"]

   [tool.uv.sources]
   mcparser = { path = "../llmparser", editable = true }

   [dependency-groups]
   dev = ["pytest>=8", "pytest-cov>=5"]
   docs = ["sphinx>=8", "myst-parser>=4", "furo>=2024.8.6"]
   ```

2. Pin Python 3.13 in `.python-version`. On this machine the uv-managed 3.12 is
   x86_64 and breaks `cryptography`; use
   `uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13`.
3. Remove the old `.venv`, `htmlcov`, `.coverage` and `.pytest_cache`. They are
   from the Poetry setup.

## What MCParser already provides

```python
from mcparser.corpus import CorpusStore
from mcparser.mcp import build_server, AlignmentSpec, SourceSpec, load_store

store = CorpusStore()
store.add_source("ar", "data/arabic.conllu")              # read-only by default
store.add_source("grc", "data/greek.conllu")
store.add_alignment("verses", "ar", "grc", "out/verses.jsonl")        # writable, created on first save
store.add_alignment("gold", "ar", "grc", "gold/verses.jsonl", mode="ro")
```

Store methods (all of them are also MCP tools):

| Method / tool | Purpose |
|---|---|
| `list_alignments()` | sets, their two sources, mode, size |
| `get_parallel(alignment, sent_id)` | both sentences as CoNLL-U, links (`"1-2S 3-5P"`), per-link confidence, unlinked word ids on each side |
| `set_links(alignment, sent_id, links, confidence=None, replace=True, reason="", agent=..., dry_run=False)` | set or add links; checks that word ids exist in both sentences; `dry_run` checks without writing |
| `remove_links(alignment, sent_id, "1-2 3-5")` | remove links |
| `translation_candidates(lemma, side="a"\|"b", alignments=None, loose=False, min_confidence=0.0, exclude_sentence=None)` | which lemmas this lemma is linked to, with counts, unaligned occurrences and examples; this is the lexicon |
| `low_confidence_links(alignment, threshold)` | links to revisit |

Also useful:
- the monolingual tools: `analyse_form`, `find_tokens` (`suffix=`,
  `previous_form=`), `find_arcs`, `relation_stats`, `get_sentence`;
- `parse_ugarit` / `format_ugarit` in `mcparser.corpus.alignment`.

The alignment file is JSON Lines, one pair per line:
`{"sent_id": ..., "links": [{"source": "1", "target": "2", "sure": true, "confidence": 0.9}]}`.
Every edit is appended to `<file>.history.jsonl`.

Patterns worth copying, not importing:
- `mcparser/agents/toolset.py`: restricting the tools each agent sees;
- `mcparser/agents/outputs.py`: compact answers validated and applied in an
  output validator, with errors sent back as `ModelRetry`;
- `mcparser/pipeline.py`: rounds, batching, concurrency, the run report;
- `mcparser/rules.py`: code-only rules with a minimum count and share;
- `mcparser/settings.py`: model tiers and YAML settings.

## Proposed design

1. **`mcaligner convert results/ArabicAligned.yaml -o data/`** writes
   `data/<corpus A>.conllu`, `data/<corpus B>.conllu` (one sentence per verse,
   `sent_id` = verse id, with `# text` and the other fields as comments) and
   `data/<name>.jsonl` with the old alignments. Use them as a silver read-only
   set, or as the starting point of a writable one.
2. **Rules (no model).** Use them to link what is near-certain:
   - identical punctuation and numerals;
   - proper names whose transliterations match (the Arabic MISC has
     `Translit=`; the Greek has lemmas);
   - pairs where a lemma's `translation_candidates` from trusted or confident
     links are overwhelming (at least N examples and ≥ 95% agreement), and the
     candidate is the only possible match in the other sentence.
   
   Measure the precision of every rule on the data before relying on it, as
   MCParser does.
3. **Aligner agent.** It works on batches of sentence pairs. Its prompt gives
   both sentences (compact CoNLL-U), the links that are already settled, and for
   each unlinked word its top `translation_candidates`. The answer has one line
   per link, `SENT_ID A-B S|P CONFIDENCE`, which code checks and applies through
   `set_links(..., dry_run=True)` and then `set_links(...)`. It may call the read
   tools for more evidence. Run it on Opus by default.
4. **Scorer.** Optional; Sonnet by default. It rates links the model made, and
   low-confidence links go back to the aligner in the next round.
5. **Evaluation: `mcaligner evaluate PRED GOLD`.** Report precision, recall and
   F1 over sure links and over sure+probable links, plus the alignment error
   rate:
   `AER = 1 − (|A∩S| + |A∩P|) / (|A| + |S|)`, where A = predicted links,
   S = gold sure links, P = gold sure+probable links. Make it per sentence and
   overall, with `--annotated-only` semantics like MCParser.
6. **Lexicon export: `mcaligner lexicon`.** Writes lemma → aligned lemmas (with
   counts and POS) from the confident links, like the old `lexicon.py` but built
   from the store.
7. **CLI** with `convert`, `run` (`--max-sentences`, `--rounds`, `--concurrency`,
   tier and model options, `--report`), `evaluate`, `lexicon`, and `mcp serve` /
   `mcp config`. The last two can call MCParser's `build_server` /
   `claude_desktop_config` with `--source` and `--alignment` options.

## Milestones

1. Package set-up, `convert`, and tests on a small fixture: 3 verses copied from
   `results/ArabicAligned.yaml` into `tests/data/`.
2. `evaluate` (AER, P/R/F1) and `lexicon`.
3. Rules, with their precision measured on the 155 verses against the silver
   links, and reported in `AGENTS.md`.
4. Aligner agent, scorer and pipeline with scripted-model tests. Then one small
   real run (about 5 verses, `--max-sentences`), reporting tokens and cost.
5. Sphinx docs and `AGENTS.md`.

Ask the owner before spending more than a couple of dollars on real model runs.
Each run's cost is printed at the end.

## Gotchas (from MCParser)

- **mcp is 2.x.** `FastMCP` is now `mcp.server.MCPServer`. Raise
  `mcp.server.mcpserver.exceptions.ToolError` for messages the model should see.
  `mcp.Client(server)` connects in-process in tests.
- **pydantic-ai 2.x.**
  - `result.usage` is a property, not a method.
  - Build agents with `defer_model_check=True`, so tests do not need an API key.
  - Models sometimes send a list argument as a JSON string; accept both.
- **Logging.** `MCPServer(log_level=...)` configures the root logger.
  MCParser's `build_server` defaults to WARNING; keep it, or every HTTP request
  is logged.
- **Docs.** typer vendors its own click, so sphinx-click cannot document the
  CLI. MCParser's `docs/conf.py` instead renders `--help` output into
  `docs/_generated/cli.md`; copy that approach.
- **API key and tests.** `ANTHROPIC_API_KEY` is set on the owner's machine,
  which is why the tests must disable model requests.
