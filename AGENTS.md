# llmaligner — implementation notes

Notes for coding agents (Codex, Claude Code) and humans picking up this repo.
Keep this file current when you change the design or finish a milestone.
Most of `../llmparser/AGENTS.md` (conventions, environment gotchas) applies here too.

## Goal

Align the **words** of two parsed versions of the same text (e.g. an Arabic
translation of Ephesians and its Greek Vorlage). Sentences (verses) are paired
by `sent_id`; links are Ugarit style (`3-5S` sure, `12-18P` probable); the
links feed a bilingual lexicon. All corpus and alignment data lives in
llmparser's `CorpusStore` and is reached by the agents through llmparser's MCP
server. The handoff brief is `INSTRUCTIONS.md`.

## Status (2026-10-14)

| Milestone | State |
|---|---|
| 1. Package set-up, `convert`, fixture tests | done, 100% covered |
| 2. `evaluate` (AER, P/R/F1) and `lexicon` | done, 100% covered |
| 3. Rules, precision measured on the 155 verses | done, 100% covered (see Rules below) |
| 4. Aligner agent, scorer, pipeline; small real run | |
| 5. Sphinx docs, AGENTS.md | |

The old implementation is in `llmalignerold/` (LangChain + retriv/chroma). It is
not imported.

## Layout

```
llmaligner/
  convert.py     # old YAML (both parses + alignment per verse) -> 2 CoNLL-U + JSONL alignment set
  evaluate.py    # P/R/F1 over sure and over all links, AER; per pair + micro total
  lexicon.py     # TranslationTable (lemma -> linked lemmas, one pass, leave-one-pair-out) + lexicon export
  rules.py       # code-only links: identical symbols, transliterated names, dominant lexicon match; measure()
  cli.py         # typer app: convert, evaluate, lexicon, rules, mcp (llmparser's mcp_app, reused as is)
tests/           # pytest; tests/data/sample.yaml = verses B10K1V1-3 of results/ArabicAligned.yaml
```

## Data

- `results/ArabicAligned.yaml` (untracked): 155 verses of Ephesians, Arabic
  (`ArabGr1-Arabic-Ephesians-Parsed`, with multiword tokens, MISC
  `Gloss=`/`Translit=`/`LTranslit=`/`Root=`) and Greek
  (`ArabGr1-GreekVorlage-Ephesians-Parsed`, PROIEL-style, unaccented forms,
  accented lemmas). `alignment` = old LLM output: **silver**, not gold.
- `uv run llmaligner convert results/ArabicAligned.yaml -o data/` writes
  `data/<corpus>.conllu` ×2 and `data/ArabicAligned.jsonl` (`/data/` is ignored).
  Silver totals: 2095 links (1967 S, 128 P); after conversion 2094 links in 155 pairs.
- Data quirks found by `convert`: 4 Arabic multiword lines have 9 columns
  (padded with `_`, reported); one silver link points to a missing word
  (`B10K2V16 16-16P`, dropped and reported); duplicate links are merged
  (first kept).
- The Greek side has **no punctuation tokens** (Arabic has 116 PUNCT), so a
  punctuation rule cannot fire on this text.

## Design decisions (and why)

- **Package**: uv + hatchling; llmparser by path (`[tool.uv.sources]`), because
  the PyPI name `llmparser` belongs to someone else.
- **`mcp serve` / `mcp config`** are llmparser's own typer sub-app
  (`llmparser.cli.mcp_app`) mounted under `llmaligner mcp`: same options
  (`--source`, `--alignment`, `--read-only`), and the Claude Desktop config
  runs `python -m llmparser mcp serve`, which is installed in this venv.
- **`convert`** writes JSONL directly (no store, no history sidecar): it is an
  import, not an edit. Links carry no confidence, so a read-only set gives them
  its default (1.0, or e.g. `:ro:0.8` in the alignment spec).
  Comments: `sent_id` = verse id, `text` (whitespace normalised), then the other
  fields (`verse = Ephesians 1:1`). Corpus A/B = the first two corpus keys of the
  first verse that has two.

- **Evaluation** (`evaluate.py`): A = predicted, S = gold sure, P = gold all.
  "sure" P/R/F1 compares predicted *sure* links with S; "all" compares A with P
  ignoring S/P; `AER = 1 − (|A∩S| + |A∩P|) / (|A| + |S|)`. Only gold pairs are
  scored (gold often covers part of a text); a gold pair missing from the
  predictions counts as empty; `--annotated-only` scores only pairs with
  predicted links; `--min-confidence` drops weak predicted links (links without
  a confidence are kept). Totals are micro-averaged. Empty denominators give 0.
  It reads the JSONL files directly: no sources needed.
- **Translation table** (`lexicon.TranslationTable`): same counting as
  llmparser's `translation_candidates` (lemma falls back to form;
  `min_confidence` on links), keyed by **source name** (not side), built in one
  pass, with per-pair counts so a pair can be left out (`exclude=(set, sent_id)`)
  — needed when measuring rules on the same data the table comes from. Code uses
  the table (calling `translation_candidates` per word is O(pairs) each); agents
  can still call the MCP tool.
- **Lexicon export** (`llmaligner lexicon -s ... -a ... [-o x.yaml|x.json]`):
  `{source: {lemma: {part_of_speech, occurrences, unaligned, alignments:
  {lemma: {count, part_of_speech}}}}}`; default `--min-confidence 0.8`. On the
  silver set it reproduces the old `results/ArabicLexicon.yaml` exactly (1138
  lemmas) except for the dropped `B10K2V16 16-16P` link (old code counted a link
  to a missing word as "aligned").

## Rules (no model)

`rules.py`; `llmaligner rules -s ... -a ... --target pred` applies them,
`--measure SET [--show-errors]` measures them. Rules only link words that have
no link yet, only 1-1, only when the match is unique in the pair, and write
sure links with confidence 0.95 (identical: 0.98), agent `rules`.

- **identical**: same form on both sides, unique on each side, and a symbol
  (UPOS PUNCT/NUM/SYM or no letters).
- **names**: one side PROPN, neither side a function word; consonant
  skeletons (romanise: NFD, strip marks, Greek → Latin; then drop vowels and
  y/w/h/j, merge consonant classes b/p/f/v/ph, t/d/th, k/g/q/c/kh, s/z; collapse
  doubles) of MISC `LTranslit`/`Translit`, lemma and form; skeletons shorter than
  3 must be equal, otherwise `SequenceMatcher` ≥ `name_similarity` (0.9); the
  best match must have no equal-or-better rival sharing one end.
- **lexicon**: from a `TranslationTable` over the evidence sets (default all),
  counting links ≥ `evidence_confidence` (0.96, above the rules' 0.95, so rules
  never feed themselves — the llmparser trick). Fires when the lemma's top
  translation has ≥ `min_count` (5) links and ≥ `min_share` (0.95) of **all**
  the lemma's occurrences, unlinked ones included (so mostly-unlinked words like
  the Greek article never fire), the lemma is unique in its sentence and the
  translation occurs exactly once (unlinked) in the other. Both directions.
  **The sentence under work is always left out of the evidence.**

**Measured** on the 155 Ephesians verses against the silver links, starting each
pair from no links, leave-one-out evidence (`--measure silver`):

| Rule | Links | In silver | Real precision (after reading the disagreements) |
|---|---|---|---|
| identical | 0 | – | – (the Greek has no punctuation) |
| names (threshold 0.9) | 20 | 18 | 20/20: both disagreements are silver errors (silver links Jesus↔Christ crosswise in B10K3V6, and Ἰησοῦ↔و in B10K3V21) |
| lexicon (5, 0.95) | 129 | 127 | 128/129: B10K4V29 لاكن→ἀλλ' is right (silver is wrong); B10K3V13 أنا "I" → μου "my" is wrong (pronoun lemmas cover every case) |

149 of the 2094 silver links (7%) are settled by rules at the start; the lexicon
rule grows as confident agent links accumulate. Settings tried: names at 0.8
added جسد "body" ~ χριστῷ (ǧasad vs khristo, 0.86) → threshold 0.9. Lexicon at
(3, 0.95): 198 links, same precision; at (3, 0.9): 229 links with 3 real errors
(ὑπό→مِن, مثل→ὡς, أنا→μου) ≈ 98.7%; at (5, 0.8): 265 links, 94.7% vs silver.
Kept llmparser's conservative (5, 0.95). **The silver set is noisy** (crossing
errors in "Jesus Christ"/"Christ Jesus"), so precision against silver is a
lower bound.

## Environment gotchas

- `uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13` (the
  uv-managed 3.12 is x86_64 and breaks `cryptography`).
- If `VIRTUAL_ENV` points at llmparser's venv (e.g. from the IDE), uv warns and
  ignores it; `unset VIRTUAL_ENV` to silence it.
- The test fixture YAML is dumped with escaped tabs (`"1\tبولس..."`), so edit
  it through `yaml.safe_load`, not with text replacement.

## Conventions

- `uv run pytest` must stay at **100% line+branch coverage**
  (`--cov-fail-under=100`) and fast. No network: `conftest.py` sets
  `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False`.
- New store/MCP functionality goes into llmparser (generic, tested at 100%),
  not here.
