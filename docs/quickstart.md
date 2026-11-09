# Quickstart

## Install

llmaligner depends on MCParser by path (the sibling directory `../llmparser`):

```bash
uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13
export ANTHROPIC_API_KEY=...
```

## From the old YAML format

```bash
uv run llmaligner convert results/ArabicAligned.yaml -o data/
```

This writes one CoNLL-U file per text and the old alignments as a JSON Lines
alignment set, and prints the `--source`/`--alignment` options to use them.
Below, `A` and `B` stand for the two CoNLL-U files:

```bash
SRC="-s ar=data/A.conllu -s grc=data/B.conllu"
```

## Align

```bash
uv run llmaligner run $SRC \
    -a silver=ar,grc,data/ArabicAligned.jsonl:ro \
    -a pred=ar,grc,out/pred.jsonl \
    --target pred --max-sentences 5
```

`silver` is read-only evidence; `pred` is written (created on first save, with
an edit history in `out/pred.jsonl.history.jsonl`). The run prints its
progress, then the tokens and the estimated cost per model.

## Evaluate and export

```bash
uv run llmaligner evaluate out/pred.jsonl gold.jsonl --annotated-only
uv run llmaligner lexicon $SRC -a pred=ar,grc,out/pred.jsonl -o lexicon.yaml
```

## Settings

```bash
uv run llmaligner settings > settings.yaml     # edit, then: run --settings settings.yaml
```
