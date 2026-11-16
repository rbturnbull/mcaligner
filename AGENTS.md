# mcaligner — implementation notes

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
| 1. Package set-up, fixture tests (`convert` has since been removed) | done, 100% covered |
| 2. `evaluate` (AER, P/R/F1) and `lexicon` | done, 100% covered |
| 3. Rules, precision measured on the 155 verses | done, 100% covered (see Rules below) |
| 4. Aligner agent, scorer, pipeline; small real run | done, 100% covered; 2 real 5-verse runs ($0.21, $0.18) |
| 5. Sphinx docs, AGENTS.md | done; `./mkdocs.sh` (`sphinx-build -E -W`) clean |

The old implementation is in `llmalignerold/` (LangChain + retriv/chroma). It is
not imported.

## Layout

```
mcaligner/
  evaluate.py    # P/R/F1 over sure and over all links, AER; per pair + micro total
  lexicon.py     # TranslationTable (lemma -> linked lemmas, one pass, leave-one-pair-out) + lexicon export
  guidelines/    # bundled annotation guidelines (grc-lat.md, bicross.md), added to the agents' instructions (setting `guidelines`, default grc-lat)
  rules.py       # code-only links: identical symbols, transliterated names, dominant lexicon match; measure()
  settings.py    # Settings (YAML): tiers, per-role model/thinking/instructions/enabled, batching, rules
  agents/
    prompts.py   # instructions (aligner, scorer); compact pair blocks with settled/review links + evidence
    outputs.py   # Alignment/Scores answers (lines), parsing, Applier (dry-run set_links, then apply)
    toolset.py   # ReadToolset: 5 read MCP tools, JSON-string list args repaired, compact results
    team.py      # AlignerTeam: one pydantic-ai Agent per role over MCPToolset(build_server(store)); usage/cost
  mcp/           # tools.py (similar_pairs, lemma_links, link_examples, pair_words, category_links, alignment_stats), server.py (MCParser's server + these), cli.py (mcp serve/config)
  pipeline.py    # rules -> align -> score -> rules rounds, batching, concurrency, RunReport
  cli.py         # typer app: evaluate, lexicon, rules, run, settings, mcp (MCParser's mcp_app)
docs/            # Sphinx (myst-parser + furo); CLI page rendered from --help in conf.py
tests/           # pytest; tests/data/{ar,grc}.conllu + silver.jsonl = verses B10K1V1-3 of results/ArabicAligned.yaml;
                 # tests/scripted.py = scripted FunctionModels (align(), score()) for agent tests
```

## Data

- `results/ArabicAligned.yaml` (untracked): 155 verses of Ephesians, Arabic
  (`ArabGr1-Arabic-Ephesians-Parsed`, with multiword tokens, MISC
  `Gloss=`/`Translit=`/`LTranslit=`/`Root=`) and Greek
  (`ArabGr1-GreekVorlage-Ephesians-Parsed`, PROIEL-style, unaccented forms,
  accented lemmas). `alignment` = old LLM output: **silver**, not gold.
- It was split once (by a `convert` command that has been removed, along with
  its code) into `data/<corpus>.conllu` ×2 and `data/ArabicAligned.jsonl`
  (`/data/` is ignored; keep them, they cannot be regenerated from the repo).
  Silver totals: 2095 links (1967 S, 128 P); in the split 2094 links in 155 pairs.
- Data quirks found then: 4 Arabic multiword lines had 9 columns (padded with
  `_`); one silver link pointed to a missing word (`B10K2V16 16-16P`, dropped);
  duplicate links were merged (first kept).
- The Greek side has **no punctuation tokens** (Arabic has 116 PUNCT), so a
  punctuation rule cannot fire on this text.

## Design decisions (and why)

- **Package**: uv + hatchling; MCParser (package and CLI `mcparser`, formerly
  llmparser) from PyPI (`mcparser>=0.2.0a1`, a pre-release, hence
  `[tool.uv] prerelease = "allow"`). To develop against the local repository
  `../llmparser` add `[tool.uv.sources] mcparser = { path = "../llmparser", editable = true }`.
- **`mcp serve` / `mcp config`** are `mcaligner/mcp/cli.py`: MCParser's options
  (reusing its typer option types) over `mcaligner.mcp.build_server`, which
  is MCParser's server plus the exploration tools; the Claude Desktop config
  runs `python -m mcaligner mcp serve`.
- **Alignment files** are MCParser's JSON Lines sets. Imported links carry no
  confidence, so a read-only set gives them its default (1.0, or e.g. `:ro:0.8`
  in the alignment spec). `mcparser align import/export` (MCParser, after 0.2.0a1)
  converts to and from Pharaoh/Ugarit text and YAML.

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
- **Lexicon export** (`mcaligner lexicon -s ... -a ... [-o x.yaml|x.json]`):
  `{source: {lemma: {part_of_speech, occurrences, unaligned, alignments:
  {lemma: {count, part_of_speech}}}}}`; default `--min-confidence 0.8`. On the
  silver set it reproduces the old `results/ArabicLexicon.yaml` exactly (1138
  lemmas) except for the dropped `B10K2V16 16-16P` link (old code counted a link
  to a missing word as "aligned").

## Greek-Latin gold standard

`/Users/rturnbull/MDAP/BICROSS/Alignment/Alignment-Gold-Standards/grc-lat`: 100 DFHG
fragments (raw text only, 1983 grc / 1860 lat tokens, 1593 links, 0-based Ugarit).
Workflow: `mcparser init grc.txt -o grc.conllu` (and lat), parse with the PROIEL
treebanks (`UD/UD_Ancient_Greek-PROIEL`, `UD/UD_Latin-PROIEL`), then
`uv run python scripts/grc_lat_gold.py GOLD.json grc.conllu lat.conllu -o gold.jsonl` (a disposable script, not part of the package) maps each
gold token to the parsed words covering the same characters (a link goes to every
overlapping word), so it survives tokenisation differences. `init` only detaches `«` and the
full stop of `rep.` (3 fragments: grc 64, lat 26, lat 64; 1593 -> 1597 links). Work files are in `data/grc-lat/`.
Do not let a parser change the segmentation after the gold is mapped.

### Greek-Latin DFHG dev set (20 fragments; `data/grc-lat/`)

Dev ids in `dev-ids.txt` (stratified by length, seed 42; `scripts/grc_lat_split.py`); gold-dev 313 links.
Parses: grc $17.74, lat $16.83 (cheap-first, syntax on Opus, 3 rounds; the PROIEL treebanks as examples).
Cold start (no evidence sets), 2 rounds, Opus aligner + Sonnet scorer, evaluated against gold-dev:

| Run | Cost | Requests | All P/R/F1 | AER |
|---|---|---|---|---|
| 1 (old prompt) | $0.84 | 34 | 0.889/0.869/0.879 | 0.088 |
| 2 (old prompt; run-to-run noise) | $0.58 | 36 | 0.886/0.866/0.876 | 0.089 |
| 3 (ids fixed, see below) | $0.60 | 23 | 0.895/0.869/0.882 | 0.083 |
| 3 without its 15 punctuation links (post-hoc) | – | – | 0.941/0.869/0.904 | 0.058 |
| 4 (+ guidelines in the prompts, punctuation dropped in code) | $0.77 | 22 | 0.955/0.885/0.919 | 0.044 |

- The prompt's answer example used an Ephesians id (`B10K1V1`), so models wrote `B98` for pair `98` and were
  retried (15 of 36 requests). The examples are now `<id>` and the task header lists the ids: 1 retry in run 3.
- `TaskResult.details` (requests, tool calls by name, retry messages) is in the report. Almost no tool calls were
  made (1 `pair_words` in run 3, none in the others): the prompt evidence is enough.
- Error analysis (pairs 80, 43, 60, 96, 84): (1) the aligner links punctuation (`,`~`,`, `«`~`«`), which the guidelines
  forbid; (2) links the guidelines rule out (`τούτου`~`Sabinorum`, `τῇ`~`libro`, an article to `filius`); (3) misses
  particle groups (`ἔτι δὲ καὶ`~`nec non`) and crossed pairs (`τότε πρῶτον`~`tunc demum`); (4) the names rule's wrong
  `Ἡφαίστου`~`festi` (0.95) where `Vulcani` is right. Done in run 4: `mcaligner/guidelines/grc-lat.md` (a condensed version, from `../guidelines/grc-lat.md`) is in the
  aligner's and scorer's instructions by default (`guidelines`), and links to punctuation are dropped in code
  (`rules.link_punctuation`); the model made 0 such links with the guidelines. Human-human on the DFHG gold:
  Dice 0.927 (from the README's flattened counts 1487/1486, 1378 agreed); BICROSS NT annotators: 0.948.
  The dev set was used to choose these changes, so confirm on the 80 test fragments before quoting a number.

**Column ablation** (same 20 dev pairs; guidelines, punctuation filter, rules, models and `--tools none` fixed; only
`--columns` varies; one run each; `data/grc-lat/ablation/`; F1 over all links, 95% bootstrap over the 20 pairs):

| Columns shown | Cost | F1 | AER |
|---|---|---|---|
| forms only (no parse) | $0.40 | 0.912 [0.881, 0.944] | 0.053 |
| lemma upos | $0.48 | 0.916 | 0.047 |
| lemma upos head deprel (default) | $0.54 | 0.907 | 0.052 |
| + feats | $0.73 | 0.913 | 0.045 |
| + feats xpos | $0.71 | 0.916 | 0.047 |
| default columns with all tools (run 4) | $0.77 | 0.919 | 0.044 |

No difference is detectable: every paired difference is within about ±0.02 F1 (e.g. forms vs default +0.005 [-0.016, +0.025]),
which is the resolution of 20 pairs / 313 links. So on DFHG Greek-Latin the agents do not need the parse in the
prompt, and FEATS only adds cost (+35%). Caveats: the rules (names rule: 43 links) still use the parse; cold start,
so the lemma-based prompt evidence was empty; Opus knows classical Greek and Latin well. The same test on the BICROSS
manuscript text (variant spellings, nomina sacra) and with accumulated evidence is still to do.

**Column ablation on BICROSS** (20 verses chosen like the DFHG dev set, `scripts/grc_lat_split.py`; ids in
`data/bicross/dev-ids.txt`, the other 79 verses are the untouched test set; consensus-dev = 322 links; same settings):

| Columns shown | Cost | F1 vs consensus | AER |
|---|---|---|---|
| forms only | $0.29 | 0.905 | 0.084 |
| lemma upos | $0.31 | 0.903 | 0.081 |
| lemma upos head deprel | $0.37 | 0.904 | 0.079 |
| + feats | $0.55 | 0.902 | 0.084 |
| + feats xpos | $0.59 | 0.903 | 0.084 |

Again no difference (paired differences within ±0.01). The two annotators agree at F1 0.955 on these 20 verses. The
whole gap is one word class: the model misses 46 of the 53 consensus links that start at a Greek article
(`το~aqua`, `το~spiritus`) and almost nothing else (precision 0.98, recall 0.84). The BICROSS annotators link the
article to its noun's translation (88-95% of articles, mostly to NOUN), whereas DFHG's gold leaves ~90% of articles
unlinked, which is what the bundled `grc-lat` guidelines say. Guidelines are therefore per corpus: BICROSS needs its
own article rule (to be tested; the dev set was used to find this).

**BICROSS guidelines** (`--guidelines bicross`, `mcaligner/guidelines/bicross.md` from `Adam/.../BICROSS_guidelines_grc-lat.odt`,
13 Aug 2024; the v2 .odt of 28 May says the opposite about articles and predates both workbooks). Same 20 dev verses, no tools:

| Run | Cost | F1 vs consensus | vs Kreinecker | vs Tilke | AER (consensus) |
|---|---|---|---|---|---|
| `grc-lat` guidelines, forms only | $0.29 | 0.905 | 0.893 | 0.895 | 0.084 |
| `bicross` guidelines, forms only | $0.40 | 0.978 | 0.957 | 0.967 | 0.016 |
| `bicross` guidelines, lemma upos head deprel | $0.54 | 0.977 | 0.955 | 0.965 | 0.018 |

The annotators agree with each other at F1 0.955 on these verses, so the aligner is at the level of the human agreement
(against each annotator separately). The consensus (links of either annotator) is a lenient reference; compare with the
per-annotator figures. The guidelines were chosen after seeing the article gap on this dev set: confirm on the 79 test verses.
- Rules on the dev set: names 43 links (41 in gold); `identical` linked punctuation only (0 right): now off
  (`link_punctuation`); lexicon with the full gold as leave-one-out evidence adds 3 (all right).
- BICROSS (`data/bicross/`): Greek and Latin manuscript text parsed the same way (resumable `parse-*.sh`); two
  annotators' alignments, IRR AER 0.052 (`scripts/bicross_prepare.py`, `irr.json`).

## Rules (no model)

`rules.py`; `mcaligner rules -s ... -a ... --target pred` applies them,
`--measure SET [--show-errors]` measures them. Rules only link words that have
no link yet, only 1-1, only when the match is unique in the pair, and write
sure links with confidence 0.95 (identical: 0.98), agent `rules`.

- **identical**: same form on both sides, unique on each side, and a symbol
  (punctuation only with `link_punctuation`, off by default: the Greek-Latin DFHG
  gold never aligns it, and the first measure linked 7 punctuation marks, 0 right)
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
- **MCParser was called mcparser** (2026-10-15 rename): the package and CLI are
  now `mcparser`, but the repository is still `../llmparser`. Imports are
  `from mcparser...`; the Claude Desktop config runs `python -m mcparser`. Older
  run reports and notes may still say mcparser.
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
- Generic store/MCP functionality goes into MCParser (tested at 100%); alignment
  exploration tools specific to this project live in `mcaligner/mcp/`.
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
