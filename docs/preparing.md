# Preparing files with MCParser

mcaligner aligns texts that are **already parsed**: two CoNLL-U files whose sentences share `sent_id`s. The tool
for making those files is [MCParser](https://rbturnbull.github.io/mcparser), which annotates raw text with a team
of LLM agents (segmentation, lemma, UPOS, XPOS, FEATS, HEAD, DEPREL) using a treebank you trust as the examples.
It installs with mcaligner (`pip install --pre mcaligner` pulls in `mcparser`), and its own documentation covers
the options in full. This page is the short path for aligning two texts.

## 1. Put each text in one file, with matching ids

The same `sent_id` must name the same verse, fragment or sentence on both sides. Use either plain text (one
sentence per line, ids are line numbers) or YAML, which lets you choose the ids:

```yaml
John.1.1:
  text: εν αρχη ην ο λογος και ο λογος ην προς τον θεον και θεος ην ο λογος
  verse: John 1:1
John.1.2:
  text: ουτος ην εν αρχη προς τον θεον
```

If the two translations do not break the text in the same places, align at the level of the unit you can pair
(a verse, a paragraph); one pair may hold several sentences.

## 2. Make a prediction file

```bash
mcparser init john-grc.yaml -o john-grc.conllu -s grc=proiel-grc-train.conllu
mcparser init john-cop.yaml -o john-cop.conllu -s cop=coptic-scriptorium-train.conllu
```

`init` splits the text into words (whitespace, punctuation detached) and fills in what the trusted treebank makes
obvious without calling a model. A gold CoNLL-U file is also accepted: its segmentation is kept and its annotation
removed. Pick a treebank in the language and, ideally, the variety of your text (a Universal Dependencies
treebank, or one you have checked by hand). Several `-s` sources can be given.

## 3. Parse it

```bash
mcparser run john-grc.conllu -s grc=proiel-grc-train.conllu --cheap-first --rounds 3
mcparser run john-cop.conllu -s cop=coptic-scriptorium-train.conllu --cheap-first --rounds 3
```

Try a few sentences first with `--max-sentences 5` and read the cost it prints. `--cheap-first` runs the first
round one model tier down (Sonnet, then Opus only for what is still doubtful), and `--max-cost` stops starting
tasks at a limit; run again to continue. `mcparser validate FILE.conllu` checks the result is well formed, and
`mcparser evaluate pred.conllu gold.conllu` scores it if you have a gold parse.

For an agglutinative or fusional text (Coptic bound groups, Arabic clitics, Greek with elision) the segmentation
agent splits the written token into **syntactic words**, shown as multiword-token lines (`1-4 ⲁϥϫⲛⲟⲩⲟⲩ`)
followed by the words. mcaligner links words, never the multiword lines, so the quality of this split decides
what can be linked: a pronoun suffix that was not split off can only be linked as part of its host word.

## 4. Check what mcaligner needs

- Both files have the same `sent_id`s (mcaligner pairs sentences by id).
- Words have a **lemma** (the lemma falls back to the form) and UPOS. Heads and relations are shown to the agents
  but made no measurable difference to accuracy in the tests ([Results](results.md)), so a cheaper parse
  (forms, lemma, UPOS) is enough if cost matters.
- The words you want aligned are separate words. Punctuation is dropped from the links in code.

## 5. Align

```bash
mcaligner run -s grc=john-grc.conllu -s cop=john-cop.conllu \
    -a pred=grc,cop,john-aligned.jsonl --target pred --guidelines grc-cop
```

Choose the guidelines that match the corpus ([Agents](agents.md#guidelines-and-punctuation)): the guidelines are
the largest single influence on accuracy in the tests. Alignments you already have (from a human or an earlier
run) can be given as read-only evidence, for example `-a gold=grc,cop,earlier.jsonl:ro`, or imported from
Pharaoh/Ugarit text or YAML with `mcparser align import`.
