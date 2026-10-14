=========================
LLM Aligner
=========================

Word alignment of parallel texts (e.g. a translation and its source) with LLM
agents, built on `llmparser <../llmparser>`_'s corpus store and MCP server.

Sentences are paired by ``sent_id``; word links are written Ugarit style
(``3-5S`` sure, ``12-18P`` probable). The alignments feed a bilingual lexicon.

Installation
============

.. code-block:: bash

   uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13

Usage
=====

.. code-block:: bash

   # old YAML (both parses + alignment per verse) -> CoNLL-U files + JSONL alignment set
   uv run llmaligner convert results/ArabicAligned.yaml -o data/

See ``uv run llmaligner --help``, the Sphinx docs in ``docs/`` and ``AGENTS.md``.
