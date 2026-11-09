# llmaligner — implementation notes

Notes for coding agents (Codex, Claude Code) and humans picking up this repo.
Keep this file current when you change the design or finish a milestone.
Most of `../llmparser/AGENTS.md` (conventions, environment gotchas) applies here too.

## Goal

Align the **words** of two parsed versions of the same text (e.g. an Arabic
translation of Ephesians and its Greek Vorlage). Sentences (verses) are paired
by `sent_id`; links are Ugarit style (`3-5S` sure, `12-18P` probable); the
links feed a bilingual lexicon. All corpus and alignment data lives in
MCParser's `CorpusStore` and is reached by the agents through MCParser's MCP
server. The handoff brief is `INSTRUCTIONS.md`.

## Status (2026-10-14)

| Milestone | State |
|---|---|
| 1. Package set-up, `convert`, fixture tests | done, 100% covered |
| 2. `evaluate` (AER, P/R/F1) and `lexicon` | done, 100% covered |
| 3. Rules, precision measured on the 155 verses | done, 100% covered (see Rules below) |
| 4. Aligner agent, scorer, pipeline; small real run | done, 100% covered; 2 real 5-verse runs ($0.21, $0.18) |
| 5. Sphinx docs, AGENTS.md | done; `./mkdocs.sh` (`sphinx-build -E -W`) clean |

The old implementation is in `llmalignerold/` (LangChain + retriv/chroma). It is
not imported.

## Layout

```
llmaligner/
  convert.py     # old YAML (both parses + alignment per verse) -> 2 CoNLL-U + JSONL alignment set
  evaluate.py    # P/R/F1 over sure and over all links, AER; per pair + micro total
  lexicon.py     # TranslationTable (lemma -> linked lemmas, one pass, leave-one-pair-out) + lexicon export
  rules.py       # code-only links: identical symbols, transliterated names, dominant lexicon match; measure()
  settings.py    # Settings (YAML): tiers, per-role model/thinking/instructions/enabled, batching, rules
  agents/
    prompts.py   # instructions (aligner, scorer); compact pair blocks with settled/review links + evidence
    outputs.py   # Alignment/Scores answers (lines), parsing, Applier (dry-run set_links, then apply)
    toolset.py   # ReadToolset: 5 read MCP tools, JSON-string list args repaired, compact results
    team.py      # AlignerTeam: one pydantic-ai Agent per role over MCPToolset(build_server(store)); usage/cost
  pipeline.py    # rules -> align -> score -> rules rounds, batching, concurrency, RunReport
  cli.py         # typer app: convert, evaluate, lexicon, rules, run, settings, mcp (MCParser's mcp_app)
docs/            # Sphinx (myst-parser + furo); CLI page rendered from --help in conf.py
tests/           # pytest; tests/data/sample.yaml = verses B10K1V1-3 of results/ArabicAligned.yaml;
                 # tests/scripted.py = scripted FunctionModels (align(), score()) for agent tests
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

- **Package**: uv + hatchling; MCParser (package and CLI `mcparser`, formerly
  llmparser) by path from its repository `../llmparser`
  (`[tool.uv.sources] mcparser = { path = "../llmparser", editable = true }`).
- **`mcp serve` / `mcp config`** are MCParser's own typer sub-app
  (`mcparser.cli.mcp_app`) mounted under `llmaligner mcp`: same options
  (`--source`, `--alignment`, `--read-only`), and the Claude Desktop config
  runs `python -m mcparser mcp serve`, which is installed in this venv.
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
  MCParser's `translation_candidates` (lemma falls back to form;
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
  never feed themselves — the MCParser trick). Fires when the lemma's top
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
Kept MCParser's conservative (5, 0.95). **The silver set is noisy** (crossing
errors in "Jesus Christ"/"Christ Jesus"), so precision against silver is a
lower bound.

## Agents and pipeline

- **Two roles**: `aligner` (strong tier, Opus 5.5) and `scorer` (efficient
  tier, Sonnet 5.5; `--no-scorer` or `roles: {scorer: {enabled: false}}`).
  Per-role `model`, `thinking`, `instructions`; tiers and `model` as in MCParser.
- **Data access**: agents get only read MCP tools (`get_parallel`,
  `translation_candidates`, `analyse_form`, `find_tokens`, `get_context`)
  through `MCPToolset(build_server(store))`; answers are applied by code through
  the store (`set_links(dry_run=True)` for every pair, retry on any error, then
  `set_links`), as MCParser's Applier does. Results of the alignment tools
  are compacted here; the monolingual ones use MCParser's `compact_result`.
- **Aligner answer**: `links` lines `SENT_ID A-B S|P CONFIDENCE` (S/P may be
  attached: `3-5S`; missing = S) and `remove` lines `SENT_ID A-B`. New links of a
  pair = settled links (≥ threshold, shown in the prompt and kept) − removals +
  answer lines. Links to review that the answer omits are dropped. **Every pair
  of the task is written** (even unchanged), so the history shows the aligner
  saw it (`seen_by_aligner`).
- **Scorer answer**: `scores` lines `SENT_ID A-B CONFIDENCE`, only for the links
  listed to score; applied with `replace=False` (S/P kept).
- **Provenance** comes from MCParser's `Link.agent` (added for this project):
  rules write `rules`, the aligner `aligner`, the scorer `scorer`; an unchanged
  link keeps its agent. The scorer gets links whose agent is `aligner`. If the
  scorer gives the same confidence, the link stays `aligner`, so the pipeline
  also remembers `(sent_id, key, S/P, confidence)` it has rated (in memory).
- **Prompt** per pair: `id form lemma UPOS head deprel Gloss` lines (MISC keys
  in `misc_keys`), multiword tokens as `5-6 form (token of words 5-6)`, settled
  links and links to review with confidence and agent, and for each unlinked
  non-punctuation word the top `candidates` translations from a
  `TranslationTable` (links ≥ `evidence_confidence` 0.8, this sentence left
  out): `B10 Χριστός: مَسِيح×25, المسيح×11, يسوع×5 (of 43, 3 unlinked)`.
  Two Ephesians verses ≈ 5k characters.
- **Rounds**: rules; then per round align (unseen pairs + pairs with links <
  threshold), score, rules again (more evidence). Stop when no task, no pair's
  links changed (Ugarit text, ignoring confidences), nothing below threshold,
  or the round limit (default 2). Batches: ≤ `batch_sentences` (5) pairs and
  ≤ `batch_words` (150) words. A failing task is recorded and the run goes on;
  `UserError` (missing API key) aborts. Each run appends its report to
  `<set>.runs.jsonl`; `--report` writes it as JSON. Tokens and cost per model are
  printed (`mcparser.pricing.estimate`).

## Real-model observations (Opus 5.5 aligner, Sonnet 5.5 scorer)

Ephesians 1:1–5 (B10K1V1–5), evidence = silver **without those 5 verses**
(`data/silver-heldout.jsonl`), so neither the rules, the prompt evidence nor the
tools can see the answer. 2 rounds, batch 5. Evaluated against silver
(`evaluate --annotated-only`):

| Run | Cost | Requests | All P/R/F1 | AER | ≥0.8 links: P/R | below 0.8 |
|---|---|---|---|---|---|---|
| 1 | $0.21 (Opus $0.16) | 6 (1 per task) | 0.825/0.930/0.874 | 0.130 | 0.952/0.831 (62 links) | 18 of 80 |
| 2 (morpheme guidance) | $0.18 (Opus $0.14) | 6 | 0.835/0.930/0.880 | 0.124 | 0.892/0.817 (65 links) | 14 of 79 |

- Rules settled 13 of ~80 links (names 5, lexicon 8). No tool calls were made:
  the prompt evidence was enough, every task was a single request. ~1 minute.
- **Most "false positives" are right.** (1) Silver is wrong where Arabic has
  "Jesus Messiah" for Greek "Christ Jesus" (it links them crosswise); the
  aligner and the names rule get it right. (2) The Arabic parse does not split
  pronoun suffixes (ربنا "our Lord", باركنا "blessed us", اختارنا "chose us",
  هواه "his desire") or some prepositions (بكل "with all"); the aligner links
  these to ἡμῶν/ἡμᾶς/αὐτοῦ/πάσῃ (one-to-many), which silver mostly lacks.
  So precision against silver underestimates; a small gold set is needed.
- Run 1: the scorer rated those suffix links 0.3–0.4 ("doubtful or wrong"),
  so round 2 re-sent them, the aligner kept them, nothing improved. Run 2 added
  "a word may contain morphemes the parse did not split off" to both prompts:
  fewer links below threshold, but round 2 still changed 1 of 4 pairs both
  times for ~1/3 of the cost. **For large runs consider `--rounds 1`** (the
  scorer still sets confidences, e.g. for `lexicon --min-confidence`).
- Cache writes exceed reads in a run of 6 requests (writes cost 1.25× input);
  caching pays off on long runs where instructions and tool definitions repeat.

## MCParser additions (for this project)

- `Link.agent` (who last set or changed a link; unchanged links keep it;
  `get_parallel` returns `agents`), and `set_links` now copies the links it is
  given (it used to be able to mutate the caller's/stored `Link` objects).
- `dry_run` on the MCP `set_links` tool (the store method had it).

## Environment gotchas

- `uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13` (the
  uv-managed 3.12 is x86_64 and breaks `cryptography`).
- **MCParser was called llmparser** (2026-10-15 rename): the package and CLI are
  now `mcparser`, but the repository is still `../llmparser`. Imports are
  `from mcparser...`; the Claude Desktop config runs `python -m mcparser`. Older
  run reports and notes may still say llmparser.
- If `VIRTUAL_ENV` points at MCParser's venv (e.g. from the IDE), uv warns and
  ignores it; `unset VIRTUAL_ENV` to silence it.
- The test fixture YAML is dumped with escaped tabs (`"1\tبولس..."`), so edit
  it through `yaml.safe_load`, not with text replacement.

## Conventions

- Docs: `./mkdocs.sh` (= `uv run --group docs sphinx-build -E -W ...`). The
  CLI page is generated from `--help` (typer vendors click, so no sphinx-click);
  add new commands to `CLI_COMMANDS` in `docs/conf.py`.

- `uv run pytest` must stay at **100% line+branch coverage**
  (`--cov-fail-under=100`) and fast. No network: `conftest.py` sets
  `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False`.
- New store/MCP functionality goes into MCParser (generic, tested at 100%),
  not here.
- Raise `CorpusError` subclasses for expected failures; the CLI turns them
  (and `OSError`, pydantic `ValidationError`, pydantic-ai `UserError`) into
  `Error: ...` with exit status 1.

## Ideas / next steps

- A small hand-checked **gold** set (silver is noisy: Jesus/Christ crossings,
  missing suffix links), then tune threshold, rounds and rule settings on it.
- `--rounds 1` as the default if round 2 keeps changing little on larger runs.
- Anthropic Message Batches (50% off): most tasks are a single request.
- Many-to-one rules (e.g. Arabic suffixed pronoun → Greek pronoun when the
  host word is linked) once a gold set shows how often they hold.
- A per-lemma index in MCParser's `translation_candidates` if agents call it
  a lot on large sets (it scans all pairs per call).
