# mcaligner

```{raw} html
<div style="display:flex;align-items:center;justify-content:center;gap:1.5rem;flex-wrap:wrap;margin:1rem 0 2rem">
  <img src="_static/mc.svg" alt="MCAligner logo: a rotating cube" width="160" height="160">
  <img class="only-light" src="_static/mcaligner-text.svg" alt="MCAligner, word alignment with LLM agents built on MCP" width="420">
  <img class="only-dark" src="_static/mcaligner-text-dark.svg" alt="MCAligner, word alignment with LLM agents built on MCP" width="420">
</div>
```

mcaligner aligns the **words** of two parsed versions of the same text, for
example an Arabic translation of Ephesians and its Greek source. Sentences
(here verses) are paired by `sent_id`, and each word link joins a word of
text A to a word of text B, written Ugarit style: `3-5S` (sure) or `12-18P`
(probable). The links feed a bilingual lexicon: which lemmas translate which.

```text
A.conllu + B.conllu (+ silver.jsonl)
                         │
                         ▼
              rules ──▶ aligner ──▶ scorer ──▶ rules ...   (run)
                         │
                         ▼
                   pred.jsonl ──evaluate──▶ P/R/F1, AER
                         └──lexicon──▶ lemma → aligned lemmas
```

It is built on [MCParser](https://github.com/rbturnbull/mcparser): the
sentences and the links live in MCParser's corpus store, and the agents reach
them through MCParser's [MCP](https://modelcontextprotocol.io) server. The
same server works from Claude Desktop (`mcaligner mcp config`).

Main features:

- **Code before models**: rules link identical symbols, transliterated proper
  names and words whose translation is overwhelming in the existing links,
  each measured for precision.
- **Batched, compact agent tasks**: several sentence pairs per task, one
  model request when the evidence in the prompt is enough, answers as short
  lines that code checks and applies.
- **A confidence and an author for every link**; links below a threshold go
  back to the aligner.
- **Model tiers** (default `anthropic:claude-opus-5-5` for the aligner, Sonnet
  5.5 for the scorer) with per-role overrides, prompt caching, and a token and
  cost report after every run.

```{toctree}
:maxdepth: 2
:caption: Guide

quickstart
preparing
data
rules
agents
evaluation
results
mcp
```

```{toctree}
:maxdepth: 1
:caption: Reference

_generated/cli
api
development
```

## Acknowledgements

The research leading to this software was conducted as part of the BICROSS project ('The Significance of Bilingual Manuscripts for Detecting
Cross-Language Interaction in the New Testament Tradition'), which has received funding from the European Research
Council (ERC) under the European Union's Horizon Europe Research and Innovation Programme (Grant Agreement
No. 101043730 – BICROSS – ERC-2021-COG). Funded by the European Union. Views and opinions expressed are however those
of the author only and do not necessarily reflect those of the European Union or the European Education and Culture
Executive Agency (EACEA). Neither the European Union nor EACEA can be held responsible for them.

Author: [Robert Turnbull](https://robturnbull.com) (Melbourne Data Analytics Platform, University of Melbourne).
Sister projects: [MCParser](https://github.com/rbturnbull/mcparser/) and [Hexapla](https://github.com/rbturnbull/hexapla/).
