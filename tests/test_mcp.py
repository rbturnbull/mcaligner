from __future__ import annotations

import pytest
from mcparser.corpus import NotFoundError
from mcp import Client

from mcaligner.mcp import build_server, tools


def first_ids(store):
    return [s.sent_id for s in store.alignment("silver").source_a.sentences]


def test_similar_pairs(store):
    ids = first_ids(store)
    result = tools.similar_pairs(store, "silver", ids[0], limit=5)
    assert result["sent_id"] == ids[0]
    assert ids[0] not in [hit["sent_id"] for hit in result["pairs"]]
    assert result["pairs"]
    scores = [hit["score"] for hit in result["pairs"]]
    assert scores == sorted(scores, reverse=True)
    assert "~" in result["pairs"][0]["links"]
    assert tools.similar_pairs(store, "silver", ids[0], limit=1)["pairs"][:1] == result["pairs"][:1]


def test_similar_pairs_unrelated_pair_is_skipped(store):
    ids = first_ids(store)
    aset = store.alignment("silver")
    assert tools.similar_pairs(store, "pred", ids[0])["pairs"] == []  # no links in pred
    for source in (aset.source_a, aset.source_b):
        for word in source.sentence(ids[1]).words:
            word.lemma = "zzz" + word.id
    assert ids[1] not in [hit["sent_id"] for hit in tools.similar_pairs(store, "silver", ids[0], 50)["pairs"]]


def test_pairs_skip_missing_sentences(store):
    aset = store.alignment("silver")
    aset.pairs["B99"] = list(next(iter(aset.pairs.values())))
    assert all(hit["sent_id"] != "B99" for hit in tools.similar_pairs(store, "silver", first_ids(store)[0], 50)["pairs"])


def lemma_with_links(store):
    aset = store.alignment("silver")
    sent_id = first_ids(store)[0]
    link = aset.links(sent_id)[0]
    a = aset.source_a.sentence(sent_id)
    b = aset.source_b.sentence(sent_id)
    word_a = next(w for w in a.words if w.id == link.source)
    word_b = next(w for w in b.words if w.id == link.target)
    from mcaligner.lexicon import lemma_of

    return sent_id, lemma_of(word_a), lemma_of(word_b)


def test_lemma_links_both_sides(store):
    sent_id, lemma_a, lemma_b = lemma_with_links(store)
    result = tools.lemma_links(store, "silver", lemma_a, "a")
    assert result["occurrences"] >= 1 and result["linked_lemmas"]
    assert any(sent_id == e["sent_id"] for e in result["examples"])
    assert tools.lemma_links(store, "silver", lemma_b, "b")["linked_lemmas"]
    left_out = tools.lemma_links(store, "silver", lemma_a, "a", exclude_sentence=f"silver:{sent_id}")
    assert all(e["sent_id"] != sent_id for e in left_out["examples"])
    assert tools.lemma_links(store, "silver", lemma_a, "a", min_confidence=1.1)["linked_lemmas"] == []
    assert tools.lemma_links(store, "silver", lemma_a, "a", min_confidence=1.1)["unlinked_in"]
    assert tools.lemma_links(store, "silver", "no-such-lemma")["occurrences"] == 0


def test_link_examples(store):
    sent_id, lemma_a, lemma_b = lemma_with_links(store)
    result = tools.link_examples(store, "silver", lemma_a, lemma_b)
    assert result["linked_in"] >= 1 and "~" in result["linked"][0]["links"][0]
    none = tools.link_examples(store, "silver", lemma_a, lemma_b, min_confidence=1.1, exclude_sentence=sent_id)
    assert none["linked_in"] == 0
    assert tools.link_examples(store, "silver", lemma_a, "no-such-lemma")["cooccur_unlinked_in"] == 0


def test_link_examples_cooccurring_without_link(store):
    aset = store.alignment("silver")
    sent_id, lemma_a, lemma_b = lemma_with_links(store)
    aset.pairs[sent_id] = [aset.links(sent_id)[-1]] if len(aset.links(sent_id)) > 1 else aset.links(sent_id)
    result = tools.link_examples(store, "silver", lemma_a, lemma_b, min_confidence=1.1)
    assert result["cooccur_unlinked_in"] >= 1


def test_alignment_stats(store):
    ids = first_ids(store)
    whole = tools.alignment_stats(store, "silver")
    one = tools.alignment_stats(store, "silver", ids[0])
    assert whole["pairs"] == len(ids) and one["pairs"] == 1 and one["sent_id"] == ids[0]
    assert whole["links"] == whole["sure"] + whole["probable"]
    assert whole["mean_confidence"] == 1.0 and whole["below_threshold"] == 0
    assert tools.alignment_stats(store, "pred")["mean_confidence"] is None
    assert tools.alignment_stats(store, "silver", threshold=1.1)["below_threshold"] == whole["links"]


def test_crossings():
    from mcparser.corpus.alignment import Link

    links = [Link(source="1", target="2"), Link(source="2", target="1"), Link(source="3", target="3"), Link(source="2-3", target="x")]
    assert tools._crossings(links) == 1


def test_unknown_alignment(store):
    with pytest.raises(NotFoundError):
        tools.alignment_stats(store, "nope")


@pytest.mark.anyio
async def test_server_exposes_tools(store):
    server = build_server(store)
    assert "similar_pairs" in server.instructions
    names = {t.name for t in await server.list_tools()}
    assert {"similar_pairs", "lemma_links", "link_examples", "alignment_stats", "get_parallel", "set_links"} <= names
    sent_id = first_ids(store)[0]
    lemma = lemma_with_links(store)
    async with Client(server) as client:
        stats = await client.call_tool("alignment_stats", {"alignment": "silver", "sent_id": sent_id})
        assert stats.structured_content["pairs"] == 1
        calls = {
            "similar_pairs": {"alignment": "silver", "sent_id": sent_id},
            "lemma_links": {"alignment": "silver", "lemma": lemma[1]},
            "link_examples": {"alignment": "silver", "lemma_a": lemma[1], "lemma_b": lemma[2]},
        }
        for name, arguments in calls.items():
            assert not (await client.call_tool(name, arguments)).is_error
        failed = await client.call_tool("alignment_stats", {"alignment": "nope"})
        assert failed.is_error
