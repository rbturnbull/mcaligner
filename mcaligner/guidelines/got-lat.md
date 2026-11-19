# Gothic–Latin Alignment Guidelines (draft)

Draft adapted from the grc-lat guidelines for the Gothic Bible (translated from Greek) and the Old Latin (Vetus Latina)
text of the same New Testament passage. Both texts are translations of the same Greek, so most words correspond;
differences come from the languages (Latin has no article and drops subject pronouns), from different Greek readings,
and from free renderings. There is no Greek in the data: align Gothic to Latin directly.

## Core Principle
- Align **minimal units that preserve meaning**:
  - Use **single words** where possible.
  - Use **multi-word groups** only when necessary.
- Units must be **semantically equivalent** and **indivisible** (cannot be split without changing the meaning).
- Allowed alignments: 1–1, 1–N, N–1, N–N.
- Words with no counterpart stay **unaligned** (no null links).
- When uncertain, **prefer no link to a wrong link**.

## Using the annotation
- Match by **meaning of the lemma**, not by form or position. Gothic lemmas come from the treebank and are
  reliable where the word is covered by it; the Latin lemmas are predictions and may be wrong, so check the form.
- Use UPOS, FEATS and the syntax to see which words belong together (a noun with its dependent genitive, a verb with its
  auxiliary), not to decide whether two words match: grammatical categories differ between the languages
  (Gothic optative vs Latin subjunctive, Gothic periphrastic vs Latin synthetic passive).
- Spelling variation in the Latin manuscript (`u`/`v`, `i`/`j`, missing diphthongs, expanded abbreviations such as
  `deus`, `dominus`, `iesus`, `christus`) does not matter; align by meaning.

## General Rules

### 1. Punctuation
- Do **not** align punctuation.

### 2. No counterpart, different reading or free translation
- Do **not** align words that have no counterpart in the other text. This is common: the two manuscripts can follow
  different Greek readings, add or omit words, or paraphrase.
- Do **not** align words that translate something different (an incorrect or very free rendering).
- A pronoun or determiner that one text replaces by the noun it refers to is **not aligned** with that noun.
- A word that governs several items but appears once in one text (a preposition before two nouns) is linked to the first
  item only.

### 3. Repetition
- If a word is repeated in one text but not in the other, align only the **first** occurrence.

## Lexical Units

### 4. Idioms and fixed expressions
- Treat as **indivisible** units and align N–N (e.g. Gothic `bi þatei` ~ Latin `secundum quod`; an `amen` formula).

### 5. Gothic enclitics and fused particles
- A Gothic token may carry an enclitic: `-uh` (and, but: `immuh`, `þanuh`), `-u` (question), `-hun` (after `ni`: `ni … ƕashun`),
  `-ei` (relative or complementiser: `saei`, `þatei`, `ei`), `-ah`. Align the **whole token** as one unit with the Latin
  word(s) that express all of it (N–1 or 1–N). Example: `immuh` ~ `illi autem`; `ni ƕashun` ~ `nemo`.
- Latin enclitics (`-que`, `-ne`, `-ue`, `-met`) are likewise kept with their host.

### 6. Names and loanwords
- Names and Greek loanwords (`iesus`, `xristus`, `paulus`, `aggilus`) align with their Latin counterparts, even when the
  spelling differs.

## Function words

### 7. The Gothic demonstrative used as an article
- `sa`, `so`, `þata` (and their forms) often render the Greek article. Latin has no article, so they are **left
  unaligned**.
- Align them only when Latin has a real demonstrative or pronoun (`is`, `ille`, `hic`, `qui`) that translates them.

### 8. Pronouns and subjects
- Explicit subject in both: align subject and verb separately (1–1).
- Subject pronoun explicit in Gothic only (`ik`, `þu`, `weis`, `jus`): link it **together with its verb** to the Latin verb (N–1).
- Subject pronoun explicit in Latin only: link it with the Gothic verb (1–N).
- A noun subject that appears in only one text is **not aligned**.
- Reflexives and reciprocals (`sik`, `sis`, `izwis misso` ~ `se`, `inuicem`) follow meaning; align when both have them.

### 9. Relative and complementiser words
- Gothic relatives `saei`, `sa þei`, `þatei`, `þoei` and Latin `qui`, `quae`, `quod` align 1–1 as relative pronouns.
- Gothic `þatei` as a complementiser ~ Latin `quia`, `quoniam`, `quod`; `ei` ~ `ut`, `ne`, `quod`, `quia`; `ƕa`, `ƕas`, `ƕan`, `ƕaiwa`
  ~ `quid`, `quis`, `quando`, `quomodo`, `quam`.
- Do not align a conjunction with a pronoun merely because they occupy the same position.

### 10. Conjunctions and particles
- Align when a semantic equivalent exists; typical pairs (not obligatory, check the sentence):
  `jah` ~ `et`, `ac`, `etiam`; `ak` ~ `sed`; `iþ`, `þan`, `than` ~ `autem`, `uero`; `auk` ~ `enim`, `nam`; `nu`, `nuh` ~ `ergo`, `igitur`, `itaque`;
  `unte` ~ `quia`, `quoniam`, `enim`; `aiþþau` ~ `aut`, `uel`, `siue`; `swaswe`, `swe` ~ `sicut`, `quasi`, `tamquam`; `ni` ~ `non`, `ne`;
  `nih` ~ `neque`, `nec`; `ni … ni` ~ `neque … neque`; `jabai` ~ `si`; `ibai` ~ `numquid`, `ne`.
- Combine particles into one group when they function as a single unit (`jah … jah` ~ `et … et`, `ni … ak` ~ `non … sed`).
- A particle with no semantic equivalent (emphatic `auk`, `þan`, `nu` used as filler) stays unaligned.

### 11. Prepositions and cases
- Preposition for preposition: align 1–1 and align the nouns separately (`in þamma` … `in` + ablative noun).
- Gothic case alone vs Latin preposition (or the reverse): align the noun with **noun + preposition** (1–N or N–1).
- The Gothic dative or genitive of a noun that Latin renders with a preposition or a different case is still aligned by meaning.
- `du` + dative or infinitive ~ `ad`, `in`, `ut`, `ut … possit`: align when it has a clear counterpart, otherwise leave it.

## Verbs and Syntax

### 12. Verbs
- Align the lexical verb to the lexical verb; the grammatical category (mood, tense, voice) does not decide the link.
- **Periphrastic forms**: Gothic auxiliary + participle (`wairþiþ`, `was` + past participle) vs a single Latin form:
  link auxiliary **and** participle to the Latin verb (N–1). The reverse (Latin periphrastic, Gothic single form) is 1–N.
- **Prefixed verbs** (`ga-`, `us-`, `fra-`, `and-`, `bi-`) are single words; do not split them.
- Modal and auxiliary verbs (`maht`, `skal`, `wiljan`, `haban` + infinitive) are aligned with the Latin verb or form that expresses
  the same meaning; if Latin has no counterpart, leave them unaligned.
- Gothic infinitive vs Latin `ut`-clause, gerund or gerundive: align the lexical verbs and, if present, the matching
  conjunction (`du`/`ei` ~ `ut`).

### 13. Participles
- Attributive participle ~ participle or relative clause: link the participle to the Latin participle or verb (1–1) and leave the article unaligned.
- Substantive participle (`sa …-ands`, `þai …-andans`): if Latin uses a relative clause, link the demonstrative to `qui` and the participle to the verb; if Latin uses a
  noun or a participle, link the participle with it only.
- Absolute constructions (Gothic dative absolute, Latin ablative absolute): align component by component (1–1).

### 14. Negation and quantifiers
- `ni … hun`, `ni ainshun`, `ni ƕashun`, `ni ƕaiwa` ~ `nemo`, `nullus`, `nihil`, `nequaquam`: align the group (N–1) when Latin has a single word.
- `all-`, `alls`, `manags`, `sums`, `ainzu` follow the Latin quantifier of the same meaning.

### 15. Possessives and genitives
- Gothic possessive (`meins`, `izwar`, `unsar`) ~ Latin possessive (`meus`, `uester`, `noster`) 1–1.
- Gothic possessive vs Latin genitive pronoun, or the reverse, is still 1–1 by meaning.
- Genitive noun ~ genitive noun 1–1; Gothic genitive vs Latin `de` + ablative is 1–N.

## Practical heuristics

- Prefer **smaller** links over larger ones; group only when the meaning is non-compositional.
- Ignore purely grammatical additions with no semantic counterpart (Gothic article, Latin supporting `est`, expletives).
- Treat syntax differences (case vs preposition, explicit vs implicit subject, periphrastic vs synthetic verb) as alignment
  **transformations**, not as reasons to drop a link.
- Where the two manuscripts clearly differ in content, leave the extra words unaligned.
- When uncertain: **no link** is better than a wrong link.

## Decision flow
1. Do the words share meaning? No → leave unaligned.
2. Can they align 1–1? Yes → 1–1.
3. Is the meaning spread over several words? Yes → 1–N, N–1 or N–N, keeping the groups as small as possible.
4. Is the unit indivisible (enclitic, prefixed verb, periphrasis, idiom)? Yes → keep it together.
5. Is the element purely grammatical (article, auxiliary, expletive)? Likely skip, unless the other text has a matching word.
