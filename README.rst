|logo| |text|

.. |logo| image:: https://raw.githubusercontent.com/rbturnbull/mcaligner/main/docs/_static/mc.svg
   :alt: MCAligner logo
   :height: 220px
   :align: middle

.. |text| image:: https://raw.githubusercontent.com/rbturnbull/mcaligner/main/docs/_static/mcaligner-text.svg
   :alt: MCAligner
   :height: 220px
   :align: middle

=========================
MCAligner
=========================

.. image:: https://github.com/rbturnbull/mcaligner/actions/workflows/testing.yml/badge.svg
   :target: https://github.com/rbturnbull/mcaligner/actions/workflows/testing.yml
   :alt: Tests

.. image:: https://img.shields.io/badge/license-Apache%202.0-blue.svg
   :target: https://github.com/rbturnbull/mcaligner/blob/main/LICENSE
   :alt: Apache 2.0 licence

**Word alignment of parallel texts with a team of LLM agents.** MCAligner links the words of two parsed
versions of the same text, such as a translation and its source, and writes the links in the Ugarit style
(``3-5S`` sure, ``12-18P`` probable). The links can feed a bilingual lexicon.

Code rules settle the near-certain words (identical symbols, transliterated names, words whose translation is
overwhelming in the links so far). An **aligner** agent links the rest in batches, an optional **scorer** gives
every link a confidence, and weak links go back for another round. Every link records which agent made it. All
access to the texts goes through the `MCP <https://modelcontextprotocol.io>`_ server of
`MCParser <https://github.com/rbturnbull/mcparser>`_, which also prepares the parsed files, so the same tools
work from Claude Desktop.

.. warning::

   This is an **alpha** release. The commands and file formats may change. Only the Greek-Latin
   guidelines have been validated against human alignments (see Results); the others are drafts.

Installation
============

Python 3.11 or later.

.. code-block:: bash

   pip install --pre mcaligner       # installs MCParser too
   export ANTHROPIC_API_KEY=...      # the key for the models you use
   mcaligner --version

To work from a clone: ``uv sync`` and prefix the commands with ``uv run``.

Quick start
===========

**1. Prepare two CoNLL-U files with MCParser.** MCAligner needs both texts parsed, with the same ``sent_id``
(for example a verse or a fragment) on both sides. MCParser turns raw text into CoNLL-U using a treebank you
trust as the examples:

.. code-block:: bash

   mcparser init john-grc.yaml -o john-grc.conllu -s grc=proiel-grc-train.conllu
   mcparser run  john-grc.conllu -s grc=proiel-grc-train.conllu --cheap-first
   # the same for the other language

The input is one sentence per line or YAML mapping ids to ``text``. See
`Preparing files with MCParser <docs/preparing.md>`_ and
`MCParser's documentation <https://rbturnbull.github.io/mcparser>`_.

**2. Align.**

.. code-block:: bash

   mcaligner run -s grc=john-grc.conllu -s cop=john-cop.conllu \
       -a pred=grc,cop,john-aligned.jsonl --target pred --guidelines grc-cop

Try ``--max-sentences 5`` first: the run prints the tokens and estimated cost per model. A run can be repeated to
continue where it stopped.

**3. Evaluate and export.**

.. code-block:: bash

   mcaligner evaluate john-aligned.jsonl gold.jsonl                  # P/R/F1 and AER
   mcaligner lexicon -s grc=... -s cop=... -a pred=grc,cop,john-aligned.jsonl -o lexicon.yaml
   mcaligner mcp config -s grc=... -s cop=... -a pred=grc,cop,john-aligned.jsonl   # Claude Desktop

Alignments are JSON Lines; ``mcparser align import`` and ``mcparser align export`` convert to and from
Pharaoh/Ugarit text and YAML.

Guidelines
==========

The agents are given annotation guidelines, and these matter more than anything else we tested.
``--guidelines`` takes a bundled name (``grc-lat`` the default, ``bicross``, ``grc-cop``, ``grc-ar``, ``lat-ar``,
``grc-syr``, ``syr-ar``, ``got-lat``), the path of your own file, or ``none``.

Results
=======

On held-out tests (cold start, Opus aligner, Sonnet scorer, two rounds):

==========================================  ==========  ===========  =====
Test set                                    F1 (links)  AER          Cost
==========================================  ==========  ===========  =====
BICROSS Greek-Latin, 79 verses, Kreinecker  0.947       0.053        $2.64
BICROSS, against Tilke                      0.975       0.025        $2.64
DFHG Greek-Latin, 80 fragments              0.922       0.042        $2.34
==========================================  ==========  ===========  =====

The two BICROSS annotators agree with each other at F1 0.946 (AER 0.054), and the DFHG annotators at about 0.927,
so the pipeline is at the level of human agreement on both. Details, caveats and ablations (the parse columns do
not help; the guidelines do) are in `docs/results.md <docs/results.md>`_.

Documentation
=============

Full documentation: https://rbturnbull.github.io/mcaligner, or ``./mkdocs.sh`` and open
``docs/_build/html/index.html``. Design notes for contributors: ``AGENTS.md``; see also ``CONTRIBUTING.md``.

Development
===========

.. code-block:: bash

   uv sync --all-groups
   uv run pytest      # 100% line and branch coverage required, no network
