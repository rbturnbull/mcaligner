# Results

Two held-out test sets, never used for tuning (the dev subsets were chosen first, stratified by length with a fixed
seed, and the prompt, guidelines and columns were chosen on those). Pipeline: rules, an Opus 5.5 aligner and a Sonnet
5.5 scorer for 2 rounds, cold start (no evidence sets), the corpus's own guidelines. One run per configuration.

| Test set | Gold | Guidelines | Pairs | Links (pipeline / gold) | F1 (all links) | AER | Cost |
|---|---|---|---|---|---|---|---|
| BICROSS (New Testament manuscripts, Greek-Latin) | 2 human annotators | `bicross` | 79 verses | 1,412 / 1,371 and 1,404 | 0.947 and 0.975 | 0.053 and 0.025 | $2.64 |
| DFHG (Greek fragments, Latin translation) | merged human gold | `grc-lat` | 80 fragments | 1,215 / 1,284 | 0.922 | 0.042 | $2.34 |

Both runs: 86-88 requests, no failed tasks, no retries, no tool calls; about $0.03 per pair.

## BICROSS against the two annotators

The two annotators agree with each other at F1 0.946 (AER 0.054) on these 79 verses.

| Compared with | Sure P / R / F1 | All links P / R / F1 | AER |
|---|---|---|---|
| Kreinecker (1,371 links) | 0.956 / 0.940 / 0.948 | 0.933 / 0.961 / **0.947** | 0.053 |
| Tilke (1,404 links) | 0.984 / 0.946 / 0.965 | 0.972 / 0.978 / **0.975** | 0.025 |
| Consensus (links of either annotator) | 0.944 / 0.970 / 0.956 | 0.986 / 0.952 / **0.969** | 0.013 |
| *Human against human* | | *0.946* | *0.054* |

The pipeline is **at the level of human agreement** (equal to it against Kreinecker, above it against Tilke, who
links a little more, as the pipeline does). The consensus is a lenient reference, so compare the per-annotator rows
with the human agreement.

## DFHG

All links P/R/F1 0.948 / 0.897 / 0.922, AER 0.042; sure links 0.967 / 0.877 / 0.920. The annotators agree at a Dice of
about 0.927 (from the counts in the gold README, over all 100 fragments, not only these 80). The remaining errors
are verbs and participles linked to relatives or subordinators, prepositions the Latin renders by case, and adverbs.

## What matters, and what does not

- **The guidelines.** On the BICROSS dev verses the same pipeline scored F1 0.905 with the DFHG-style guidelines and
  0.978 with the BICROSS ones: the annotators align the Greek article with its noun, DFHG leaves it unaligned.
  Give the agents the rules your annotators followed (`--guidelines`).
- **The parse columns.** Words only, words + lemma + UPOS, and the default columns with all tools differ by at most
  0.005 F1 on both test sets; words only is about 35% cheaper.

| Prompt shows | DFHG F1 / cost | BICROSS F1 (Kreinecker / Tilke) | BICROSS cost |
|---|---|---|---|
| words only | 0.927 / $1.55 | 0.948 / 0.974 | $1.76 |
| + lemma, UPOS | 0.922 / $1.88 | 0.946 / 0.973 | $1.95 |
| + head, deprel, all tools (default) | 0.922 / $2.34 | 0.946 / 0.975 | $2.64 |

## Caveats

- One run each; sampling noise on 79-80 pairs is about ±0.015 F1.
- The guidelines were chosen on dev after seeing errors there. The DFHG test errors have been seen: tune on dev only.
- The evidence path (lemma hints from accumulated links) and lower-resource languages are not tested here. The
  Greek-Arabic, Greek-Coptic, Greek-Syriac, Latin-Arabic, Syriac-Arabic and Gothic-Latin guidelines are
  **unvalidated drafts**: no human gold alignment exists for them yet.
