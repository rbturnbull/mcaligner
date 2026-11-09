# Quickstart

## Install

mcaligner depends on MCParser by path (the sibling directory `../llmparser`):

```bash
uv sync --python /opt/homebrew/opt/python@3.13/bin/python3.13
export ANTHROPIC_API_KEY=...
```

## From the old YAML format

```bash
uv run mcaligner convert results/ArabicAligned.yaml -o data/
```

This writes one CoNLL-U file per text and the old alignments as a JSON Lines
alignment set, and prints the `--source`/`--alignment` options to use them.
Below, `A` and `B` stand for the two CoNLL-U files:

```bash
SRC="-s ar=data/A.conllu -s grc=data/B.conllu"
```

## Align

```bash
uv run mcaligner run $SRC \
    -a silver=ar,grc,data/ArabicAligned.jsonl:ro \
    -a pred=ar,grc,out/pred.jsonl \
    --target pred --max-sentences 5
```

`silver` is read-only evidence; `pred` is written (created on first save, with
an edit history in `out/pred.jsonl.history.jsonl`). The run prints its
progress, then the tokens and the estimated cost per model.

## Evaluate and export

```bash
uv run mcaligner evaluate out/pred.jsonl gold.jsonl --annotated-only
uv run mcaligner lexicon $SRC -a pred=ar,grc,out/pred.jsonl -o lexicon.yaml
```

## Settings

```bash
uv run mcaligner settings > settings.yaml     # edit, then: run --settings settings.yaml
```
