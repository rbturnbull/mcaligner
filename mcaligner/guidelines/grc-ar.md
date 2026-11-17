# Greek–Arabic Alignment Guidelines (Early Arabic New Testament)

Written in the spirit of the BICROSS Greek–Latin guidelines (which derive from the Ugarit guidelines), adapted to an Arabic
translation of a Greek Vorlage: Middle Arabic, literal in vocabulary and free in syntax. The Greek is New Testament text
(unaccented, lowercase); the Arabic is the translation. Source A is Greek, source B is Arabic. A draft for review: it has not
been checked against a human gold alignment.

## General Principles

- Align the **smallest units that preserve the meaning**: single words wherever possible, groups only when necessary.
- The two sides must bear the **same meaning** and the link should involve as few words as possible, but as many as necessary.
- Allowed links: one-to-one (1-1), one-to-many (1-N), many-to-one (N-1) and many-to-many (N-N).
- Words that do not correspond are left **unaligned** (there are no null links).
- Align what the translator **wrote**, not what you think the Greek should have produced. The translation follows Greek word
  order only loosely: expect crossing links.
- Use `S` for a clear correspondence and `P` for a looser one (a paraphrase, a shifted person or number, a different
  Vorlage reading that still fills the same place in the sentence).
- When uncertain, prefer **no alignment over a wrong one**.

## The Arabic words in the parse

The Arabic is split into syntactic words. Prepositions (`ب` `ل` `ك` `مع`), conjunctions (`و` `ف`) and many pronoun suffixes
(`ه` `هم` `كم` `نا` `ها`) are separate words, so each can be linked on its own. A token such as `بمشيه` is the words `ب`
and `مشيه`.

Some morphemes are **not** split off: the definite article `ال` (it stays inside the noun), the person, number and gender
of a verb, and some pronoun suffixes (`ربنا` "our Lord", `بركنا` "he blessed us"). Link such a word to **every Greek word it
renders**: Greek `κυριου` and `ημων` both link to `ربنا`; Greek `ευλογησας` and `ημας` both link to `بركنا`.

## Guidelines

### 1. Punctuation
Punctuation is never aligned.

### 2. Words with no equivalent
- A word that appears in only one language and has no counterpart in the other is not aligned: a word the translator added,
  or a Greek word the Arabic leaves out.
- A wrong or purely explanatory rendering is not aligned.
- If one word governs several items (a preposition before two nouns) and appears only once on one side, it links to the
  first item only.

### 3. Repetition
When a word is repeated in one language but not in the other, only the first instance is aligned. Exception: the translator
repeats words for emphasis or clarity, for example `ما ... وما ...` for `τα ... και τα`; there each Arabic word links to its
own Greek counterpart.

### 4. Fixed expressions and idioms
If several words together form one unit of meaning that no single word translates, align them as a group (N-N).

### 5. Proper names and titles
- Names are transliterated (`بولس` Paul, `افسس` Ephesus, `الله` God): align them 1-1 with the Greek name.
- The Arabic always writes `يسوع المسيح` (Jesus Christ), whatever the Greek order (`ιησους χριστος` or `χριστος ιησους`).
  Link by name, not by position: `ιησου` to `يسوع`, `χριστου` to `المسيح`, with crossing links if the order differs.
- `ربنا` renders `ο κυριος ημων`: see the rule on attached morphemes above.

### 6. Definite article
- The Greek article is aligned with the **Arabic article** `ال`, and both are kept **separate from the noun**: article to
  article and noun to noun are separate links.
- In this parse `ال` is not a word of its own: it stays inside the noun (`المسيح`). So link the Greek article to the Arabic
  word that carries `ال`, and link the Greek noun to that same Arabic word. Each Greek word keeps its own link; two links
  end on one Arabic word.
- Link the article only when **both** languages have one. The translator adds the Arabic article where Greek has none and
  omits it where Greek has one: then the article is left unaligned and the nouns are still linked.
- A Greek article that introduces a participle, an adjective or a phrase (`ο ευλογησας`, `ο εν ...`) is rendered by the Arabic
  relative `الذي`, not by `ال`: see rule 7.
- Greek `ο`, `η`, `το` used as a pronoun (`ο δε` "and he") links to the Arabic pronoun or to the word that renders it.

### 7. Relative clauses and substantive participles
- Greek relatives (`ος`, `η`, `ο`) are rendered by `الذي هو` or `الذي`: link the relative to the Arabic relative word,
  and include `هو` in the same group when it is part of that expression (1-N).
- A Greek article with a participle (`ο ευλογησας`, "the one who blessed") is often rendered `الذي` plus a finite verb: link
  the article to `الذي` and the participle to the verb.

### 8. Participles, infinitives and verbs
- Greek participles are often rendered as finite verbs (`γνωρισας` as `واعلمنا`). Link the participle to the verb that
  carries its meaning (1-1).
- A participle rendered by a coordinated verb (`و` plus verb) links to the verb. The added `و` is linked to a Greek `και` only
  if the Greek has one; otherwise it is left unaligned.
- A participle rendered as a noun links to that noun.
- Purpose and result: `ινα` links to `ل`, `لكي` or `ان` and the verb to the verb; an infinitive links to the verb or verbal
  noun that renders it.
- The Arabic does not reliably distinguish Greek tenses: link verbs by meaning, whatever the tense.

### 9. Subjects and pronouns
- Both languages may leave the subject in the verb. If the subject is implicit in both, only the verbs are linked.
- An explicit pronoun on one side only (Greek `εγω λεγω`, Arabic `اقول`) is linked to the verb together with it (1-N).
- An explicit noun subject missing on the other side is not aligned.
- Pronoun suffixes link to the Greek pronoun they render (`ه` to `αυτου`, `نا` to `ημων` or `ημας`, `كم` to `υμων` or
  `υμας`). The Arabic may generalise or shift person or number (`ημων` for `υμων`): if the suffix still fills the same place
  in the sentence, link it with `P`.
- A reflexive (`εν εαυτω`) may be a plain `به`: link the pronoun parts.

### 10. The verb "to be" and nominal sentences
The Arabic often uses a sentence without a verb where Greek has one (`εστιν`, `ην`). The Greek verb is then left unaligned.
Link a Greek `ειμι` to an Arabic copula or to `هو` only when one is actually written (`مبارك هو` for `ευλογητος`).

### 11. Prepositions
- A Greek preposition and its Arabic equivalent are aligned 1-1 (`εν` to `في` or `ب`, `δια` to `ب`, `εις` to `الى` or `ل`).
- The Arabic prepositions are flexible: `في` may render `εν` or `επι`; `عن` may render `υπερ` or `περι`; `ب` covers dative
  and instrumental senses. Link the preposition the translator chose for the same relation, even if it is not the usual
  one.
- If Greek has a preposition and the Arabic uses a construct state or the accusative with no preposition, leave the Greek
  preposition unaligned and link the nouns.
- A Greek prepositional phrase translated by a different Arabic structure (a verb, a clause): link the content words that
  carry the meaning.

### 12. Case and construct phrases
- A Greek genitive noun links to the noun that renders it in the Arabic construct (`ابو ربنا`) or after `ل`; the case itself
  is not a word.
- A Greek dative or accusative with no preposition may be rendered by `ل`, `ب` or a bare noun: link the nouns, and link
  the preposition only if the Greek has a word it corresponds to.
- When one Greek word is rendered by several Arabic words (or the reverse), align the whole group (1-N or N-1).

### 13. Particles and conjunctions
- An Arabic conjunction is a separate word in the parse (`و` in `والقوى`, `ف` in `فاما`) and is aligned with the Greek
  conjunction or particle it renders. The translator inserts and omits `و` and `ف` freely: an Arabic conjunction with no
  Greek counterpart is unaligned, and so is a Greek conjunction with no Arabic counterpart.
- `και` links to `و` or `ف` when both express the connection.
- `δε` links to `ف`, `و` or `اما` when it is rendered; `μεν` and `δε` are linked separately to their counterparts.
- `γαρ` links to `ف`, `لان` or `اذ`; `ουν` to `ف`; `αλλα` to `لكن` or `بل`; `η` to `او`; `οτι` to `ان` or `لان`; `ει` to
  `ان` or `اذا`.
- Particles that work together as one unit and are rendered by one expression are aligned as a group (N-N).

### 14. Vocabulary
The translator is lexically conservative: the same Greek word usually has the same Arabic equivalent (`χαρις` as `نعمة`,
`ευδοκια` as `مسرة`). Use the translation hints in the task. Do not link two words only because they look similar in
form; link them because they carry the same meaning in this sentence.

## Practical heuristics

- Prefer smaller links over larger ones. Group words only when the meaning is not compositional.
- Treat syntactic differences (participle as verb, case as preposition, noun phrase as nominal sentence, an
  inserted conjunction) as differences of structure, not of meaning: link what carries the meaning, leave the purely
  grammatical additions unaligned.
- Do not link a word because it is in the same position: the Arabic order often differs.
- Use `P` for a loose correspondence, and leave a word unlinked if you cannot say what it renders.

## Decision flow

1. Do the words share meaning in this sentence? No: leave unaligned.
2. Can they be linked 1-1? Yes: use 1-1.
3. Is the meaning spread over several words, or does one Arabic word contain several Greek words' meaning (a suffix, an
   article)? Yes: use 1-N, N-1 or N-N.
4. Is the unit indivisible? Yes: keep it grouped.
5. Is the element purely grammatical (an inserted conjunction, a case ending, an Arabic article)? Likely unaligned, unless the
   other language has a word it corresponds to.
