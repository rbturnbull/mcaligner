# Syriac–Arabic Alignment Guidelines (Arabic translation made from the Syriac, draft)

Adapted from the Greek–Arabic guidelines (`grc-ar`). The Arabic is a translation made from the Syriac (not from the Greek), so it follows the Syriac
closely, often word by word, in Middle Arabic. Here both texts translate Aristotle. Source A is the Syriac text, source B is the Arabic translation. A draft
for review: it has not been checked against a human gold alignment.

## General Principles

- Align the **smallest units that preserve the meaning**: single words wherever possible, groups only when necessary.
- Allowed links: 1-1, 1-N, N-1 and N-N. Words that do not correspond are left **unaligned** (no null links).
- Align what the translator **wrote**. The Arabic usually follows the Syriac word order, so most links run in order; crossing links are exceptions.
- Use `S` for a clear correspondence and `P` for a looser one (a paraphrase, a gloss, a shifted number or person, a different reading that still fills the same place).
- When uncertain, prefer **no alignment over a wrong one**.

## The words in the parse

The Arabic is split into syntactic words: prepositions (`ب` `ل` `ك`), conjunctions (`و` `ف`) and many pronoun suffixes are separate words. The definite article `ال` and the
person, number and gender of a verb are **not** split off. The Syriac one-letter prefixes (`ܘ` and, `ܕ` of/who/that, `ܒ` in/by, `ܠ` to) and pronoun suffixes may be separate words or still
attached: if a Syriac prefix or suffix is a word of its own, link it on its own; if it is attached, link the whole word to **every Arabic word it renders**
(Syriac `ܕܒܡܢܘ̈ܬܐ` ~ Arabic `التى فى الأجزاء`).

## Guidelines

1. **Punctuation** is never aligned (Syriac `܂ ܀ ܉`, Arabic `، ؛`).
2. **No equivalent**: a word present on one side only (added by the translator, a gloss, or a word the Arabic omits) is not aligned; so is a wrong or purely explanatory rendering.
   A word that governs several items but appears once links to the first item only.
3. **Repetition**: a word repeated on one side only is aligned once (the first), unless the translator repeats words for clarity (`ܚܕ ܚܕ` ~ `واحد واحد`).
4. **Fixed expressions**: several words that together render one word or expression align as a group (1-N, N-1 or N-N).
5. **Definiteness**: the Syriac emphatic state (ending `-ܐ`) is not a word; the Arabic `ال` is not a word of its own either. Do not link them separately: link the noun to the noun.
6. **`ܕ` (of, who, that)**: Syriac `ܕ` as a relative links to `الذي`, `التى`, `الذين` (and to `ما` or `من` where the Arabic uses those); as a genitive marker it links to the Arabic
   construct or to `ل`/`من` only if the Arabic writes a word for it; as a conjunction (`ܕ` = that) it links to `ان`, `لان`, `ل`, `حتى`. The Arabic construct state has no word: link the nouns.
7. **Verbs and participles**: link verbs by meaning, whatever the tense or stem. A Syriac participle with `ܕ` or `ܟܕ` rendered by an Arabic finite verb or participle links to that verb.
   `ܐܝܬ` (there is), `ܐܝܬܝܗ` (it is), `ܗܘ`, `ܗܘܐ` link to `هو`, `كان`, `يكون`, `يوجد` or `ليس` where written; where the Arabic has a nominal sentence the Syriac copula is left unaligned.
   `ܐܝܬ ܠ` + suffix ("has") links to `له`, `لها` or `عنده` (as a group when one Arabic word renders both).
8. **Pronouns**: pronoun suffixes link to the Arabic suffix or pronoun they render (`ܗ` ~ `ه`, `ܗܘܢ` ~ `هم`, `ܢ` ~ `نا`). An explicit pronoun on one side only links to the verb together with it (1-N).
   Demonstratives `ܗܢܐ`, `ܗܠܝܢ` ~ `هذا`, `هذه`, `هؤلاء`.
9. **Prepositions**: preposition for preposition 1-1 (`ܒ` ~ `ب`/`فى`, `ܠ` ~ `ل`/`الى`, `ܡܢ` ~ `من`, `ܥܠ` ~ `على`/`عن`, `ܥܡ` ~ `مع`, `ܒܝܕ` ~ `ب`, `ܡܛܠ` ~ `لاجل`/`بسبب`, `ܒܠܥܕ` ~ `ما خلا`/`بدون`/`من غير`).
   The Arabic prepositions are flexible: link the one chosen for the same relation. The Syriac `ܠ` that only marks the object has no Arabic word: leave it unaligned.
10. **Conjunctions and particles**: typical pairs `ܘ` ~ `و`/`ف`, `ܕܝܢ` ~ `فاما`/`و`/`ف`, `ܓܝܪ` ~ `لان`/`ف`, `ܐܠܐ` ~ `لكن`/`بل`, `ܐܘ` ~ `او`, `ܐܝܟ` ~ `مثل`/`كما`/`ك`,
    `ܠܐ`, `ܠܘ` ~ `لا`/`ليس`/`لم`/`ما`. The translator adds and omits `و` and `ف` freely: unmatched ones stay unaligned.
11. **Vocabulary**: the Arabic translator is lexically conservative and often transliterates or glosses a Syriac word (`ܡܬܕܡܝܢܘܬܐ` ~ `تشبيه ومحاكاة`, a doublet that renders one Syriac word: align 1-N).
    Do not link two words only because they look similar in form.

## Practical heuristics

- Prefer smaller links over larger ones; group only when the meaning is not compositional.
- Treat structural differences (construct state, nominal sentence, doublets, an inserted conjunction) as differences of structure, not of meaning.
- Do not link a word because it sits in the same position.
- Use `P` for a loose correspondence, and leave a word unlinked if you cannot say what it renders.

## Decision flow

1. Do the words share meaning in this sentence? No: leave unaligned.
2. Can they be linked 1-1? Yes: use 1-1.
3. Is the meaning spread over several words, or does one word contain several words' meaning (a prefix, a suffix, a doublet)? Yes: 1-N, N-1 or N-N.
4. Is the unit indivisible? Yes: keep it grouped.
5. Is the element purely grammatical (an inserted conjunction, a case or state ending, an object marker)? Likely unaligned, unless the other language has a word it corresponds to.
