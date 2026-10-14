from __future__ import annotations

import json

import pytest
import yaml
from conftest import ARABIC, GREEK, SAMPLE
from llmparser.corpus import CorpusError, parse_conllu

from llmaligner.convert import build_sentence, convert, corpus_names


def test_convert_sample(converted):
    assert (converted.corpus_a, converted.corpus_b) == (ARABIC, GREEK)
    assert converted.sentences_a == converted.sentences_b == converted.pairs == 3
    assert converted.dropped_links == [] and converted.repaired_lines == 0
    arabic = parse_conllu(converted.conllu_a.read_text(encoding="utf-8"))
    assert [s.sent_id for s in arabic] == ["B10K1V1", "B10K1V2", "B10K1V3"]
    assert arabic[0].meta("verse") == "Ephesians 1:1"
    assert arabic[0].meta("text").startswith("بولس رسول")
    records = [json.loads(line) for line in converted.alignment.read_text(encoding="utf-8").splitlines()]
    assert records[0]["links"][0] == {"source": "1", "target": "1", "sure": True}
    assert sum(len(r["links"]) for r in records) == converted.links
    assert converted.alignment.name == "silver.jsonl"


def test_convert_repairs_and_drops(tmp_path):
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    first = data["B10K1V1"]
    # a multiword line with a missing MISC column, a link to a missing word, a duplicate link
    first[ARABIC]["conllu"] = first[ARABIC]["conllu"].replace("5-6\tبشيه\t_\t_\t_\t_\t_\t_\t_\t_", "5-6\tبشيه\t_\t_\t_\t_\t_\t_\t_")
    first["alignment"] = "1-1S 1-1P 99-1S 2-2P"
    data["B10K1V2"]["alignment"] = "99-99"  # nothing valid left: no record
    del data["B10K1V3"][GREEK]  # one side only: sentence written, no pair
    data["B10K1V3"][ARABIC]["note"] = None
    path = tmp_path / "in.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    report = convert(path, tmp_path / "out")
    assert report.repaired_lines == 1
    assert report.dropped_links == ["B10K1V1 99-1S", "B10K1V2 99-99S"]
    assert (report.sentences_a, report.sentences_b, report.pairs, report.links) == (3, 2, 1, 2)
    assert report.alignment.name == "in.jsonl"
    (record,) = [json.loads(line) for line in report.alignment.read_text(encoding="utf-8").splitlines()]
    assert record["links"] == [{"source": "1", "target": "1", "sure": True}, {"source": "2", "target": "2", "sure": False}]


def test_corpus_names_need_two_corpora():
    assert corpus_names({"x": {"alignment": "1-1"}, "y": {"a": {}, "b": {}, "align": ""}}) == ("a", "b")
    with pytest.raises(CorpusError, match="two corpora"):
        corpus_names({"x": {"a": {}, "alignment": "1-1"}})


def test_build_sentence_errors():
    line = "1\tx\tx\tX\t_\t_\t0\troot\t_\t_"
    with pytest.raises(CorpusError, match="Verse V1: expected exactly one sentence"):
        build_sentence("V1", {"conllu": f"{line}\n\n{line}"})
    with pytest.raises(CorpusError, match="Verse V1: expected exactly one sentence"):
        build_sentence("V1", {})
    with pytest.raises(CorpusError, match="Verse V1: line 2: comment after token lines"):
        build_sentence("V1", {"conllu": f"{line}\n# late"})
    sentence, repaired = build_sentence("V1", {"conllu": f"# sent_id = old\n{line}", "text": ""})
    assert sentence.sent_id == "V1" and sentence.meta("text") is None and repaired == 0
