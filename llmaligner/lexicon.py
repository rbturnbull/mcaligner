"""Which lemmas translate which: a translation table built from alignment sets.

:class:`TranslationTable` counts, for every lemma of every aligned source,
which lemmas of the other source its words are linked to. It is the same count
as MCParser's ``translation_candidates`` tool (a word's lemma falls back to its
form; only links with at least ``min_confidence`` count), but built in one
pass over the sets, so code can look up thousands of words cheaply. The counts
of each sentence are kept, so a sentence's own links can be left out
(``exclude``, a ``sent_id``) when the table is used as evidence for that
sentence pair.

:func:`build_lexicon` turns the table into the exported lexicon.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from mcparser.corpus import CorpusStore, NotFoundError, Token
from mcparser.corpus.conllu import EMPTY

def lemma_of(word: Token) -> str:
    """The word's lemma, or its form if the lemma is empty (as in MCParser)."""
    return word.lemma if word.lemma != EMPTY else word.form


@dataclass
class Entry:
    """One lemma of one source."""

    occurrences: int = 0
    unaligned: int = 0
    pos: Counter[str] = field(default_factory=Counter)
    translations: Counter[str] = field(default_factory=Counter)
    by_sentence: dict[str, Counter[str]] = field(default_factory=dict)
    """Translations counted in each sentence (to leave one out)."""
    occurrences_by_sentence: Counter[str] = field(default_factory=Counter)
    unaligned_by_sentence: Counter[str] = field(default_factory=Counter)

    def candidates(self, exclude: str | None = None) -> Counter[str]:
        """Translations, without those counted in sentence ``exclude``."""
        if exclude is None or exclude not in self.by_sentence:
            return self.translations
        return self.translations - self.by_sentence[exclude]

    def occurrences_without(self, exclude: str | None = None) -> int:
        return self.occurrences - (self.occurrences_by_sentence[exclude] if exclude is not None else 0)

    def unaligned_without(self, exclude: str | None = None) -> int:
        return self.unaligned - (self.unaligned_by_sentence[exclude] if exclude is not None else 0)

    @property
    def part_of_speech(self) -> str | None:
        return self.pos.most_common(1)[0][0] if self.pos else None


class TranslationTable:
    """Lemma → linked-lemma counts for every source of the given alignment sets (default all)."""

    def __init__(self, store: CorpusStore, alignments: Iterable[str] | None = None, min_confidence: float = 0.0):
        self.store = store
        self.names = list(alignments) if alignments is not None else list(store.alignments)
        self.min_confidence = min_confidence
        self.entries: dict[str, dict[str, Entry]] = {}
        """source name → lemma → entry."""
        self.pos: dict[str, dict[str, Counter[str]]] = {}
        """source name → lemma → UPOS counts over the whole source (aligned or not)."""
        for name in self.names:
            self._add_set(name)

    def _add_set(self, name: str) -> None:
        aset = self.store.alignment(name)
        for source in (aset.source_a, aset.source_b):
            if source.name not in self.pos:
                counts: dict[str, Counter[str]] = {}
                for sentence in source.sentences:
                    for word in sentence.words:
                        if word.upos != EMPTY:
                            counts.setdefault(lemma_of(word), Counter())[word.upos] += 1
                self.pos[source.name] = counts
        for sent_id, links in aset.pairs.items():
            try:
                a, b = aset.source_a.sentence(sent_id), aset.source_b.sentence(sent_id)
            except NotFoundError:
                continue  # a pair whose sentence was removed from a source
            kept = [link for link in links if aset.confidence(link) >= self.min_confidence]
            self._add_side(aset.source_a.name, sent_id, a.words, b.words, [(l.source, l.target) for l in kept])
            self._add_side(aset.source_b.name, sent_id, b.words, a.words, [(l.target, l.source) for l in kept])

    def _add_side(self, source: str, sent_id: str, here: list[Token], there: list[Token], links: list[tuple[str, str]]) -> None:
        other = {word.id: word for word in there}
        linked: dict[str, list[str]] = {}
        for mine, theirs in links:
            linked.setdefault(mine, []).append(theirs)
        entries = self.entries.setdefault(source, {})
        for word in here:
            entry = entries.setdefault(lemma_of(word), Entry())
            entry.occurrences += 1
            entry.occurrences_by_sentence[sent_id] += 1
            if word.upos != EMPTY:
                entry.pos[word.upos] += 1
            partners = [lemma_of(other[i]) for i in linked.get(word.id, []) if i in other]
            if not partners:
                entry.unaligned += 1
                entry.unaligned_by_sentence[sent_id] += 1
            for partner in partners:
                entry.translations[partner] += 1
                entry.by_sentence.setdefault(sent_id, Counter())[partner] += 1

    def entry(self, source: str, lemma: str) -> Entry | None:
        return self.entries.get(source, {}).get(lemma)

    def candidates(self, source: str, lemma: str, exclude: str | None = None) -> Counter[str]:
        entry = self.entry(source, lemma)
        return entry.candidates(exclude) if entry else Counter()

    def part_of_speech(self, source: str, lemma: str) -> str | None:
        counts = self.pos.get(source, {}).get(lemma)
        return counts.most_common(1)[0][0] if counts else None


def build_lexicon(table: TranslationTable, min_count: int = 1, top: int | None = None) -> dict[str, dict[str, dict]]:
    """``{source: {lemma: {part_of_speech, occurrences, unaligned, alignments: {lemma: {count, part_of_speech}}}}}``.

    Lemmas are sorted; translations by count (most frequent first), keeping
    those seen at least ``min_count`` times (and at most ``top`` of them).
    """
    other_of: dict[str, str] = {}
    for name in table.names:
        aset = table.store.alignment(name)
        other_of.setdefault(aset.source_a.name, aset.source_b.name)
        other_of.setdefault(aset.source_b.name, aset.source_a.name)
    lexicon: dict[str, dict[str, dict]] = {}
    for source, entries in table.entries.items():
        other = other_of[source]
        out: dict[str, dict] = {}
        for lemma in sorted(entries):
            entry = entries[lemma]
            kept = [(value, n) for value, n in entry.translations.most_common() if n >= min_count][:top]
            out[lemma] = {
                "part_of_speech": entry.part_of_speech,
                "occurrences": entry.occurrences,
                "unaligned": entry.unaligned,
                "alignments": {
                    value: {"count": n, "part_of_speech": table.part_of_speech(other, value)} for value, n in kept
                },
            }
        lexicon[source] = out
    return lexicon
