# Greek–Coptic Alignment Guidelines (Sahidic New Testament)

Written in the spirit of the BICROSS Greek–Latin guidelines (which derive from the Ugarit guidelines), adapted to a Sahidic
Coptic translation of a Greek Vorlage: literal in vocabulary, with a very different grammar. The Greek is New Testament text
(unaccented, lowercase, no punctuation); the Coptic is the translation. Source A is Greek, source B is Coptic. A draft for
review: it has not been checked against a human gold alignment.

## General Principles

- Align the **smallest units that preserve the meaning**: single words wherever possible, groups only when necessary.
- The two sides must bear the **same meaning** and the link should involve as few words as possible, but as many as necessary.
- Allowed links: one-to-one (1-1), one-to-many (1-N), many-to-one (N-1) and many-to-many (N-N).
- Words that do not correspond are left **unaligned** (there are no null links).
- Align what the translator **wrote**, not what you think the Greek should have produced. Coptic word order differs from
  Greek (verb first, pronoun subject inside the verb complex): expect crossing links.
- Use `S` for a clear correspondence and `P` for a looser one (a paraphrase, a shifted person or number, a different
  Vorlage reading that still fills the same place in the sentence).
- When uncertain, prefer **no alignment over a wrong one**.

## The Coptic words in the parse

Coptic is written in bound groups, and the parse splits each group into syntactic words (shown as `5-8 ⲉⲡⲛⲁⲩ (token of
words 5-8)` followed by the words). Articles (`ⲡ` `ⲧ` `ⲛ` `ⲟⲩ`), prepositions (`ⲉ` `ⲛ` `ϩⲛ` `ⲙ`), tense and mood
auxiliaries (`ⲁ` `ⲛⲉⲣⲉ` `ⲛⲁ` `ⲙⲡⲉ`), subject pronouns (`ϥ` `ⲟⲩ` `ⲧⲉⲧⲛ`) and suffix pronouns are separate words, so each can be
linked on its own. A word may still contain morphemes the parse did not split: link it to **every Greek word it renders**.
Words in the bound group are not words of the sentence: link the words, never the group line.

Coptic words in the parse have their **lemma in the Coptic script** (`ⲛⲧⲟϥ` for every `ϥ`, a lemma shared by all persons), so
the lemma alone does not tell you the person: read the FEATS or the form.

## Guidelines

### 1. Punctuation
Punctuation is never aligned. The Greek has none.

### 2. Words with no equivalent
- A word that appears in only one language and has no counterpart in the other is not aligned: a word the translator added,
  or a Greek word the Coptic leaves out.
- A wrong or purely explanatory rendering is not aligned.
- If one word governs several items (a preposition before two nouns) and appears only once on one side, it links to the
  first item only.

### 3. Repetition
When a word is repeated in one language but not in the other, only the first instance is aligned. Exception: the translator
repeats words for emphasis or clarity (a preposition repeated before each noun in Coptic, `ⲛ...ⲛ`): then each Coptic word
links to its own Greek counterpart.

### 4. Fixed expressions and idioms
If several words together form one unit of meaning that no single word translates, align them as a group (N-N).
Coptic has many light-verb compounds (`ⲉⲣ ϩⲱⲃ` "do work", `ϫⲓ ⲙⲧⲟⲛ`, `ⲉⲓⲣⲉ ⲛ-` plus noun): when the compound renders one Greek
verb, link the Greek verb to the Coptic verb and its noun (1-N).

### 5. Proper names and titles
- Names are borrowed or transliterated (`ⲓⲏⲥⲟⲩⲥ` Jesus, `ⲡⲉⲝⲣⲥ` or `ⲡⲉⲭⲣⲓⲥⲧⲟⲥ` Christ, `ⲙⲱⲩⲥⲏⲥ` Moses): link them 1-1 with the
  Greek name. Sacred names are written in abbreviated form (nomina sacra, `ⲓⲥ`, `ⲡⲉⲭⲥ`, `ⲡⲛⲟⲩⲧⲉ`): they still link to the
  Greek word they render (`θεος` to `ⲛⲟⲩⲧⲉ`, `κυριος` to `ⲡϫⲟⲉⲓⲥ`).
- Link by name, not by position: when the order differs (`ιησους χριστος` and `ⲡⲉⲭⲣⲓⲥⲧⲟⲥ ⲓⲏⲥⲟⲩⲥ`) the links cross.

### 6. Definite and indefinite article
- The Greek article is aligned with the **Coptic article** (`ⲡ` `ⲧ` `ⲛ`, the possessive articles `ⲡⲁ` `ⲡⲉϥ` `ⲧⲉⲧⲛ`, and the demonstrative
  `ⲡⲁⲓ`, `ⲡⲉⲓ`), and both are kept **separate from the noun**: article to article, noun to noun.
- Coptic articles are separate words in the parse, so each Greek article links to its own Coptic article.
- Link the article only when **both** languages have one. Coptic uses the article where Greek has none (nouns after
  prepositions, with a proper name) and omits it in places where Greek has one: then the article is left unaligned and the
  nouns are still linked.
- The Coptic indefinite article `ⲟⲩ` (and plural `ϩⲉⲛ`) is aligned with the Greek word for "a" (`τις`, `εις`), if present; otherwise
  it is left unaligned and the noun is linked.
- A Greek article introducing a participle, adjective or phrase (`ο λεγων`, `ο εκ`) is rendered by the Coptic relative
  `ⲉⲧ-` or `ⲡⲉⲧ-`/`ⲛⲉⲧ-` (the article with a relative): link the Greek article to the Coptic article part (`ⲡ` in `ⲡⲉⲧ-`),
  and the participle to the verb. A Coptic relative converter `ⲉⲧ` or `ⲉⲧⲉ` is linked to a Greek relative pronoun (`ος`, `ο`).
- Greek `ο`, `η`, `το` used as a pronoun (`ο δε` "and he") links to the Coptic pronoun or to the word that renders it.
- Greek `τα` before a plural or a neuter with a genitive (`τα του θεου`) is rendered by `ⲛⲁ` or `ⲛⲉⲧ`: link it to the
  Coptic word that carries the plural article or relative.

### 7. Relative clauses and substantive participles
- Greek relatives (`ος`, `η`, `ο`, `οστις`) are rendered by the Coptic relative converter `ⲉⲧⲉ`/`ⲉⲧ`/`ⲉⲛⲧ` or the relative `ⲛⲧⲁ` plus
  a pronoun: link the relative pronoun to the converter, and the resumptive pronoun in Coptic (a suffix `ϥ` or `ⲟⲩ` inside the
  relative clause) stays unaligned unless the Greek has a corresponding pronoun.
- The Greek article with a participle ("the one who ...") is often rendered `ⲡⲉⲧ-` plus the verb or `ⲡⲉⲛⲧⲁϥ-` plus verb: link the
  article to `ⲡ`/`ⲡⲉⲧ`, and the participle to the verb.

### 8. The verb complex
Coptic verbs are made of **auxiliary + subject + verb**: `ⲁ ϥ ϫⲛⲟⲩ` (`ⲁ` perfect, `ϥ` "he", `ϫⲛⲟⲩ` "ask").
- The Greek verb links to the Coptic verb (1-1). The auxiliary (`ⲁ`, `ⲛⲉⲣⲉ`, `ⲛⲁ`, `ⲉⲣϣⲁⲛ`, `ⲙⲡⲉ`) carries tense, mood or negation
  and is **not** linked unless the Greek has a word it renders: Greek `ου` "not" links to the negative `ⲙⲡⲉ`, `ⲙⲛ`, `ⲁⲛ`, `ⲧⲙ`;
  Greek `μη` to `ⲙⲡⲣ`, `ⲧⲙ`.
- The subject pronoun `ϥ` `ⲥ` `ⲟⲩ` `ⲧⲉⲧⲛ` etc. is linked to the Greek subject pronoun only if one is written. If the subject is
  implicit in Greek (inside the verb ending), only the verbs are linked; the Coptic subject pronoun is left unaligned. If
  Greek has an explicit pronoun (`εγω λεγω`) and Coptic has `ⲁⲛⲟⲕ`, link them; if Coptic has only the verb complex, link the
  Greek pronoun to the Coptic subject pronoun.
- Greek tenses do not map to the Coptic tense system: link verbs by meaning, whatever the tense. Greek `αν` and `εαν` link to
  the Coptic conditional `ⲉϣⲱⲡⲉ`, `ⲉⲣϣⲁⲛ` if rendered.
- Greek participles are often rendered as a finite verb with a circumstantial (`ⲉ` plus pronoun) or a coordinated verb (`ⲁϥ` or
  `ⲁⲩⲱ ⲁϥ`): link the participle to the verb that carries its meaning. The `ⲁⲩⲱ` is linked to a Greek `και` only if the Greek has
  one.
- Greek infinitives link to the Coptic infinitive or to the verb of a `ϫⲉⲕⲁⲥ`/`ⲉ` clause (`ινα` to `ϫⲉⲕⲁⲥ`).
- Greek passives and middles are rendered by an active with an impersonal subject (`ⲁⲩ-`): link the verbs.

### 9. Pronouns
- Coptic suffix pronouns (`ϥ`, `ⲥ`, `ⲟⲩ`, `ⲕ`, `ⲧⲉⲧⲛ`, `ⲛ`) after prepositions or verbs are separate words, linked to the Greek pronoun they
  render (`αυτου`, `αυτω`, `αυτον`, `ημας`, `υμιν`). A preposition with a suffix (`ⲛⲁϥ`, `ⲉⲣⲟϥ`, `ⲛⲙⲙⲁϥ`) is the preposition word plus
  the pronoun word: link the preposition to the Greek preposition (or case) and the suffix to the Greek pronoun.
- Greek case (dative `αυτω`) corresponds to `ⲛⲁ` plus pronoun: link `αυτω` to the pronoun, and leave `ⲛⲁ` unaligned
  unless a Greek preposition renders it.
- The possessive article (`ⲡⲉϥⲣⲁⲛ` "his name") is `ⲡⲉϥ` (article plus possessive in one word) plus noun; link Greek `αυτου` to `ⲡⲉϥ`
  (1-N is possible: link both the article and the possessive to `το` and `αυτου` where Greek has both).
- A Coptic independent pronoun (`ⲁⲛⲟⲕ`, `ⲛⲧⲟⲕ`, `ⲛⲧⲟϥ`) links to the Greek pronoun (`εγω`, `συ`, `αυτος`).
- Greek `ουτος`, `εκεινος` link to the Coptic demonstrative (`ⲡⲁⲓ`, `ⲡⲉⲧⲉⲙⲙⲁⲩ`, `ⲡⲉⲓ`): link the demonstrative, and the noun it
  qualifies separately.

### 10. The verb "to be" and nominal sentences
Coptic has nominal sentences (`ⲡⲁⲓ ⲡⲉ ⲡϩⲱⲃ`, "this is the work") with a copula `ⲡⲉ`, `ⲧⲉ`, `ⲛⲉ` at the end, and a noun sentence
without a verb. Link Greek `ειμι` (`εστιν`, `ην`) to the copula or to `ⲛⲉ`, `ⲡⲉ`, `ⲧⲉ`, `ⲛⲉ` when it is written. Where the Coptic has no copula, the
Greek verb is left unaligned. Existential `ⲟⲩⲛ` or `ⲙⲛ` links to `εστιν` or `ουκ εστιν` when the translator wrote it. A Coptic
auxiliary `ⲛⲉⲣⲉ` or `ⲛⲉ` with "was" is linked to Greek `ην` when `ην` is a copula or auxiliary.

### 11. Prepositions
- A Greek preposition and its Coptic equivalent are aligned 1-1 (`εν` to `ϩⲛ`, `εις` to `ⲉ` or `ⲉⲣⲁⲧ`, `προς` to `ⲉϫⲛ`, `ⲉⲣⲟ`, `ⲛⲁ`, `εκ` to `ⲛⲧⲟⲟⲧ`
  or `ϩⲓ`, `δια` to `ϩⲓⲧⲛ` or `ϩⲛ`, `περι` to `ⲉⲧⲃⲉ` or `ϩⲉⲛ`).
- Coptic has few prepositions and they are flexible: `ⲉ` may render `εις`, `προς`, `επι`; `ϩⲛ` may render `εν`, `εκ`, `δια`. Link the one the
  translator chose for the same relation, even if it is not the usual one.
- The Coptic genitive marker `ⲛ` ("of") between nouns (`ⲛⲉϩⲃⲏⲩⲉ ⲙⲡⲛⲟⲩⲧⲉ`) corresponds to the Greek genitive, which is a case and not a
  word: leave it unaligned and link the nouns. The direct-object marker `ⲙ`/`ⲛ` (`ⲙⲡⲛⲟⲩⲧⲉ`) is also left unaligned.
- If Greek has a preposition and the Coptic has none, leave the Greek preposition unaligned and link the nouns.

### 12. Case and construct phrases
- A Greek genitive noun links to the noun that renders it in the Coptic `ⲛ`-phrase or possessive; the case itself is not a word.
- A Greek dative or accusative with no preposition may be rendered by `ⲛ`/`ⲙ` or a bare noun: link the nouns, and link the
  preposition only if the Greek has a word it corresponds to.
- When one Greek word is rendered by several Coptic words (or the reverse), align the whole group (1-N or N-1).

### 13. Particles and conjunctions
- Coptic conjunctions and particles (`ⲁⲩⲱ`, `ⲇⲉ`, `ϭⲉ`, `ⲅⲁⲣ`, `ϫⲉ`, `ⲉⲧⲃⲉ ⲡⲁⲓ`, `ⲁⲗⲗⲁ`, `ϩⲁⲙⲏⲛ`) are separate words and linked to the
  Greek conjunction or particle they render. The translator inserts and omits `ⲁⲩⲱ`, `ⲇⲉ` and `ϭⲉ` freely: a Coptic conjunction with
  no Greek counterpart is unaligned, and so is a Greek conjunction with no Coptic counterpart.
- `και` links to `ⲁⲩⲱ` or `ⲇⲉ` when both express the connection; `δε` to `ⲇⲉ`, `ϭⲉ` or `ⲁⲩⲱ`; `μεν` and `δε` are linked separately to their
  counterparts; `γαρ` to `ⲅⲁⲣ`; `ουν` to `ϭⲉ` or `ⲉⲧⲃⲉ ⲡⲁⲓ`; `αλλα` to `ⲁⲗⲗⲁ`; `η` to `ⲏ`; `οτι` to `ϫⲉ`; `ινα` to `ϫⲉⲕⲁⲥ`; `ει` to `ⲉϣⲱⲡⲉ`, `ⲉϣϫⲉ`;
  `ως` and `καθως` to `ⲕⲁⲧⲁ ⲑⲉ ⲉⲧⲉ` or `ⲑⲉ ⲉⲧⲉ`.
- The Coptic quotation particle `ϫⲉ` ("that", "saying") introduces speech and links to Greek `οτι` or `λεγων`/`λεγουσα` when
  they carry the same function; otherwise it is left unaligned.
- Particles that work together as one unit and are rendered by one expression are aligned as a group (N-N).
- Coptic `ⲛϭⲓ` (the focus marker for a postposed subject) has no Greek counterpart: leave it unaligned.

### 14. Vocabulary
Coptic keeps many Greek loanwords (`ⲅⲁⲣ`, `ⲇⲉ`, `ⲁⲗⲗⲁ`, `ⲡⲛⲉⲩⲙⲁ`, `ⲡⲓⲥⲧⲉⲩⲉ`, `ⲉⲡⲓⲥⲧⲉⲩⲉ`, `ⲉⲕⲕⲗⲏⲥⲓⲁ`): such a Coptic word links to the same
Greek word when the Greek text has it, and to its actual Greek counterpart otherwise. The translator is lexically conservative: the
same Greek word usually has the same Coptic equivalent. Use the translation hints in the task. Do not link two words only
because they look similar in form; link them because they carry the same meaning in this sentence.

## Practical heuristics

- Prefer smaller links over larger ones. Group words only when the meaning is not compositional.
- Treat syntactic differences (participle as finite verb, tense auxiliary, case as `ⲛ` or `ⲙ`, an inserted conjunction, a
  nominal sentence) as differences of structure, not of meaning: link what carries the meaning, leave the purely
  grammatical additions unaligned.
- Do not link a word because it is in the same position: the Coptic order often differs.
- Use `P` for a loose correspondence, and leave a word unlinked if you cannot say what it renders.

## Decision flow

1. Do the words share meaning in this sentence? No: leave unaligned.
2. Can they be linked 1-1? Yes: use 1-1.
3. Is the meaning spread over several words, or does one Coptic word contain several Greek words' meaning? Yes: use 1-N, N-1 or N-N.
4. Is the unit indivisible? Yes: keep it grouped.
5. Is the element purely grammatical (a tense auxiliary, a genitive `ⲛ`, an object marker, an inserted conjunction)? Likely unaligned,
   unless the other language has a word it corresponds to.
