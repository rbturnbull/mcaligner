# Agents and runs

`mcaligner run` applies the rules, then runs rounds of two
[pydantic-ai](https://ai.pydantic.dev) agents over a writable alignment set:

1. **Aligner** (strong tier, default `anthropic:claude-opus-5-5`). Works on
   pairs it has not seen and on pairs with links below the threshold (0.8),
   several pairs per task.
2. **Scorer** (efficient tier, default `anthropic:claude-sonnet-5-5`,
   optional). Rates the links the aligner set or changed; links it rates below
   the threshold go back to the aligner in the next round.
3. **Rules** run again with the new confident links as evidence.

A run stops when nothing is below the threshold, a round changes no pair's
links, or the round limit (`--rounds`, default 2) is reached.

## What the aligner sees

For each pair: both sentences as compact lines (`id form lemma UPOS head
deprel` and glosses from MISC), the settled links (kept), the links to review,
and for each unlinked word how its lemma is linked elsewhere:

```text
## Pair B10K1V3
A: مبارك هو الله ابو ربنا يسوع المسيح: ...
1 مبارك مُبَارَك ADJ 3 nsubj blessed
...
Settled links: 3-3S 0.95 rules, 5-7S 0.95 rules, 6-9S 0.95 rules
Evidence for unlinked words (linked lemmas elsewhere):
A4 أَب: πατήρ×8, πατριά×1, γονεύς×1 (of 11)
B10 Χριστός: مَسِيح×25, المسيح×11, يسوع×5 (of 43, 3 unlinked)
```

It answers with one line per link, `SENT_ID A-B S|P CONFIDENCE`, plus
`SENT_ID A-B` lines for settled links to remove. Code checks every pair with
`set_links(..., dry_run=True)` and sends any problem back to the model; only a
fully valid answer is written. The scorer answers `SENT_ID A-B CONFIDENCE`.

Both agents can call read-only MCP tools (`get_parallel`,
`translation_candidates`, `analyse_form`, `find_tokens`, `get_context`) when
the prompt is not enough; their results are shown in compact text.

## Models and settings

```bash
mcaligner run ... --model anthropic:claude-sonnet-5-5      # one model for both
mcaligner run ... --aligner-model ... --scorer-model ...  # per role
mcaligner run ... --strong-thinking low --no-scorer
```

All options also live in a YAML settings file (`mcaligner settings` prints
the defaults): tiers, per-role `model`, `thinking`, `instructions` and
`enabled`, `threshold`, `rounds`, `batch_sentences`, `batch_words`,
`candidates`, `misc_keys`, `guidelines`, and the rule settings (including `link_punctuation`).

## Columns and tools

The prompt shows each word as `id form` plus the `columns` setting (default `lemma upos head deprel`; `--columns
lemma,upos,head,deprel,feats,xpos`, or `none` for forms only), then any `misc_keys`. `tools` limits the read tools the
agents may call (`--tools none`, or a list; default all). The instructions describe whatever is shown and available, so
the same code runs ablations such as "no parse" or "with FEATS".

## Guidelines and punctuation

The aligner's and scorer's instructions include annotation guidelines, so they follow the rules the human
annotators followed. The default is the bundled `grc-lat` (`mcaligner/guidelines/grc-lat.md`, a condensed version of
the Ugarit guidelines for Greek-Latin fragments; articles are not aligned). `bicross` is the BICROSS guidelines of 13 August 2024
for the New Testament manuscripts (articles are aligned with their noun's translation), which the BICROSS annotators followed. The other bundled files are **drafts, not checked against a human alignment**: `grc-cop` (Greek-Coptic, Sahidic with the
Coptic split into articles, auxiliaries and pronouns), `grc-ar` (Greek-Arabic), `lat-ar`, `grc-syr`, `syr-ar` and `got-lat`. Use `--guidelines PATH` (or `guidelines:` in the settings) for your
own text, or `--guidelines none` for other language pairs such as Arabic-Greek.

Punctuation is never aligned under these guidelines, so links to punctuation are dropped in code from the aligner's
answers and the identical rule skips it; the number dropped is in each task's `details.dropped` in the report.
`--link-punctuation` (or `rules: {link_punctuation: true}`) allows them.

## Cost

Every run prints tokens and an estimated price per model (list prices from
`mcparser.pricing`), and appends its full report to `<set>.runs.jsonl`.
Prompt caching is on by default.

Ephesians 1:1–5 with the other 150 verses as silver evidence, 2 rounds: 6
requests (one per task, no tool calls), about 44k input and 5k output tokens,
**$0.18–0.21** (Opus about three quarters of it). Against silver: F1 0.87–0.88
over all links, AER 0.12–0.13; most disagreements were silver errors or
correct links from unsplit Arabic pronoun suffixes. The second round changed
little, so for large runs `--rounds 1` is worth considering.
