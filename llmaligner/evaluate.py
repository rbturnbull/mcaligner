"""Score predicted word links against gold links.

With A the predicted links, S the gold sure links and P the gold sure and
probable links (S ⊆ P), the report gives:

* precision, recall and F1 over **sure** links (predicted S links against S);
* precision, recall and F1 over **all** links (A against P, ignoring S/P);
* the alignment error rate (Och & Ney 2003),
  ``AER = 1 − (|A∩S| + |A∩P|) / (|A| + |S|)``.

Links are compared by their word ids (``3-5``). Scores are given per sentence
pair and over all pairs (micro-averaged: counts are summed first).
"""

from __future__ import annotations

import json
from pathlib import Path

from llmparser.corpus import CorpusError
from llmparser.corpus.alignment import Link
from pydantic import BaseModel, Field


class Counts(BaseModel):
    """Link counts for one sentence pair (or summed over several)."""

    predicted: int = 0
    predicted_sure: int = 0
    gold_sure: int = 0
    gold_all: int = 0
    sure_correct: int = Field(0, description="Predicted sure links that are gold sure links.")
    all_correct: int = Field(0, description="|A∩P|: predicted links that are gold links.")
    a_and_s: int = Field(0, description="|A∩S|: predicted links that are gold sure links.")

    def add(self, other: Counts) -> None:
        for name in type(self).model_fields:
            setattr(self, name, getattr(self, name) + getattr(other, name))


class Scores(BaseModel):
    precision: float
    recall: float
    f1: float


class PairScore(BaseModel):
    sent_id: str
    counts: Counts
    sure: Scores
    all: Scores
    aer: float


class EvaluationReport(BaseModel):
    sentences: int
    total: PairScore
    pairs: list[PairScore]


def read_links(path: Path | str, min_confidence: float = 0.0) -> dict[str, list[Link]]:
    """An alignment JSONL file as links per ``sent_id``; links without a confidence are kept."""
    pairs: dict[str, list[Link]] = {}
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            links = [Link.model_validate(link) for link in data.get("links", [])]
            pairs[str(data["sent_id"])] = links
        except (ValueError, KeyError, TypeError) as error:
            raise CorpusError(f"{path}, line {number}: {error}") from None
    return {
        sent_id: [link for link in links if link.confidence is None or link.confidence >= min_confidence]
        for sent_id, links in pairs.items()
    }


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _scores(correct: int, predicted: int, gold: int) -> Scores:
    precision, recall = _ratio(correct, predicted), _ratio(correct, gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return Scores(precision=round(precision, 4), recall=round(recall, 4), f1=round(f1, 4))


def count(predicted: list[Link], gold: list[Link]) -> Counts:
    a = {link.key for link in predicted}
    a_sure = {link.key for link in predicted if link.sure}
    s = {link.key for link in gold if link.sure}
    p = {link.key for link in gold}
    return Counts(
        predicted=len(a),
        predicted_sure=len(a_sure),
        gold_sure=len(s),
        gold_all=len(p),
        sure_correct=len(a_sure & s),
        all_correct=len(a & p),
        a_and_s=len(a & s),
    )


def score(sent_id: str, counts: Counts) -> PairScore:
    denominator = counts.predicted + counts.gold_sure
    aer = 1 - (counts.a_and_s + counts.all_correct) / denominator if denominator else 0.0
    return PairScore(
        sent_id=sent_id,
        counts=counts,
        sure=_scores(counts.sure_correct, counts.predicted_sure, counts.gold_sure),
        all=_scores(counts.all_correct, counts.predicted, counts.gold_all),
        aer=round(aer, 4),
    )


def evaluate(
    predicted: dict[str, list[Link]], gold: dict[str, list[Link]], annotated_only: bool = False
) -> EvaluationReport:
    """Score every gold pair (a pair missing from the predictions has no links).

    Pairs that are not in the gold file are ignored: gold alignments often
    cover only part of a text. With ``annotated_only`` only pairs with at least
    one predicted link count, which measures a partial run on what it has done.
    """
    sent_ids = [sent_id for sent_id in gold if not annotated_only or predicted.get(sent_id)]
    total = Counts()
    pairs = []
    for sent_id in sent_ids:
        counts = count(predicted.get(sent_id, []), gold.get(sent_id, []))
        total.add(counts)
        pairs.append(score(sent_id, counts))
    return EvaluationReport(sentences=len(pairs), total=score("total", total), pairs=pairs)


def format_report(report: EvaluationReport, per_sentence: bool = False) -> str:
    """A plain-text table: P/R/F1 over sure and all links, and AER."""
    header = f"{'pair':<14} {'A':>5} {'S':>5} {'P':>5}  {'sure P/R/F1':<20} {'all P/R/F1':<20} {'AER':>6}"
    rows = [*report.pairs, report.total] if per_sentence else [report.total]
    lines = [header, "-" * len(header)]
    for row in rows:
        c = row.counts
        sure = f"{row.sure.precision:.3f}/{row.sure.recall:.3f}/{row.sure.f1:.3f}"
        every = f"{row.all.precision:.3f}/{row.all.recall:.3f}/{row.all.f1:.3f}"
        lines.append(f"{row.sent_id:<14} {c.predicted:>5} {c.gold_sure:>5} {c.gold_all:>5}  {sure:<20} {every:<20} {row.aer:>6.3f}")
    lines.append(f"{report.sentences} sentence pairs")
    return "\n".join(lines)
