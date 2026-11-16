"""Instructions and task prompts for the aligner and the scorer.

A task covers several sentence pairs. Each pair is rendered compactly: one line
per word (``id form lemma UPOS head deprel`` and glosses from MISC), the links
already settled, the links to review, and for each unlinked word how its lemma
is linked elsewhere (translation evidence). The answers are compact lines that
code checks and applies (see :mod:`mcaligner.agents.outputs`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mcparser.corpus import Sentence
from mcparser.corpus.alignment import Link

from ..lexicon import TranslationTable, lemma_of


@dataclass
class PairItem:
    """One sentence pair of a task."""

    sent_id: str
    a: Sentence
    b: Sentence
    settled: list[Link] = field(default_factory=list)
    """Links kept as they are (at or above the threshold)."""
    review: list[Link] = field(default_factory=list)
    """Links below the threshold (aligner) or links to score (scorer)."""

    @property
    def words(self) -> int:
        return len(self.a.words) + len(self.b.words)


ALIGNER = """\
You align the words of two versions of the same text: source A ({a}) and
source B ({b}), for example a translation and its original. Sentences are
paired by id. Words are numbered as in CoNLL-U; a multiword token (e.g. a word
with clitics) is split into syntactic words, and links join words, not tokens.

A link joins a word of A and a word of B that translate each other: "A-B S"
(sure) or "A-B P" (probable: a looser or partial correspondence, e.g. a
paraphrase). One-to-many and many-to-many alignments are several links (2-3 S
and 2-4 S when word 2 of A renders words 3 and 4 of B). A word may contain
morphemes that the parse did not split off (a pronoun suffix, an attached
preposition or article, the person of a verb): link it to every word it
renders, e.g. a verb with an object suffix "blessed-us" to both the verb and
the pronoun. Leave a word unlinked when it has no counterpart (a word the
translator added, or a function word the other language leaves out).

The task gives, for each pair: both sentences (id form lemma UPOS head deprel,
glosses where available), the settled links (by code rules or earlier work;
they are kept), links to review, and for unlinked words how their lemma is
linked elsewhere in the corpus. Follow that evidence unless the context rules
it out. Tools are available (get_parallel on alignment "{target}" or other sets
for aligned examples, translation_candidates for other lemmas with side="a" or
"b", similar_pairs, lemma_links, link_examples, alignment_stats, analyse_form,
find_tokens) but call them only when the evidence given is not enough, and make
independent calls in parallel. The prompt omits XPOS and FEATS: pair_words gives
every column of a pair's words, and category_links shows how words of a category
(UPOS, XPOS, FEATS such as Case=Gen, deprel) are usually linked or left unlinked.
Use them when the grammar decides a link (an article, a case against a
preposition, tense and voice, a participle).

Answer with ONE final result. In `links`, one line per link:
"SENT_ID A-B S|P CONFIDENCE", e.g. "B10K1V1 3-5 S 0.95". List every link of
each pair except the settled ones, which are kept automatically; a link to
review that you do not list is removed. To remove a settled link that is
wrong, put "SENT_ID A-B" in `remove`. Confidence: 0.95 or more = clear; 0.8 =
probable; 0.6 = doubtful; below 0.5 = a guess. Keep `summary` under 15 words.
"""

SCORER = """\
You check word alignments between two versions of the same text: source A
({a}) and source B ({b}). Sentences are paired by id; words are numbered as in
CoNLL-U. A link "A-B S|P" says that word A and word B translate each other
(S = sure, P = probable, a looser correspondence). A word may contain
morphemes the parse did not split off (a pronoun suffix, an attached
preposition, the person of a verb), so a link from such a word to a pronoun
or preposition on the other side is right when that morpheme renders it.

For each pair the task gives both sentences (id form lemma UPOS head deprel,
glosses where available), all its links, and the links to score. Rate each
link to score: how likely is it that these two words correspond in this
sentence? (Tools: pair_words for XPOS and FEATS, category_links for how a kind of
word is usually linked, similar_pairs, lemma_links, link_examples.) 0.95 or more = clearly right; 0.8 = probably right; 0.6 = doubtful;
below 0.5 = probably wrong (e.g. the wrong one of two similar words, or a word
that has a better counterpart). Links below {threshold} go back to the aligner.

Answer with ONE final result: in `scores`, one line per link to score,
"SENT_ID A-B CONFIDENCE", e.g. "B10K1V1 3-5 0.9". Keep `summary` under 15 words.
"""


def instructions(role: str, a: str, b: str, target: str, threshold: float, extra: str | None = None) -> str:
    template = ALIGNER if role == "aligner" else SCORER
    text = template.format(a=a, b=b, target=target, threshold=threshold)
    return f"{text}\n{extra.strip()}\n" if extra else text


def word_lines(sentence: Sentence, misc_keys: list[str]) -> list[str]:
    """``id form lemma UPOS head deprel [glosses]`` per word, and a line per multiword token."""
    lines = []
    for token in sentence.tokens:
        if token.is_multiword:
            lines.append(f"{token.id} {token.form} (token of words {token.id})")
        elif token.is_word:
            extra = [value for key in misc_keys if (value := token.misc_value(key))]
            lines.append(" ".join([token.id, token.form, token.lemma, token.upos, token.head, token.deprel, *extra]))
    return lines


def link_text(link: Link, confidence: float) -> str:
    agent = f" {link.agent}" if link.agent else ""
    return f"{link.ugarit()} {confidence:.2f}{agent}"


def evidence_lines(item: PairItem, table: TranslationTable, source_a: str, source_b: str, limit: int) -> list[str]:
    """For unlinked words (not punctuation): their lemma's linked lemmas elsewhere (this pair left out)."""
    if limit <= 0:
        return []
    linked_a = {link.source for link in item.settled + item.review}
    linked_b = {link.target for link in item.settled + item.review}
    lines = []
    for side, source, sentence, linked in (("A", source_a, item.a, linked_a), ("B", source_b, item.b, linked_b)):
        seen: set[str] = set()
        for word in sentence.words:
            lemma = lemma_of(word)
            if word.id in linked or lemma in seen or word.upos == "PUNCT":
                continue
            seen.add(lemma)
            entry = table.entry(source, lemma)
            if entry is None:
                continue
            candidates = entry.candidates(item.sent_id).most_common(limit)
            if not candidates:
                continue
            unlinked = entry.unaligned_without(item.sent_id)
            shown = ", ".join(f"{value}×{count}" for value, count in candidates)
            note = f"of {entry.occurrences_without(item.sent_id)}" + (f", {unlinked} unlinked" if unlinked else "")
            lines.append(f"{side}{word.id} {lemma}: {shown} ({note})")
    return lines


def pair_block(
    item: PairItem,
    role: str,
    confidence: dict[str, float],
    table: TranslationTable | None,
    names: tuple[str, str],
    misc_keys: list[str],
    candidates: int,
) -> str:
    """The text of one pair in a task prompt."""
    lines = [f"## Pair {item.sent_id}", f"A: {item.a.text}"]
    lines += word_lines(item.a, misc_keys)
    lines += [f"B: {item.b.text}", *word_lines(item.b, misc_keys)]
    settled = ", ".join(link_text(link, confidence[link.key]) for link in item.settled) or "none"
    lines.append(f"Settled links: {settled}")
    if role == "aligner":
        if item.review:
            lines.append("Links to review: " + ", ".join(link_text(link, confidence[link.key]) for link in item.review))
        hints = evidence_lines(item, table, *names, candidates) if table is not None else []
        if hints:
            lines += ["Evidence for unlinked words (linked lemmas elsewhere):", *hints]
    else:
        forms_a = {word.id: word.form for word in item.a.words}
        forms_b = {word.id: word.form for word in item.b.words}
        lines.append("Links to score:")
        lines += [f"{link.ugarit()} {forms_a[link.source]}→{forms_b[link.target]}" for link in item.review]
    return "\n".join(lines)


def task_prompt(
    role: str,
    items: list[PairItem],
    confidence: dict[str, dict[str, float]],
    table: TranslationTable | None,
    names: tuple[str, str],
    misc_keys: list[str],
    candidates: int,
) -> str:
    header = (
        f"Align these {len(items)} sentence pairs." if role == "aligner" else f"Score the listed links of these {len(items)} sentence pairs."
    )
    blocks = [pair_block(item, role, confidence[item.sent_id], table, names, misc_keys, candidates) for item in items]
    return "\n\n".join([header, *blocks])
