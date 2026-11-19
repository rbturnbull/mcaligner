# Latin–Arabic Alignment Guidelines (Early Arabic New Testament, draft)

Adapted from the Greek–Arabic guidelines (`grc-ar`), which derive from the BICROSS Greek–Latin guidelines, for an Arabic
translation that stands next to a Latin (Vetus Latina or Vulgate) text in a bilingual manuscript. The Arabic may be translated from
the Latin or from a Greek Vorlage: Middle Arabic, literal in vocabulary and free in syntax. Source A is Latin (lowercase, spelling
as in the manuscript, nomina sacra expanded), source B is Arabic. A draft for review: it has not been checked against a human gold alignment.

## General Principles

- Align the **smallest units that preserve the meaning**: single words wherever possible, groups only when necessary.
- Allowed links: 1-1, 1-N, N-1 and N-N. Words that do not correspond are left **unaligned** (no null links).
- Align what the translator **wrote**. Arabic word order differs from Latin: expect crossing links.
- Use `S` for a clear correspondence and `P` for a looser one (a paraphrase, a shifted person or number, a different reading
  that still fills the same place in the sentence).
- When uncertain, prefer **no alignment over a wrong one**.

## The Arabic words in the parse

Prepositions (`ب` `ل` `ك` `مع`), conjunctions (`و` `ف`) and many pronoun suffixes (`ه` `هم` `كم` `نا` `ها`) are separate words, so each can be
linked on its own. The definite article `ال`, the person, number and gender of a verb, and some pronoun suffixes are **not** split
off. Link such a word to **every Latin word it renders**: Latin `domini` and `nostri` both link to `ربنا`.

## Guidelines

1. **Punctuation** is never aligned.
2. **No equivalent**: a word present on one side only (added by the translator, or left out) is not aligned; so is a wrong or purely
   explanatory rendering. A word that governs several items but appears once on one side links to the first item only.
3. **Repetition**: when a word is repeated on one side only, align the first instance, unless the translator repeats words for
   emphasis or clarity (then each links to its own counterpart).
4. **Fixed expressions**: several words forming one unit of meaning that no single word translates align as a group (N-N).
5. **Names and titles**: transliterated names align 1-1 (`paulus` ~ `بولس`, `ephesi` ~ `افسس`, `deus`, `dei`, `deo` ~ `الله`). The Arabic
   usually writes `يسوع المسيح` whatever the Latin order (`iesu christi` or `christi iesu`): link by name, with crossing links if
   the order differs. `ربنا` renders `dominus noster`: link both Latin words to it.
6. **Latin has no article; Arabic has `ال`.** Leave `ال` unaligned (it is not a word of its own anyway). A Latin demonstrative or
   pronoun (`is`, `ille`, `hic`, `qui`) links to the Arabic pronoun, demonstrative or relative that renders it.
7. **Relatives and participles**: `qui`, `quae`, `quod` link to `الذي` (include `هو` when it is part of the expression, 1-N). A Latin participle
   is often a finite verb in Arabic (`benedicens` ~ `بارك`) or a relative clause: link it to the verb that carries its meaning;
   a Latin participle rendered as a noun links to the noun.
8. **Subjects and pronouns**: both languages may leave the subject in the verb; then only the verbs link. An explicit pronoun on one side
   only (`ego dico` ~ `اقول`) links to the verb together with it (1-N). A noun subject missing on the other side is not aligned.
   Pronoun suffixes link to the Latin pronoun they render (`ه` ~ `eum`, `ei`, `eius`; `نا` ~ `nos`, `nobis`, `nostri`; `كم` ~ `uos`, `uobis`,
   `uestri`); with `P` if person or number shifts. Latin reflexives (`se`, `sibi`) link to `به`, `نفسه` and the like by meaning.
9. **"To be"**: the Arabic often has a nominal sentence where Latin has `est`, `sunt`, `erat`; leave the Latin verb unaligned unless a
   copula or `هو` is written. Periphrastic Latin forms (`esse` + participle, `habeo` + infinitive) link to the Arabic verb as a group.
10. **Prepositions and cases**: preposition for preposition 1-1 (`in` ~ `في` or `ب`, `per` ~ `ب`, `ad` ~ `الى` or `ل`, `de`, `ex` ~ `من`). The Arabic
    prepositions are flexible: link the one chosen for the same relation. If Latin has a bare case (genitive, dative, ablative) and Arabic
    a construct state, `ل` or `ب`, link the nouns, and the preposition only if the other side has a word for it. A Latin prepositional phrase
    rendered by a clause: link the content words.
11. **Conjunctions and particles**: an Arabic `و` or `ف` is aligned with the Latin conjunction it renders (`et`, `autem`, `enim`, `ergo`,
    `igitur`, `sed`); the translator inserts and omits them freely, so unmatched ones stay unaligned. Typical pairs: `et` ~ `و`, `autem` ~ `ف`/`و`/`اما`,
    `enim` ~ `ف`/`لان`, `ergo` ~ `ف`, `sed` ~ `لكن`/`بل`, `aut`, `uel` ~ `او`, `quia`, `quoniam`, `quod` ~ `ان`/`لان`, `ut` ~ `ل`/`لكي`/`ان`, `si` ~ `ان`/`اذا`,
    `non`, `ne` ~ `لا`/`لم`/`ليس`/`ما`. Latin enclitics (`-que`, `-ne`) stay with their host and link with the Arabic word for the whole.
12. **Verbs**: Latin tense, mood and voice do not decide the link; the Arabic does not reliably distinguish them. Link verbs by meaning.
    Latin ablative absolute or gerund rendered by a clause: link component by component where a counterpart exists.
13. **Vocabulary**: the translator is lexically conservative (`gratia` ~ `نعمة`, `pax` ~ `سلام`). Use the translation hints in the task. Do not link two
    words only because they look similar in form.

## Practical heuristics

- Prefer smaller links over larger ones; group only when the meaning is not compositional.
- Treat syntactic differences (participle as verb, case as preposition, noun phrase as nominal sentence, an inserted conjunction) as
  differences of structure, not of meaning: link what carries the meaning, leave the purely grammatical additions unaligned.
- Do not link a word because it sits in the same position: the Arabic order often differs.
- Use `P` for a loose correspondence, and leave a word unlinked if you cannot say what it renders.

## Decision flow

1. Do the words share meaning in this sentence? No: leave unaligned.
2. Can they be linked 1-1? Yes: use 1-1.
3. Is the meaning spread over several words, or does one Arabic word contain the meaning of several Latin words (a suffix, `ربنا`)? Yes: 1-N, N-1 or N-N.
4. Is the unit indivisible? Yes: keep it grouped.
5. Is the element purely grammatical (an inserted conjunction, a case ending, `ال`)? Likely unaligned, unless the other language has a word it
   corresponds to.
