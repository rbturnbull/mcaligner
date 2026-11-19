# Greek–Syriac Alignment Guidelines (translated Greek philosophical and scientific prose, draft)

Adapted from the Greek–Arabic guidelines (`grc-ar`), which derive from the BICROSS Greek–Latin guidelines. The Syriac is a translation of a
Greek philosophical or scientific text (here Aristotle): very literal in vocabulary and word order, with the glosses and paraphrases of a
translator who works word by word. Source A is the Greek text (polytonic, as edited), source B is the Syriac translation. A draft for review:
it has not been checked against a human gold alignment.

## General Principles

- Align the **smallest units that preserve the meaning**: single words wherever possible, groups only when necessary.
- Allowed links: 1-1, 1-N, N-1 and N-N. Words that do not correspond are left **unaligned** (no null links).
- Align what the translator **wrote**. The Syriac follows the Greek word order closely, but not always: do not force position.
- Use `S` for a clear correspondence and `P` for a looser one (a gloss, a paraphrase, a shifted number or person, a different Greek reading
  that still fills the same place in the sentence).
- When uncertain, prefer **no alignment over a wrong one**.

## The Syriac words in the parse

The one-letter prefixes `ܘ` (and), `ܕ` (of, who, that), `ܒ` (in, by), `ܠ` (to, object marker) and `ܟ` (as) may be separate words in the parse (the
segmentation agent splits them) or still attached; pronoun suffixes (`ܗ` his, `ܗ̇` her, `ܗܘܢ` their, `ܢ` our, `ܟܘܢ` your) are suffixes and may be split off.
Check the parse: if a prefix or suffix is a word of its own, link it on its own; if it is still attached to a noun or verb, link the whole word to
**every Greek word it renders** (`ܕܒܡܢܘ̈ܬܐ` renders Greek `ἐν τοῖς μορίοις` or a relative plus `ἐν`).

## Guidelines

1. **Punctuation** is never aligned (the Syriac stops `܂ ܀ ܉` and the Greek commas, colons and raised dots).
2. **No equivalent**: a word present on one side only (added by the translator, a gloss, or a Greek word the Syriac does not render) is not aligned;
   so is a wrong or purely explanatory rendering. A word that governs several items but appears once links to the first item only.
3. **Repetition**: a word repeated on one side only is aligned once (the first), unless the translator repeats words for clarity (`ܚܕ ܚܕ` for `ἕκαστος`).
4. **Fixed expressions and calques**: several words that together render one Greek word (a compound rendered by a phrase, `ܡܬܕܡܝܢܘܬܐ` for `μίμησις`
   is one word) or one expression that no single word renders align as a group (1-N, N-1 or N-N).
5. **Greek article**: Syriac has no article. The article is left **unaligned**, except where it clearly renders a demonstrative or relative
   (`ܗܢܐ`, `ܗܘ`, `ܕ`) or heads a substantive participle that the Syriac renders with `ܕ` plus a verb: then link it to that word.
   The **emphatic state** (the ending `-ܐ`) is not a word and carries no separate link.
6. **Relatives, `ܕ` and participles**: Greek relatives (`ὅς`, `ἥ`, `ὅ`, `ὅστις`) link to `ܕ` (or `ܕܗܘ`, `ܗܘ ܕ`). Greek `ὅτι` and `ἵνα` link to `ܕ` or `ܕܐܝܟ`, `ܕܠܡܐ`.
   A genitive noun is often rendered by `ܕ` plus the noun (the construct state or `ܕ`): link the noun to the noun, and link `ܕ` only if the Greek has a word
   for it (a preposition, a relative). A Greek participle may be rendered by a Syriac participle, by `ܕ` plus a finite verb or by `ܟܕ` plus a participle: link
   the participle to the verb that carries its meaning.
7. **Subjects, pronouns and "to be"**: both languages may leave the subject in the verb. An explicit pronoun on one side only links to the verb
   together with it (1-N). Pronoun suffixes link to the Greek pronoun they render (`ܗ` ~ `αὐτοῦ`, `αὐτόν`, `αὐτῷ`). `ܐܝܬ` (there is), `ܐܝܬܝܗ` (it is), `ܗܘ`, `ܗܘܐ`
   link to Greek `εἰμί`, `ἔστιν`, `ἦν`; `ܐܝܬ ܠ` + suffix (`ܐܝܬ ܠܗ̇`, "it has") links to Greek `ἔχω` or to a dative of possession. Where Greek has no copula
   and the Syriac has one, leave the Syriac word unaligned.
8. **Prepositions and cases**: preposition for preposition 1-1 (`ἐν` ~ `ܒ`, `ἐκ`, `ἀπό` ~ `ܡܢ`, `εἰς`, `πρός` ~ `ܠ`, `διά` + genitive ~ `ܒܝܕ`, `διά` + accusative ~ `ܡܛܠ`,
   `περί`, `ἐπί` ~ `ܥܠ`, `μετά` ~ `ܥܡ`, `χωρίς` ~ `ܒܠܥܕ` or `ܡܢ ܒܠܥܕ`). The Syriac `ܠ` marks the object and the dative: link it only to a Greek word it renders.
   A Greek case with no preposition rendered by a Syriac preposition: link the nouns; link the preposition only if the Greek has a word for it.
9. **Conjunctions and particles**: typical pairs `καί` ~ `ܘ`, `δέ` ~ `ܕܝܢ`, `γάρ` ~ `ܓܝܪ`, `ἀλλά` ~ `ܐܠܐ`, `ἤ` ~ `ܐܘ`, `οὖν` ~ `ܐܢܐ`/`ܗܟܝܠ`, `ὡς` ~ `ܐܝܟ`, `μέν` ~ `ܡܢ ܡܕܡ` (often
   unrendered), `ἐπεί` ~ `ܡܛܠ ܕ`, `ὥστε` ~ `ܕܗܟܢܐ`; `οὐ`, `μή` ~ `ܠܐ`, `ܠܘ`. The translator adds and omits `ܘ` and `ܕܝܢ` freely: unmatched ones stay unaligned.
10. **Vocabulary**: the translator is lexically very conservative (a Greek word mostly has one Syriac equivalent: `τραγῳδία` ~ `ܛܪܓܘܕܝܐ`, `μίμησις` ~ `ܡܬܕܡܝܢܘܬܐ`, `λόγος` ~ `ܡܠܬܐ`).
    Transliterations of Greek words are aligned 1-1. Do not link two words only because they look similar in form.

## Practical heuristics

- Prefer smaller links over larger ones; group only when the meaning is not compositional.
- Treat structural differences (genitive as `ܕ` phrase, participle as clause, article lost, inserted copula) as differences of structure, not of meaning.
- Do not link a word because it sits in the same position.
- Use `P` for a loose correspondence, and leave a word unlinked if you cannot say what it renders.

## Decision flow

1. Do the words share meaning in this sentence? No: leave unaligned.
2. Can they be linked 1-1? Yes: use 1-1.
3. Is the meaning spread over several words, or does one Syriac word contain several Greek words' meaning (a suffix, a prefix)? Yes: 1-N, N-1 or N-N.
4. Is the unit indivisible? Yes: keep it grouped.
5. Is the element purely grammatical (an inserted conjunction, a case ending, an emphatic-state ending, the Greek article)? Likely unaligned, unless the other language has a word it
   corresponds to.
