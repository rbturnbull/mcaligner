"""Alignment exploration over a :class:`~mcparser.corpus.CorpusStore`.

Plain functions returning small dicts, so they can be tested without a server
and registered as MCP tools by :mod:`mcaligner.mcp.server`. They complement
MCParser's ``get_parallel`` and ``translation_candidates``: similar pairs,
every link of a lemma, how two lemmas were linked, and statistics.

Sides are ``"a"`` and ``"b"`` as in MCParser: the first and second source of the
alignment set. A word's lemma falls back to its form when the lemma is empty.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterator, Literal

from mcparser.corpus import CorpusStore, NotFoundError, Sentence, Token
from mcparser.corpus.alignment import AlignmentSet, Link

from ..lexicon import lemma_of

Side = Literal["a", "b"]


def _pairs(aset: AlignmentSet, exclude: str | None = None) -> Iterator[tuple[str, Sentence, Sentence, list[Link]]]:
    """Pairs with links whose sentences still exist, without the pair ``exclude``."""
    for sent_id, links in aset.pairs.items():
        if not links or sent_id == exclude:
            continue
        try:
            yield sent_id, aset.source_a.sentence(sent_id), aset.source_b.sentence(sent_id), links
        except NotFoundError:
            continue


def _split(exclude_sentence: str | None) -> str | None:
    """``"alignment:sent_id"`` or ``"sent_id"`` → ``sent_id``."""
    return exclude_sentence.rsplit(":", 1)[-1] if exclude_sentence else None


def similar_pairs(
    store: CorpusStore, alignment: str, sent_id: str, limit: int = 5, min_confidence: float = 0.0
) -> dict[str, Any]:
    """Linked pairs whose lemmas overlap most with pair ``sent_id`` (which is never returned).

    Score = shared lemmas (both sides) / lemmas of the pair. Each hit lists the
    shared lemmas and its links as ``lemmaA~lemmaB``, as evidence for how the
    shared lemmas were aligned elsewhere.
    """
    aset = store.alignment(alignment)
    a, b = aset.source_a.sentence(sent_id), aset.source_b.sentence(sent_id)
    mine_a, mine_b = {lemma_of(w) for w in a.words}, {lemma_of(w) for w in b.words}
    hits = []
    for other_id, other_a, other_b, links in _pairs(aset, exclude=sent_id):
        words_a, words_b = {w.id: lemma_of(w) for w in other_a.words}, {w.id: lemma_of(w) for w in other_b.words}
        shared_a, shared_b = mine_a & set(words_a.values()), mine_b & set(words_b.values())
        if not shared_a and not shared_b:
            continue
        kept = [link for link in links if aset.confidence(link) >= min_confidence]
        hits.append(
            {
                "sent_id": other_id,
                "score": round((len(shared_a) + len(shared_b)) / (len(mine_a) + len(mine_b)), 3),
                "shared_a": sorted(shared_a),
                "shared_b": sorted(shared_b),
                "text_a": other_a.text,
                "text_b": other_b.text,
                "links": " ".join(f"{words_a.get(l.source, '?')}~{words_b.get(l.target, '?')}" for l in kept),
            }
        )
    hits.sort(key=lambda hit: (-hit["score"], hit["sent_id"]))
    return {"alignment": alignment, "sent_id": sent_id, "pairs": hits[:limit]}


def lemma_links(
    store: CorpusStore,
    alignment: str,
    lemma: str,
    side: Side = "a",
    limit: int = 20,
    min_confidence: float = 0.0,
    exclude_sentence: str | None = None,
) -> dict[str, Any]:
    """Every occurrence of ``lemma`` in the linked pairs: its form, what it is linked to, and the context.

    Also the counts of linked lemmas and the pairs where the lemma has no link.
    """
    aset = store.alignment(alignment)
    exclude = _split(exclude_sentence)
    occurrences, partners, unlinked = [], Counter(), []
    for sent_id, a, b, links in _pairs(aset, exclude):
        here, there = (a, b) if side == "a" else (b, a)
        other = {w.id: w for w in there.words}
        linked: dict[str, list[tuple[str, float]]] = {}
        for link in links:
            confidence = aset.confidence(link)
            if confidence >= min_confidence:
                mine, theirs = (link.source, link.target) if side == "a" else (link.target, link.source)
                linked.setdefault(mine, []).append((theirs, confidence))
        for word in here.words:
            if lemma_of(word) != lemma:
                continue
            found = [(other[i], c) for i, c in linked.get(word.id, []) if i in other]
            for partner, _ in found:
                partners[lemma_of(partner)] += 1
            if not found:
                unlinked.append(sent_id)
            occurrences.append(
                {
                    "sent_id": sent_id,
                    "word": f"{word.id} {word.form}",
                    "linked_to": [f"{p.id} {p.form} ({lemma_of(p)}) {c:.2f}" for p, c in found],
                    "text": here.text,
                }
            )
    return {
        "lemma": lemma,
        "side": side,
        "occurrences": len(occurrences),
        "linked_lemmas": [{"lemma": k, "count": v} for k, v in partners.most_common()],
        "unlinked_in": unlinked,
        "examples": occurrences[:limit],
    }


def link_examples(
    store: CorpusStore,
    alignment: str,
    lemma_a: str,
    lemma_b: str,
    limit: int = 10,
    min_confidence: float = 0.0,
    exclude_sentence: str | None = None,
) -> dict[str, Any]:
    """Pairs where ``lemma_a`` (source A) is linked to ``lemma_b`` (source B), and where both occur unlinked to each other."""
    aset = store.alignment(alignment)
    exclude = _split(exclude_sentence)
    linked, apart = [], []
    for sent_id, a, b, links in _pairs(aset, exclude):
        ids_a = {w.id: w for w in a.words if lemma_of(w) == lemma_a}
        ids_b = {w.id: w for w in b.words if lemma_of(w) == lemma_b}
        if not ids_a or not ids_b:
            continue
        found = [
            f"{ids_a[l.source].form}~{ids_b[l.target].form} {aset.confidence(l):.2f}"
            for l in links
            if l.source in ids_a and l.target in ids_b and aset.confidence(l) >= min_confidence
        ]
        entry = {"sent_id": sent_id, "text_a": a.text, "text_b": b.text}
        if found:
            linked.append({**entry, "links": found})
        else:
            apart.append(entry)
    return {
        "lemma_a": lemma_a,
        "lemma_b": lemma_b,
        "linked_in": len(linked),
        "cooccur_unlinked_in": len(apart),
        "linked": linked[:limit],
        "cooccur_unlinked": apart[:limit],
    }


def _crossings(links: list[Link]) -> int:
    """Pairs of links that cross (their order differs on the two sides)."""
    edges = sorted({(int(l.source), int(l.target)) for l in links if l.source.isdigit() and l.target.isdigit()})
    return sum(1 for i, (a1, b1) in enumerate(edges) for a2, b2 in edges[i + 1 :] if a1 < a2 and b1 > b2)


def word_row(word: Token, linked: list[str]) -> dict[str, Any]:
    return {
        "id": word.id,
        "form": word.form,
        "lemma": word.lemma,
        "upos": word.upos,
        "xpos": word.xpos,
        "feats": word.feats,
        "head": word.head,
        "deprel": word.deprel,
        "linked": linked,
    }


def pair_words(store: CorpusStore, alignment: str, sent_id: str, side: Side | None = None) -> dict[str, Any]:
    """Every column of the words of a pair (lemma, UPOS, XPOS, FEATS, head, deprel) with the ids they are linked to.

    ``side`` limits it to source A or B (default both).
    """
    aset = store.alignment(alignment)
    links = aset.links(sent_id)
    result: dict[str, Any] = {"alignment": alignment, "sent_id": sent_id}
    for name, source, mine in (("a", aset.source_a, "source"), ("b", aset.source_b, "target")):
        if side in (None, name):
            theirs = "target" if mine == "source" else "source"
            result[name] = {
                "source": source.name,
                "words": [
                    word_row(word, [getattr(l, theirs) for l in links if getattr(l, mine) == word.id])
                    for word in source.sentence(sent_id).words
                ],
            }
    return result


def feats_match(word: Token, wanted: dict[str, str]) -> bool:
    have = word.feats_dict
    return all(key in have and value in (have[key] or "").split(",") for key, value in wanted.items())


def category_links(
    store: CorpusStore,
    alignment: str,
    side: Side = "a",
    upos: str | None = None,
    xpos: str | None = None,
    feats: str | None = None,
    deprel: str | None = None,
    limit: int = 10,
    min_confidence: float = 0.0,
    exclude_sentence: str | None = None,
) -> dict[str, Any]:
    """How words of a category are linked: their partners' UPOS, XPOS and lemmas, and how often they have none.

    A word is in the category if it has the given ``upos``, ``xpos`` and ``deprel`` and all the ``feats``
    (``"Case=Gen|Number=Sing"``; a value matches if it is one of a comma-separated list). At least one filter is needed.
    """
    wanted = {key: value for key, _, value in (item.partition("=") for item in (feats or "").split("|") if item)}
    if not (upos or xpos or deprel or wanted):
        raise NotFoundError("Give at least one of upos, xpos, deprel or feats.")
    aset = store.alignment(alignment)
    exclude = _split(exclude_sentence)
    counts = {"upos": Counter(), "xpos": Counter(), "lemma": Counter()}
    occurrences, unlinked, examples = 0, 0, []
    for sent_id, a, b, links in _pairs(aset, exclude):
        here, there = (a, b) if side == "a" else (b, a)
        other = {w.id: w for w in there.words}
        linked: dict[str, list[str]] = {}
        for link in links:
            if aset.confidence(link) >= min_confidence:
                mine, theirs = (link.source, link.target) if side == "a" else (link.target, link.source)
                linked.setdefault(mine, []).append(theirs)
        for word in here.words:
            if (upos and word.upos != upos) or (xpos and word.xpos != xpos) or (deprel and word.deprel != deprel):
                continue
            if not feats_match(word, wanted):
                continue
            occurrences += 1
            partners = [other[i] for i in linked.get(word.id, []) if i in other]
            unlinked += not partners
            for partner in partners:
                counts["upos"][partner.upos] += 1
                counts["xpos"][partner.xpos] += 1
                counts["lemma"][lemma_of(partner)] += 1
            if len(examples) < 5:
                examples.append(f"{sent_id} {word.form} -> " + (", ".join(p.form for p in partners) or "nothing"))
    return {
        "side": side,
        "filter": {"upos": upos, "xpos": xpos, "feats": feats, "deprel": deprel},
        "occurrences": occurrences,
        "unlinked": unlinked,
        **{f"partner_{key}": [{"value": v, "count": n} for v, n in counter.most_common(limit)] for key, counter in counts.items()},
        "examples": examples,
    }


def alignment_stats(
    store: CorpusStore, alignment: str, sent_id: str | None = None, threshold: float = 0.8
) -> dict[str, Any]:
    """Link counts for one pair, or for the whole set when ``sent_id`` is omitted.

    Sure/probable links, words without links on each side, how many words take
    part in one-to-many links, crossing links, mean confidence, links below
    ``threshold`` and links per agent.
    """
    aset = store.alignment(alignment)
    if sent_id is not None:
        pairs = [(sent_id, aset.source_a.sentence(sent_id), aset.source_b.sentence(sent_id), aset.links(sent_id))]
    else:
        pairs = list(_pairs(aset))
    stats = Counter()
    agents: Counter[str] = Counter()
    confidences = []
    for _, a, b, links in pairs:
        out_a, out_b = Counter(l.source for l in links), Counter(l.target for l in links)
        stats["pairs"] += 1
        stats["words_a"] += len(a.words)
        stats["words_b"] += len(b.words)
        stats["links"] += len(links)
        stats["sure"] += sum(l.sure for l in links)
        stats["unlinked_a"] += sum(1 for w in a.words if w.id not in out_a)
        stats["unlinked_b"] += sum(1 for w in b.words if w.id not in out_b)
        stats["a_words_with_many"] += sum(1 for n in out_a.values() if n > 1)
        stats["b_words_with_many"] += sum(1 for n in out_b.values() if n > 1)
        stats["crossings"] += _crossings(links)
        for link in links:
            confidences.append(aset.confidence(link))
            agents[link.agent or "unknown"] += 1
    result: dict[str, Any] = dict(stats)
    result["probable"] = stats["links"] - stats["sure"]
    result["mean_confidence"] = round(sum(confidences) / len(confidences), 3) if confidences else None
    result["below_threshold"] = sum(1 for c in confidences if c < threshold)
    result["threshold"] = threshold
    result["agents"] = dict(agents)
    result["alignment"] = alignment
    if sent_id is not None:
        result["sent_id"] = sent_id
    return result
