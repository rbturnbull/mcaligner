"""Link near-certain word pairs in code, without a model.

Rules only add links between words that have no link yet, and only when the
match is unique in the sentence pair. They are:

* **identical** — punctuation, numerals and symbols (or other forms without
  letters) written the same on both sides;
* **names** — a proper noun on one side whose romanisation matches a word on
  the other side (consonant skeletons; the Arabic MISC ``LTranslit=`` /
  ``Translit=`` are used when present, Greek is romanised from the lemma);
* **lexicon** — a lemma whose translation is overwhelming in the evidence (at
  least ``min_count`` linked occurrences, and that translation for at least
  ``min_share`` of all its occurrences, unlinked ones included), when the
  translation occurs exactly once in the other sentence and the lemma exactly
  once in this one.

Evidence for the lexicon rule is a :class:`~llmaligner.lexicon.TranslationTable`
over the given alignment sets, counting only links with confidence of at least
``evidence_confidence`` (read-only sets default to 1.0). Rules write links with
confidence :data:`RULE_CONFIDENCE`, below that, so they never feed themselves;
the sentence being linked is always left out of the evidence.

:func:`measure` proposes links for the pairs of a reference set (starting from
no links, as at the start of a run) and reports each rule's precision against it.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from difflib import SequenceMatcher

from mcparser.corpus import CorpusStore, Sentence, Token
from mcparser.corpus.alignment import Link
from pydantic import BaseModel, Field

from .lexicon import TranslationTable, lemma_of

RULE_AGENT = "rules"
RULE_CONFIDENCE = 0.95
IDENTICAL_CONFIDENCE = 0.98
EVIDENCE_CONFIDENCE = 0.96
"""Links count as lexicon evidence from this confidence (above what rules set)."""

SYMBOL_TAGS = frozenset({"PUNCT", "NUM", "SYM"})
FUNCTION_TAGS = frozenset({"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "PUNCT", "SCONJ", "SYM"})
"""Words that are never the counterpart of a proper name."""
TRANSLIT_KEYS = ("LTranslit", "Translit")

GREEK = dict(zip("αβγδεζηθικλμνξοπρσςτυφχψω", "a b g d e z e th i k l m n x o p r s s t u ph kh ps o".split(), strict=True))
DIGRAPHS = (("ph", "b"), ("th", "t"), ("kh", "k"), ("ch", "k"), ("sh", "s"), ("ps", "bs"), ("x", "ks"))
CONSONANT_CLASSES = str.maketrans({"p": "b", "f": "b", "v": "b", "d": "t", "g": "k", "q": "k", "c": "k", "z": "s"})
DROPPED = re.compile(r"[aeiouywhj]")


class RuleSettings(BaseModel):
    min_count: int = Field(5, ge=1, description="Linked occurrences of a lemma needed before the lexicon rule fires.")
    min_share: float = Field(0.95, gt=0.5, le=1, description="Share of the lemma's occurrences linked to that translation.")
    evidence_confidence: float = Field(EVIDENCE_CONFIDENCE, ge=0, le=1, description="Links count as evidence from this confidence.")
    name_similarity: float = Field(0.9, gt=0, le=1, description="Skeleton similarity for names (short skeletons must be equal).")
    rules: list[str] = Field(["identical", "names", "lexicon"], description="Rules to apply, in order.")


class Proposal(BaseModel):
    sent_id: str
    source: str
    target: str
    rule: str
    confidence: float
    reason: str

    @property
    def link(self) -> Link:
        return Link(source=self.source, target=self.target, sure=True, confidence=self.confidence)


class RuleCount(BaseModel):
    links: int = 0
    correct: int | None = None
    precision: float | None = None


class RulesReport(BaseModel):
    sentences: int = 0
    rules: dict[str, RuleCount] = Field(default_factory=dict)
    reference_links: int | None = Field(None, description="Links in the reference set (for measure).")

    @property
    def total(self) -> int:
        return sum(count.links for count in self.rules.values())


def romanise(text: str) -> str:
    """Lowercase ASCII letters: accents stripped, Greek transliterated, other scripts dropped."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z]", "", "".join(GREEK.get(char, char) for char in plain))


def skeleton(text: str) -> str:
    """The consonants of a romanised word in broad classes, doubles collapsed (``Ἔφεσος`` → ``bs``, ``ʾafasus`` → ``bs``)."""
    for digraph, replacement in DIGRAPHS:
        text = text.replace(digraph, replacement)
    consonants = DROPPED.sub("", text).translate(CONSONANT_CLASSES)
    return re.sub(r"(.)\1+", r"\1", consonants)


def name_keys(word: Token) -> set[str]:
    """Skeletons of a word's transliterations, lemma and form."""
    texts = [word.misc_value(key) or "" for key in TRANSLIT_KEYS] + [word.lemma, word.form]
    return {key for key in (skeleton(romanise(text)) for text in texts) if key}


def similar(keys_a: set[str], keys_b: set[str], threshold: float) -> float:
    """The best similarity of two skeleton sets; skeletons shorter than 3 must be equal."""
    best = 0.0
    for a in keys_a:
        for b in keys_b:
            if min(len(a), len(b)) < 3:
                score = 1.0 if a == b else 0.0
            else:
                score = SequenceMatcher(None, a, b).ratio()
            best = max(best, score if score >= threshold else 0.0)
    return best


def has_letters(form: str) -> bool:
    return any(char.isalpha() for char in form)


class Rules:
    """Applies the rules to a writable alignment set; ``evidence`` names the sets used by the lexicon rule (default all)."""

    def __init__(
        self,
        store: CorpusStore,
        target: str,
        settings: RuleSettings | None = None,
        evidence: Iterable[str] | None = None,
    ):
        self.store = store
        self.target = target
        self.settings = settings or RuleSettings()
        self.alignment = store.alignment(target)
        self.evidence = list(evidence) if evidence is not None else None
        self._table: TranslationTable | None = None

    @property
    def table(self) -> TranslationTable:
        if self._table is None:
            self._table = TranslationTable(self.store, self.evidence, min_confidence=self.settings.evidence_confidence)
        return self._table

    def refresh(self) -> None:
        """Rebuild the evidence on next use (after links were added elsewhere)."""
        self._table = None

    # ------------------------------------------------------------ rules

    @staticmethod
    def _unique(words: list[Token], key) -> dict[str, Token]:
        counts = Counter(key(word) for word in words)
        return {key(word): word for word in words if counts[key(word)] == 1}

    def identical(self, sent_id: str, a: list[Token], b: list[Token]) -> list[Proposal]:
        def symbol(word: Token) -> bool:
            return word.upos in SYMBOL_TAGS or not has_letters(word.form)

        forms_b = self._unique(b, lambda word: word.form)
        once_a = self._unique(a, lambda word: word.form)
        return [
            Proposal(
                sent_id=sent_id, source=word.id, target=forms_b[form].id, rule="identical",
                confidence=IDENTICAL_CONFIDENCE, reason=f"identical {word.upos} '{form}'",
            )
            for form, word in once_a.items()
            if form in forms_b and symbol(word) and symbol(forms_b[form])
        ]  # fmt: skip

    def names(self, sent_id: str, a: list[Token], b: list[Token]) -> list[Proposal]:
        threshold = self.settings.name_similarity
        keys = {id(word): name_keys(word) for word in a + b}
        scores: dict[tuple[str, str], float] = {}
        for wa in a:
            for wb in b:
                if "PROPN" not in (wa.upos, wb.upos) or wa.upos in FUNCTION_TAGS or wb.upos in FUNCTION_TAGS:
                    continue
                score = similar(keys[id(wa)], keys[id(wb)], threshold)
                if score:
                    scores[(wa.id, wb.id)] = score
        proposals = []
        for (ida, idb), score in scores.items():
            rivals = [s for (x, y), s in scores.items() if (x == ida) != (y == idb) and s >= score]
            if not rivals:
                form_a = next(w.form for w in a if w.id == ida)
                form_b = next(w.form for w in b if w.id == idb)
                proposals.append(
                    Proposal(
                        sent_id=sent_id, source=ida, target=idb, rule="names", confidence=RULE_CONFIDENCE,
                        reason=f"name '{form_a}' ~ '{form_b}' (similarity {score:.2f})",
                    )
                )  # fmt: skip
        return proposals

    def _dominant(self, source: str, lemma: str, sent_id: str) -> tuple[str, int, int] | None:
        entry = self.table.entry(source, lemma)
        if entry is None:
            return None
        candidates = entry.candidates(sent_id)
        occurrences = entry.occurrences_without(sent_id)
        if not candidates or not occurrences:
            return None
        value, count = candidates.most_common(1)[0]
        if count >= self.settings.min_count and count / occurrences >= self.settings.min_share:
            return value, count, occurrences
        return None

    def lexicon(self, sent_id: str, a: list[Token], b: list[Token], all_a: list[Token], all_b: list[Token]) -> list[Proposal]:
        """Lemmas with an overwhelming translation that occurs exactly once in the other sentence."""
        proposals: dict[tuple[str, str], Proposal] = {}
        sides = (
            (self.alignment.source_a.name, a, all_a, all_b, {w.id for w in b}, False),
            (self.alignment.source_b.name, b, all_b, all_a, {w.id for w in a}, True),
        )
        for source, free, here, there, free_there, reverse in sides:
            here_counts = Counter(lemma_of(word) for word in here)
            for word in free:
                lemma = lemma_of(word)
                if here_counts[lemma] != 1:
                    continue
                found = self._dominant(source, lemma, sent_id)
                if found is None:
                    continue
                value, count, occurrences = found
                matches = [other for other in there if lemma_of(other) == value]
                if len(matches) != 1 or matches[0].id not in free_there:
                    continue
                ida, idb = (matches[0].id, word.id) if reverse else (word.id, matches[0].id)
                proposals.setdefault(
                    (ida, idb),
                    Proposal(
                        sent_id=sent_id, source=ida, target=idb, rule="lexicon", confidence=RULE_CONFIDENCE,
                        reason=f"'{lemma}' is linked to '{value}' in {count} of {occurrences} occurrences",
                    ),
                )  # fmt: skip
        return list(proposals.values())

    # ------------------------------------------------------------ driver

    def propose(self, sent_id: str, links: list[Link] | None = None) -> list[Proposal]:
        """Links the rules would add to a sentence pair that already has ``links`` (default: its current links)."""
        a_sentence: Sentence = self.alignment.source_a.sentence(sent_id)
        b_sentence: Sentence = self.alignment.source_b.sentence(sent_id)
        links = self.alignment.links(sent_id) if links is None else links
        linked_a = {link.source for link in links}
        linked_b = {link.target for link in links}
        proposals: list[Proposal] = []
        for rule in self.settings.rules:
            a = [w for w in a_sentence.words if w.id not in linked_a]
            b = [w for w in b_sentence.words if w.id not in linked_b]
            if rule == "lexicon":
                found = self.lexicon(sent_id, a, b, a_sentence.words, b_sentence.words)
            else:
                found = getattr(self, rule)(sent_id, a, b)
            proposals += found
            linked_a |= {p.source for p in found}
            linked_b |= {p.target for p in found}
        return proposals

    def apply(self, sent_ids: Iterable[str] | None = None) -> RulesReport:
        """Add the rules' links to the target set (default: every sentence of source A that is in source B)."""
        if sent_ids is None:
            ids_b = {s.sent_id for s in self.alignment.source_b.sentences}
            sent_ids = [s.sent_id for s in self.alignment.source_a.sentences if s.sent_id in ids_b]
        report = RulesReport()
        for sent_id in sent_ids:
            report.sentences += 1
            proposals = self.propose(sent_id)
            for proposal in proposals:
                report.rules.setdefault(proposal.rule, RuleCount()).links += 1
            if proposals:
                reasons = "; ".join(p.reason for p in proposals)
                self.store.set_links(
                    self.target, sent_id, [p.link for p in proposals], replace=False, reason=reasons, agent=RULE_AGENT
                )
        return report


def measure(rules: Rules, reference: str, sent_ids: Iterable[str] | None = None) -> tuple[RulesReport, list[tuple[Proposal, bool]]]:
    """Propose links for the pairs of ``reference`` from scratch; count those in ``reference`` (S or P) as correct."""
    gold = rules.store.alignment(reference)
    report = RulesReport(reference_links=0)
    outcomes = []
    for sent_id in sent_ids if sent_ids is not None else list(gold.pairs):
        report.sentences += 1
        keys = {link.key for link in gold.links(sent_id)}
        report.reference_links += len(keys)
        for proposal in rules.propose(sent_id, links=[]):
            correct = proposal.link.key in keys
            count = report.rules.setdefault(proposal.rule, RuleCount(correct=0))
            count.links += 1
            count.correct += correct
            outcomes.append((proposal, correct))
    for count in report.rules.values():
        count.precision = round(count.correct / count.links, 4)
    return report, outcomes
