from __future__ import annotations

from llmaligner.lexicon import TranslationTable, build_lexicon


def test_translation_table(store):
    table = TranslationTable(store)
    assert table.names == ["silver", "pred"]
    apostle = table.entry("ar", "رَسُول")
    assert apostle.occurrences == 1 and apostle.translations["ἀπόστολος"] == 1
    assert apostle.part_of_speech == "NOUN"
    assert table.candidates("ar", "رَسُول", exclude="B10K1V1") == {}
    assert table.candidates("ar", "رَسُول", exclude="B10K1V2")["ἀπόστολος"] == 1
    assert table.candidates("ar", "no such lemma") == {}
    assert apostle.occurrences_without("B10K1V1") == 0 and apostle.occurrences_without(None) == 1
    colon = table.entry("ar", ":")
    assert colon.unaligned_without("B10K1V1") == colon.unaligned - 1 and colon.unaligned_without(None) == colon.unaligned
    assert table.candidates("grc", "Ἰησοῦς")["يَسُوع"] == 2
    assert table.part_of_speech("grc", "Ἰησοῦς") == "PROPN"
    assert table.part_of_speech("grc", "nothing") is None
    # multiword token lines have no UPOS and are not words; punctuation is never linked
    assert table.entry("ar", ":").unaligned == table.entry("ar", ":").occurrences


def test_confidence_and_missing_sentences(store):
    store.set_links("pred", "B10K1V1", "2-2S", confidence=0.3)
    assert TranslationTable(store, ["pred"], min_confidence=0.5).entry("ar", "رَسُول").unaligned == 1
    assert TranslationTable(store, ["pred"]).entry("ar", "رَسُول").unaligned == 0
    store.source("ar").sentence("B10K1V1").words[1].set("upos", "_")  # untagged words have no POS
    assert TranslationTable(store, ["pred"]).entry("ar", "رَسُول").part_of_speech is None
    store.alignment("pred").pairs["nowhere"] = store.alignment("pred").pairs["B10K1V1"]
    assert TranslationTable(store, ["pred"]).entry("ar", "رَسُول").occurrences == 1


def test_build_lexicon(store):
    lexicon = build_lexicon(TranslationTable(store, ["silver"]), min_count=1, top=1)
    entry = lexicon["grc"]["Ἰησοῦς"]
    assert entry["part_of_speech"] == "PROPN"
    assert list(entry["alignments"]) == ["يَسُوع"]
    assert entry["alignments"]["يَسُوع"]["part_of_speech"] == "NOUN"
    assert list(lexicon["ar"]) == sorted(lexicon["ar"])
    assert build_lexicon(TranslationTable(store, ["silver"]), min_count=100)["grc"]["Ἰησοῦς"]["alignments"] == {}
