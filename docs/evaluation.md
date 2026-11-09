# Evaluation and lexicon

## Evaluate

```bash
uv run llmaligner evaluate PRED.jsonl GOLD.jsonl [--annotated-only] [--min-confidence 0.8] [--per-sentence] [--json]
```

With A the predicted links, S the gold sure links and P all gold links:

- **sure** precision/recall/F1: predicted sure links against S;
- **all** precision/recall/F1: A against P, ignoring S/P;
- **AER** = 1 − (|A∩S| + |A∩P|) / (|A| + |S|) (Och & Ney 2003).

Only pairs in the gold file are scored, because gold often covers part of a
text; a gold pair without predictions counts as empty. `--annotated-only`
scores only pairs with predicted links (a partial run). `--min-confidence`
ignores weaker predicted links, to see precision at a confidence level. Totals
are micro-averaged.

## Lexicon

```bash
uv run llmaligner lexicon $SRC -a pred=ar,grc,out/pred.jsonl -o lexicon.yaml [--min-confidence 0.8] [--min-count 2] [--top 5]
```

```yaml
ArabGr1-Arabic-Ephesians-Parsed:
  رَسُول:
    part_of_speech: NOUN
    occurrences: 2
    unaligned: 0
    alignments:
      ἀπόστολος: {count: 2, part_of_speech: NOUN}
```

A `.json` output path writes JSON. Only links at least `--min-confidence`
confident count (default 0.8). On the silver set this reproduces the old
`ArabicLexicon.yaml`.
