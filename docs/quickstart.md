# Quickstart

## Install

mcaligner needs Python 3.11 or later and depends on MCParser (a pre-release):

```bash
pip install --pre mcaligner          # or: uv tool install --prerelease allow mcaligner
export ANTHROPIC_API_KEY=...         # the key for whichever provider your models use
mcaligner --version
```

To work from a clone, run `uv sync` in the repository and prefix the commands in these docs with `uv run`.

## Data

You need two parsed CoNLL-U files (see [Preparing files with MCParser](preparing.md)) (the same `sent_id` on both sides) and, for evaluation or
evidence, an alignment set in JSON Lines (see [Data](data.md)).
Below, `A` and `B` stand for the two CoNLL-U files:

```bash
SRC="-s ar=data/A.conllu -s grc=data/B.conllu"
```

## Align

```bash
mcaligner run $SRC \
    -a silver=ar,grc,data/ArabicAligned.jsonl:ro \
    -a pred=ar,grc,out/pred.jsonl \
    --target pred --max-sentences 5
```

`silver` is read-only evidence; `pred` is written (created on first save, with
an edit history in `out/pred.jsonl.history.jsonl`). The run prints its
progress, then the tokens and the estimated cost per model.

## Evaluate and export

```bash
mcaligner evaluate out/pred.jsonl gold.jsonl --annotated-only
mcaligner lexicon $SRC -a pred=ar,grc,out/pred.jsonl -o lexicon.yaml
```

## Settings

```bash
mcaligner settings > settings.yaml     # edit, then: run --settings settings.yaml
```
