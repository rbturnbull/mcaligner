from __future__ import annotations

import pytest
from llmparser.corpus import CorpusError
from llmparser.corpus.alignment import parse_ugarit

from llmaligner.evaluate import count, evaluate, format_report, read_links


def test_counts_and_aer():
    predicted = parse_ugarit("1-1S 2-2S 3-3P 4-5S")
    gold = parse_ugarit("1-1S 2-2P 3-3S 6-6S")
    c = count(predicted, gold)
    assert (c.predicted, c.predicted_sure, c.gold_sure, c.gold_all) == (4, 3, 3, 4)
    assert (c.sure_correct, c.all_correct, c.a_and_s) == (1, 3, 2)
    report = evaluate({"v": predicted}, {"v": gold})
    total = report.total
    assert total.sure.precision == pytest.approx(1 / 3, abs=1e-4)
    assert total.all.recall == 0.75 and total.all.precision == 0.75
    assert total.aer == pytest.approx(1 - (2 + 3) / (4 + 3), abs=1e-4)


def test_evaluate_coverage_rules():
    gold = {"v1": parse_ugarit("1-1"), "v2": parse_ugarit("1-1 2-2")}
    predicted = {"v1": parse_ugarit("1-1"), "extra": parse_ugarit("1-1")}
    report = evaluate(predicted, gold)
    assert [p.sent_id for p in report.pairs] == ["v1", "v2"]  # pairs outside gold are ignored
    assert report.total.all.recall == pytest.approx(1 / 3, abs=1e-4)
    only = evaluate(predicted, gold, annotated_only=True)
    assert only.sentences == 1 and only.total.aer == 0.0


def test_empty_scores():
    report = evaluate({}, {"v": parse_ugarit("1-1P")})
    assert report.total.all.f1 == 0.0 and report.total.sure.precision == 0.0
    assert report.total.aer == 0.0  # no predictions and no sure links: nothing to get wrong


def test_read_links(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text(
        '{"sent_id": "v1", "links": [{"source": "1", "target": "1", "confidence": 0.4}, {"source": "2", "target": "2"}]}\n\n'
        '{"sent_id": 7, "links": []}\n',
        encoding="utf-8",
    )
    links = read_links(path, min_confidence=0.5)
    assert [link.key for link in links["v1"]] == ["2-2"] and links["7"] == []
    path.write_text('{"links": []}\n', encoding="utf-8")
    with pytest.raises(CorpusError, match="line 1"):
        read_links(path)


def test_format_report():
    report = evaluate({"v": parse_ugarit("1-1")}, {"v": parse_ugarit("1-1")})
    assert "1 sentence pairs" in format_report(report)
    table = format_report(report, per_sentence=True)
    assert table.splitlines()[2].startswith("v ") and "total" in table
