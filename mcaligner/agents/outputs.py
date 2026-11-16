"""Compact answers from the agents, checked and applied in code.

The aligner answers with one line per link, the scorer with one line per
rating::

    <id> 3-5 S 0.95              aligner: SENT_ID A-B S|P CONFIDENCE
    <id> 3-5 0.9                 scorer:  SENT_ID A-B CONFIDENCE

Nothing is written until the whole answer is valid: unknown pairs, malformed
lines and links to words that do not exist (checked with
``set_links(..., dry_run=True)``) go back to the model as a retry with the
list of problems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from mcparser.corpus import CorpusError, CorpusStore
from mcparser.corpus.alignment import Link
from pydantic import BaseModel, Field
from pydantic_ai import ModelRetry

from ..rules import is_punctuation

ALIGNER_AGENT = "aligner"
SCORER_AGENT = "scorer"

LINK_LINE = re.compile(r"^(\S+)\s+(\d+)-(\d+)\s*([SP])?\s+(\S+)$")
SCORE_LINE = re.compile(r"^(\S+)\s+(\d+)-(\d+)[SP]?\s+(\S+)$")
REMOVE_LINE = re.compile(r"^(\S+)\s+(\d+)-(\d+)[SP]?$")


class Alignment(BaseModel):
    """Your answer: the links of the sentence pairs."""

    links: str = Field(
        description=(
            'One line per link, "SENT_ID A-B S|P CONFIDENCE", e.g. "<id> 3-5 S 0.95", with <id> the pair id exactly as in its "## Pair" heading. '
            "Settled links are kept without listing them."
        )
    )
    remove: str = Field("", description='Settled links that are wrong, one per line: "SENT_ID A-B".')
    summary: str = Field("", description="At most 15 words.")


class Scores(BaseModel):
    """Your answer: a confidence for each link to score."""

    scores: str = Field(description='One line per link, "SENT_ID A-B CONFIDENCE", e.g. "<id> 3-5 0.9", with <id> the pair id exactly as in its "## Pair" heading.')
    summary: str = Field("", description="At most 15 words.")


@dataclass
class TaskBatch:
    """The pairs of one task; passed to the agent run as its dependencies."""

    target: str
    sent_ids: list[str]
    settled: dict[str, list[Link]] = field(default_factory=dict)
    """Aligner: the links shown as settled, per pair (they are kept)."""
    review: dict[str, list[Link]] = field(default_factory=dict)
    """Scorer: the links to score, per pair."""
    dropped: int = 0
    """Aligner: links to punctuation that code removed from the answer."""


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def _confidence(text: str) -> float | None:
    try:
        return min(max(float(text), 0.0), 1.0)
    except ValueError:
        return None


def parse_links(text: str, batch: TaskBatch) -> tuple[dict[str, list[Link]], list[str]]:
    """``SENT_ID A-B S|P CONFIDENCE`` lines as links per pair, plus error messages."""
    links: dict[str, list[Link]] = {}
    errors = []
    for number, line in enumerate(_lines(text), start=1):
        match = LINK_LINE.match(line)
        if match is None:
            errors.append(f"links line {number}: expected SENT_ID A-B S|P CONFIDENCE, got {line!r}")
            continue
        sent_id, source, target, kind, confidence = match.groups()
        score = _confidence(confidence)
        if sent_id not in batch.sent_ids:
            errors.append(f"links line {number}: pair {sent_id!r} is not in this task")
        elif score is None:
            errors.append(f"links line {number}: confidence {confidence!r} is not a number")
        else:
            links.setdefault(sent_id, []).append(Link(source=source, target=target, sure=kind != "P", confidence=score))
    return links, errors


def parse_removals(text: str, batch: TaskBatch) -> tuple[dict[str, set[str]], list[str]]:
    removals: dict[str, set[str]] = {}
    errors = []
    for number, line in enumerate(_lines(text), start=1):
        match = REMOVE_LINE.match(line)
        if match is None or match.group(1) not in batch.sent_ids:
            errors.append(f"remove line {number}: expected SENT_ID A-B for a pair of this task, got {line!r}")
            continue
        sent_id, source, target = match.groups()
        removals.setdefault(sent_id, set()).add(f"{source}-{target}")
    return removals, errors


def parse_scores(text: str, batch: TaskBatch) -> tuple[dict[str, dict[str, float]], list[str]]:
    """``SENT_ID A-B CONFIDENCE`` lines as {link key: confidence} per pair, plus error messages."""
    scores: dict[str, dict[str, float]] = {}
    errors = []
    for number, line in enumerate(_lines(text), start=1):
        match = SCORE_LINE.match(line)
        if match is None:
            errors.append(f"scores line {number}: expected SENT_ID A-B CONFIDENCE, got {line!r}")
            continue
        sent_id, source, target, confidence = match.groups()
        key, score = f"{source}-{target}", _confidence(confidence)
        if sent_id not in batch.sent_ids:
            errors.append(f"scores line {number}: pair {sent_id!r} is not in this task")
        elif score is None:
            errors.append(f"scores line {number}: confidence {confidence!r} is not a number")
        elif key not in {link.key for link in batch.review.get(sent_id, [])}:
            errors.append(f"scores line {number}: {sent_id} {key} is not one of the links to score")
        else:
            scores.setdefault(sent_id, {})[key] = score
    return scores, errors


class Applier:
    """Checks an agent's answer against the store, then applies it."""

    def __init__(self, store: CorpusStore, link_punctuation: bool = False):
        self.store = store
        self.link_punctuation = link_punctuation

    def without_punctuation(self, batch: TaskBatch, links: dict[str, list[Link]]) -> dict[str, list[Link]]:
        """The answer's links without those that touch punctuation (counted in ``batch.dropped``)."""
        aset = self.store.alignment(batch.target)
        kept, batch.dropped = {}, 0  # reset: a retried answer is filtered again
        for sent_id, group in links.items():
            skip_a = {w.id for w in aset.source_a.sentence(sent_id).words if is_punctuation(w)}
            skip_b = {w.id for w in aset.source_b.sentence(sent_id).words if is_punctuation(w)}
            kept[sent_id] = [link for link in group if link.source not in skip_a and link.target not in skip_b]
            batch.dropped += len(group) - len(kept[sent_id])
        return kept

    @staticmethod
    def _retry(errors: list[str]) -> None:
        if errors:
            raise ModelRetry("Fix these problems and answer again:\n" + "\n".join(f"- {e}" for e in errors[:20]))

    def merged(self, batch: TaskBatch, sent_id: str, links: list[Link], removals: set[str]) -> list[Link]:
        """Settled links (minus removals) plus the answer's links (which win on the same word pair)."""
        result = {link.key: link for link in batch.settled.get(sent_id, []) if link.key not in removals}
        result.update({link.key: link for link in links})
        return list(result.values())

    def alignment(self, answer: Alignment, batch: TaskBatch) -> Alignment:
        links, errors = parse_links(answer.links, batch)
        if not self.link_punctuation and not errors:
            links = self.without_punctuation(batch, links)
        removals, removal_errors = parse_removals(answer.remove, batch)
        errors += removal_errors
        new = {sent_id: self.merged(batch, sent_id, links.get(sent_id, []), removals.get(sent_id, set())) for sent_id in batch.sent_ids}
        for sent_id, merged in new.items():
            try:
                self.store.set_links(batch.target, sent_id, merged, agent=ALIGNER_AGENT, dry_run=True)
            except CorpusError as error:
                errors.append(f"pair {sent_id}: {error}")
        self._retry(errors)
        for sent_id, merged in new.items():  # every pair is written, so the history shows the aligner saw it
            self.store.set_links(batch.target, sent_id, merged, reason=answer.summary, agent=ALIGNER_AGENT)
        return answer

    def scores(self, answer: Scores, batch: TaskBatch) -> Scores:
        scores, errors = parse_scores(answer.scores, batch)
        self._retry(errors)
        for sent_id, keyed in scores.items():
            rated = [
                link.model_copy(update={"confidence": keyed[link.key]}) for link in batch.review[sent_id] if link.key in keyed
            ]
            self.store.set_links(batch.target, sent_id, rated, replace=False, reason=answer.summary, agent=SCORER_AGENT)
        return answer
