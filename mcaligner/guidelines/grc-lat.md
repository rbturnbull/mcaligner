# Greek–Latin Alignment Guidelines

## Core Principle
- Align **minimal units that preserve meaning**:
  - Use **single words** where possible.
  - Use **multi-word groups** only when necessary.
- Units must be:
  - **Semantically equivalent**
  - **Indivisible** (cannot be split without changing meaning)
- Allowed alignments:
  - 1–1, 1–N, N–1, N–N
- Unaligned items:
  - Leave them unaligned (no null links)

---

## General Rules

### 1. Punctuation
- Do **not align punctuation**
- Exception:
  - Apostrophes in genitives when semantically aligned

### 2. Omission & Incorrect Translation
- Do **not align**:
  - Words with **no semantic counterpart**
  - **Incorrect translations**
- If a word governs multiple items:
  - Align only with the **first relevant element**

### 3. Repetition
- If repeated in one language:
  - Align **only the first occurrence**

---

## Lexical Units

### 4. Idioms & Fixed Expressions
- Treat as **indivisible units**
- Align as **N–N**

### 5. Enclitics
- Align with host word as a **single unit** (N–1)

### 6. Quoted Source Words
- If untranslated and copied:
  - **Do not align**

---

## Determiners & Function Words

### 7. Articles (Greek vs Latin)
- Greek articles:
  - **Usually not aligned**
- Exception:
  - When translated as demonstratives → align

### 8. Pronominal / Adverbial Groups
- Align **entire group** when functioning as a unit

---

## Verbs & Syntax

### 9. Verbs and Subjects
- Explicit subject in both:
  - Align subject and verb separately (1–1)
- Implicit subject in both:
  - Align **verb only**
- Subject explicit in Latin only:
  - Pronoun → align with verb (1–N)
  - Noun → **do not align**

### 10. Verbs with Particles
- If Latin adds structural particles:
  - Align Greek verb → Latin verb + particle

---

## Participles

### 11. Genitive Absolute
- Align components **1–1**

### 12. Attributive Participles
- Prefer **1–1 alignment**
- Do not align Greek article

### 13. Substantive Participles
- If translated as clause:
  - Align article → pronoun
  - Align participle → verb
- If translated as noun:
  - Align **participle → noun only**

### 14. Participial Clauses
- Align as **1–N or N–N groups**

---

## Phrases & Case

### 15. Prepositional Phrases
- If structurally equivalent:
  - Align **1–1**
- If mismatch (case vs phrase):
  - Align as **1–N or N–1**

### 16. Case Constructions
- Greek inflected word → Latin phrase:
  - Align **1–N**
- Reverse:
  - Align **N–1**

---

## Functional Words

### 17. Particles & Function Words
- Align when **semantic equivalent exists**
- Combine particles into groups if:
  - They function as a **single semantic unit**

---

## Special Cases

### 18. Abbreviations
- Align abbreviated ↔ full form
- Punctuation allowed here (exception)

---

## Practical Heuristics for LLMs

- Prefer:
  - **Smaller alignments over larger ones**
- Only group words when:
  - Meaning is **non-compositional**
- Ignore:
  - Purely grammatical additions with no semantic counterpart
- Treat:
  - Syntax differences (case vs preposition, implicit vs explicit subjects) as **alignment transformations**
- When uncertain:
  - Favor **no alignment over incorrect alignment**

---

## Summary Decision Flow

1. Do words share meaning?
   - No → do not align
2. Can they align 1–1?
   - Yes → use 1–1
3. Is meaning distributed across words?
   - Yes → use N–N / 1–N / N–1
4. Is unit indivisible?
   - Yes → keep grouped
5. Is element purely grammatical?
   - Likely skip unless semantically matched
