# Data

## Sentences and links

The two texts are CoNLL-U files, one sentence per pair, with the same
`sent_id` on both sides. Links join **syntactic words** (ids `1`, `2`, ...),
not multiword tokens: an Arabic token `بشيه` split into `ب` + `شيه` has two
words that can be linked separately.

Links are stored in an MCParser **alignment set**, a JSON Lines file with
one sentence pair per line:

```json
{"sent_id": "B10K1V1", "links": [{"source": "1", "target": "1", "sure": true, "confidence": 0.95, "agent": "rules"}]}
```

- `sure`: S (sure) or P (probable), as in Ugarit.
- `confidence`: 0–1. Links without one take the set's default (1.0 for a
  read-only set, 0.0 for a writable one; `PATH:ro:0.8` sets it).
- `agent`: who last set or changed the link (`rules`, `aligner`, `scorer`, a
  person). A link sent again unchanged keeps its agent.

A set is given on the command line as
`NAME=SOURCE_A,SOURCE_B,PATH[:ro|rw[:CONFIDENCE]]` (default `rw`), with the
sources as `[NAME=]PATH[:ro|rw]` (default `ro`). Every edit to a writable set is
appended to `<file>.history.jsonl`.

## Exchange formats

JSON Lines is the stored format. `mcparser align import` and `mcparser align
export` convert to and from Pharaoh/Ugarit text (`0-0S 1-2P`, one line per
pair, 0- or 1-based) and YAML (`sent_id: 1-1S 2-3P`); see MCParser's
documentation. Gold standards that come as raw text plus links (for example
the Greek-Latin one) need the tokens of the parsed CoNLL-U files, which can
differ from the gold's tokens; `scripts/grc_lat_gold.py` maps one onto the
other by character position.

Alignments from an earlier LLM run (for example the old Ephesians YAML) are
**silver**: use them as read-only evidence, not as gold.

## The translation table

Code (the rules, the prompt evidence, the lexicon export) counts translations
with {class}`~mcaligner.lexicon.TranslationTable`: for every lemma of every
aligned source, which lemmas of the other source its words are linked to,
built in one pass over the sets. A word's lemma falls back to its form. Counts
are kept per sentence, so the sentence being aligned is always left out of its
own evidence. Agents can ask the same question through the MCP tool
`translation_candidates`.
