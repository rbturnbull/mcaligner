# Rules

Rules link words in code, without a model. They only add links between words
that have no link yet, only one-to-one, and only when the match is unique in
the sentence pair. Rule links are sure, with confidence 0.95 (0.98 for
identical symbols) and agent `rules`.

| Rule | Links when |
|---|---|
| `identical` | the same numeral or symbol (or other form without letters) occurs once on each side; punctuation only with `link_punctuation: true`, because alignment guidelines such as Ugarit's never align it |
| `names` | a proper noun on one side and a word on the other have matching consonant skeletons (transliterations from MISC `LTranslit`/`Translit`, lemma, form; Greek romanised; similarity ≥ 0.9, short skeletons equal), with no equally good rival |
| `lexicon` | the lemma's top translation has at least `min_count` (5) links and covers at least `min_share` (95%) of **all** the lemma's occurrences, the lemma occurs once in its sentence and the translation once (unlinked) in the other |

The lexicon rule counts only links with confidence ≥ 0.96, above what rules
write, so rules never feed themselves; links that agents give high confidence
do count, so the rule grows during a run.

```bash
mcaligner rules $SRC -a pred=... --target pred              # add links
mcaligner rules $SRC -a silver=...:ro --measure silver --show-errors
```

`--measure` proposes links for every pair of a reference set, starting from no
links and with the pair left out of the evidence, and reports each rule's
precision.

## Measured precision

On the 155 verses of Ephesians against the silver links:

| Rule | Links | In silver | After reading the disagreements |
|---|---|---|---|
| identical | 0 | – | the Greek text has no punctuation |
| names | 20 | 18 | 20/20 correct: both disagreements are silver errors |
| lexicon | 129 | 127 | 128/129 correct |

Looser lexicon settings add links at lower precision: (3, 0.9) gives 229 links
with 3 real errors; (5, 0.8) 265 links at 94.7% against silver.
