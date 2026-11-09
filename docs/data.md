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

## Converting the old format

The old llmaligner kept both parses and the alignment of each verse in one
YAML file:

```yaml
B10K1V1:
  ArabGr1-Arabic-Ephesians-Parsed: {text: ..., verse: Ephesians 1:1, conllu: ..., id: B10K1V1}
  ArabGr1-GreekVorlage-Ephesians-Parsed: {...}
  alignment: 1-1S 2-2S 3-3P
```

`llmaligner convert` writes `<corpus>.conllu` for each text (`sent_id` = the
verse id, `# text`, and the other fields as comments) and `<name>.jsonl` with
the alignments. It pads token lines that lack trailing columns and drops links
to words that do not exist, and reports both. On `results/ArabicAligned.yaml`
(155 verses, 2095 links): 4 lines padded, 1 link dropped.

The old alignments came from an earlier LLM run: use them as **silver**
evidence (read-only), not as gold.

## The translation table

Code (the rules, the prompt evidence, the lexicon export) counts translations
with {class}`~llmaligner.lexicon.TranslationTable`: for every lemma of every
aligned source, which lemmas of the other source its words are linked to,
built in one pass over the sets. A word's lemma falls back to its form. Counts
are kept per sentence, so the sentence being aligned is always left out of its
own evidence. Agents can ask the same question through the MCP tool
`translation_candidates`.
