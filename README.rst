=========================
LLM Aligner
=========================

Word alignment of parallel texts (e.g. a translation and its source) with LLM
agents, built on MCParser's corpus store and MCP server (sibling repository
``../llmparser``).

Sentences are paired by ``sent_id``; word links are written Ugarit style
(``3-5S`` sure, ``12-18P`` probable). Code rules link the near-certain words,
an aligner agent links the rest in batches, an optional scorer rates its links,
and the result feeds a bilingual lexicon.

Full documentation: ``./mkdocs.sh`` and open ``docs/_build/html/index.html``.
Design notes for contributors: ``AGENTS.md``.

Installation
============

.. code-block:: bash

   uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13
   export ANTHROPIC_API_KEY=...

Usage
=====

.. code-block:: bash

   # old YAML (both parses + alignment per verse) -> CoNLL-U files + JSONL alignment set
   uv run mcaligner convert results/ArabicAligned.yaml -o data/

   SRC="-s ar=data/ArabGr1-Arabic-Ephesians-Parsed.conllu -s grc=data/ArabGr1-GreekVorlage-Ephesians-Parsed.conllu"

   # rules + aligner/scorer agents; prints tokens and estimated cost
   uv run mcaligner run $SRC -a silver=ar,grc,data/ArabicAligned.jsonl:ro \
       -a pred=ar,grc,out/pred.jsonl --target pred --max-sentences 5

   uv run mcaligner evaluate out/pred.jsonl gold.jsonl --annotated-only    # P/R/F1, AER
   uv run mcaligner lexicon $SRC -a pred=ar,grc,out/pred.jsonl -o lexicon.yaml
   uv run mcaligner rules $SRC -a silver=ar,grc,data/ArabicAligned.jsonl:ro --measure silver
   uv run mcaligner mcp config $SRC -a pred=ar,grc,out/pred.jsonl          # Claude Desktop

Development
===========

.. code-block:: bash

   uv run pytest      # 100% line and branch coverage required
