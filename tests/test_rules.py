from __future__ import annotations

from conftest import parallel_store

from llmaligner.rules import RULE_CONFIDENCE, Proposal, Rules, RuleSettings, measure, romanise, similar, skeleton

EVIDENCE_A = {f"e{i}": "kai/kai/CCONJ logos/logos/NOUN" for i in range(5)}
EVIDENCE_B = {f"e{i}": "wa/wa/CCONJ kalima/kalima/NOUN" for i in range(5)}
EVIDENCE_LINKS = {f"e{i}": "2-2" for i in range(5)}  # kai is never linked


def store_with(tmp_path, a: dict[str, str], b: dict[str, str], links: dict[str, str] | None = None):
    return parallel_store(tmp_path, {**EVIDENCE_A, **a}, {**EVIDENCE_B, **b}, {**EVIDENCE_LINKS, **(links or {})})


def test_romanise_and_skeleton():
    assert romanise("Ἔφεσος") == "ephesos" and romanise("ʾafasus") == "afasus" and romanise("بولس") == ""
    assert skeleton("ephesos") == skeleton("afasus") == "bs"
    assert skeleton(romanise("Παῦλος")) == skeleton(romanise("būlus")) == "bls"
    assert skeleton(romanise("Ἰησοῦς")) == skeleton(romanise("yswʿ")) == "s"
    assert similar({"krst"}, {"krst", "s"}, 0.9) == 1.0
    assert similar({"krst"}, {"kst"}, 0.9) == 0.0  # 0.86: below the threshold
    assert similar({"s"}, {"st"}, 0.1) == 0.0  # short skeletons must be equal


def test_identical(tmp_path):
    store = store_with(
        tmp_path,
        {"s": "logos/logos/NOUN ././PUNCT 3/3/NUM ,/,/PUNCT ,/,/PUNCT x/x/X"},
        {"s": "kalima/kalima/NOUN 3/3/NUM ././PUNCT ,/,/PUNCT x/x/X"},
    )
    rules = Rules(store, "pred", RuleSettings(rules=["identical"]))
    found = {(p.source, p.target) for p in rules.propose("s")}
    assert found == {("2", "3"), ("3", "2")}  # ',' is not unique in A; 'x' has letters and is not a symbol


def test_names(tmp_path):
    store = store_with(
        tmp_path,
        {
            "s": "Παῦλος/Παῦλος/PROPN ἀπόστολος/ἀπόστολος/NOUN Ἔφεσος/Ἔφεσος/PROPN",
            "t": "Ἰησοῦς/Ἰησοῦς/PROPN ὁ/ὁ/DET",
        },
        {
            "s": "بولس/بولس/X/LTranslit=būlus رسول/رسول/NOUN/Translit=rasūl افسس/افسس/NOUN/LTranslit=ʾafasus",
            "t": "يسوع/يسوع/NOUN/Translit=yswʿ يسوع/يسوع/NOUN/Translit=yasūʿ",
        },
    )
    rules = Rules(store, "pred", RuleSettings(rules=["names"]))
    assert {(p.source, p.target) for p in rules.propose("s")} == {("1", "1"), ("3", "3")}
    assert rules.propose("t") == []  # two equally good matches: no link


def test_names_skip_function_words(tmp_path):
    store = store_with(tmp_path, {"s": "Ἰησοῦς/Ἰησοῦς/PROPN"}, {"s": "س/س/ADP/Translit=s"})
    assert Rules(store, "pred", RuleSettings(rules=["names"])).propose("s") == []


def test_lexicon(tmp_path):
    store = store_with(
        tmp_path,
        {"s": "kai/kai/CCONJ logos/logos/NOUN", "two": "logos/logos/NOUN logos/logos/NOUN", "none": "logos/logos/NOUN x/x/X"},
        {"s": "wa/wa/CCONJ kalima/kalima/NOUN", "two": "kalima/kalima/NOUN", "none": "y/y/X"},
    )
    rules = Rules(store, "pred", RuleSettings(rules=["lexicon"]))
    (proposal,) = rules.propose("s")
    assert (proposal.source, proposal.target, proposal.rule) == ("2", "2", "lexicon")
    assert proposal.reason == "'logos' is linked to 'kalima' in 5 of 5 occurrences"
    assert rules.propose("two") == []  # the lemma is not unique in its sentence (and kalima's evidence is 5/7)
    assert rules.propose("none") == []  # no counterpart in the other sentence
    assert rules.propose("s", links=[proposal.link.model_copy(update={"source": "1"})]) == []  # counterpart already linked
    strict = Rules(store, "pred", RuleSettings(rules=["lexicon"], min_count=6))
    assert strict.propose("s") == []


def test_lexicon_without_evidence(tmp_path):
    store = parallel_store(tmp_path, {"s": "kai/kai/CCONJ", "t": "kai/kai/CCONJ"}, {"s": "wa/wa/CCONJ", "t": "wa/wa/CCONJ"}, {"t": "1-1"})
    rules = Rules(store, "pred", RuleSettings(rules=["lexicon"], min_count=1), evidence=["silver"])
    assert rules.propose("t") == []  # leaving t out leaves no linked occurrence
    store.set_links("pred", "s", "1-1", confidence=0.5)
    weak = Rules(store, "pred", RuleSettings(rules=["lexicon"], min_count=1), evidence=["pred"])
    assert weak.propose("t", links=[]) == []  # weak links are no evidence
    trusting = Rules(store, "pred", RuleSettings(rules=["lexicon"], min_count=1, evidence_confidence=0.5), evidence=["pred"])
    assert [p.reason for p in trusting.propose("t", links=[])] == ["'kai' is linked to 'wa' in 1 of 1 occurrences"]


def test_lexicon_no_entry(tmp_path):
    (tmp_path / "x").mkdir()
    store = parallel_store(tmp_path / "x", {"s": "kai/kai/CCONJ"}, {"s": "wa/wa/CCONJ"})
    rules = Rules(store, "pred", RuleSettings(rules=["lexicon"], min_count=1), evidence=[])
    assert rules.propose("s") == []


def test_apply_and_refresh(tmp_path):
    store = store_with(tmp_path, {"s": "kai/kai/CCONJ logos/logos/NOUN"}, {"s": "wa/wa/CCONJ kalima/kalima/NOUN", "only_b": "x/x/X"})
    rules = Rules(store, "pred")
    report = rules.apply()  # leaving each e* sentence out leaves 4 < 5 examples: only s is linked
    assert report.sentences == 6 and report.rules["lexicon"].links == 1 and report.total == 1
    view = store.get_parallel("pred", "s")
    assert view.links == "2-2S" and view.confidence["2-2"] == RULE_CONFIDENCE
    assert store.alignment("pred").history[-1].agent == "rules"
    rules.refresh()
    assert rules.apply(["s"]).total == 0  # already linked


def test_measure(tmp_path):
    store = store_with(tmp_path, {"s": "kai/kai/CCONJ logos/logos/NOUN"}, {"s": "wa/wa/CCONJ kalima/kalima/NOUN"}, {"s": "1-2"})
    report, outcomes = measure(Rules(store, "silver", RuleSettings(min_count=4, min_share=0.8)), "silver")
    assert report.sentences == 6 and report.reference_links == 6
    count = report.rules["lexicon"]
    assert (count.links, count.correct, count.precision) == (6, 5, round(5 / 6, 4))
    assert [p.sent_id for p, ok in outcomes if not ok] == ["s"]
    report, _ = measure(Rules(store, "silver"), "silver", ["e0"])
    assert report.sentences == 1


def test_proposal_link():
    proposal = Proposal(sent_id="s", source="1", target="2", rule="x", confidence=0.9, reason="")
    assert proposal.link.ugarit() == "1-2S" and proposal.link.confidence == 0.9
