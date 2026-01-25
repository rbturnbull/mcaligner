from types import SimpleNamespace

import pytest

import llmaligner.align as align
from llmaligner.align import retrieve_examples, merge_data, align_items


class DummyDB:
    def __init__(self, expected_query, results):
        self.expected_query = expected_query
        self.results = results
        self.calls = []

    def __call__(self, query, k):
        self.calls.append((query, k))
        assert query == self.expected_query
        return self.results


class DummyIterDB:
    def __init__(self, items, search_results=None):
        self._items = items
        self._items_by_id = {item.get("id"): item for item in items}
        self._search_results = search_results or {}
        self.calls = []

    def __iter__(self):
        return iter(self._items)

    def get(self, item_id, default=None):
        return self._items_by_id.get(item_id, default)

    def __contains__(self, item_id):
        return item_id in self._items_by_id

    def __getitem__(self, item_id):
        return self._items_by_id[item_id]

    def __call__(self, query, k):
        self.calls.append((query, k))
        return self._search_results.get(query, [])


def test_retrieve_examples_mix_and_sort():
    item = {
        "c1": {"text": "hello"},
        "c2": {"text": "bonjour"},
    }

    results1 = [
        {"id": "a", "score": 0.1},
        {"id": "b", "score": 0.2},
        {"id": "c", "score": 0.3},
        {"id": "d", "score": 0.4},
    ]
    results2 = [
        {"id": "e", "score": 0.9},
        {"id": "b", "score": 0.8},
        {"id": "f", "score": 0.5},
        {"id": "g", "score": 0.7},
    ]

    db1 = DummyDB("hello", results1)
    db2 = DummyDB("bonjour", results2)

    example_ids = retrieve_examples(
        db1,
        db2,
        item,
        corpus1="c1",
        corpus2="c2",
        n_examples=6,
    )

    assert db1.calls == [("hello", 6)]
    assert db2.calls == [("bonjour", 6)]

    # First third from db1 -> a, b; first third from db2 adds e (b already present)
    # Remaining sorted by score from c,d,f,g -> g(0.7), f(0.5), d(0.4)
    assert example_ids == ["a", "b", "e", "g", "f", "d"]

    example_ids = retrieve_examples(
        db1,
        db2,
        item,
        corpus1="c1",
        corpus2="c2",
        n_examples=10,
    )
    assert example_ids == ["a", "b", "c", "e", "f", "g", "d"]

    example_ids = retrieve_examples(
        db1,
        db2,
        item,
        corpus1="c1",
        corpus2="c2",
        n_examples=3,
    )
    assert example_ids == ["a", "e", "b"]


def test_merge_data_combines_and_fills_none():
    db1 = DummyIterDB(
        [
            {"id": "a", "text": "one"},
            {"id": "b", "text": "two"},
        ]
    )
    db2 = DummyIterDB(
        [
            {"id": "a", "text": "uno"},
            {"id": "c", "text": "tres"},
        ]
    )

    data = merge_data(db1, db2, "c1", "c2")

    assert data["a"]["c1"]["text"] == "one"
    assert data["a"]["c2"]["text"] == "uno"
    assert data["b"]["c1"]["text"] == "two"
    assert data["b"]["c2"] is None
    assert data["c"]["c1"] is None
    assert data["c"]["c2"]["text"] == "tres"


def test_align_items_runs_and_writes(monkeypatch, tmp_path):
    db1 = DummyIterDB(
        [
            {"id": "1", "text": "hello", "conllu": "1\thello\n"},
            {"id": "2", "text": "skip", "conllu": "1\tskip\n"},
        ],
        search_results={"hello": [{"id": "ex1"}], "skip": [{"id": "ex2"}]},
    )
    db2 = DummyIterDB(
        [
            {"id": "1", "text": "bonjour", "conllu": "1\tbonjour\n"},
        ],
        search_results={"bonjour": [{"id": "ex3"}]},
    )

    recorded = {"build_chain": [], "write_yaml": []}

    def fake_retrieve_examples(database1, database2, item, corpus1, corpus2, n_examples):
        return ["ex1"]

    def fake_build_chain(llm, data, item_id, example_ids, corpus1, corpus2, guidelines):
        recorded["build_chain"].append(
            (item_id, tuple(example_ids), corpus1, corpus2, guidelines)
        )
        return SimpleNamespace(invoke=lambda _: "1-1S")

    def fake_write_yaml(data, output):
        recorded["write_yaml"].append((output, data))

    monkeypatch.setattr(align, "retrieve_examples", fake_retrieve_examples)
    monkeypatch.setattr(align, "build_chain", fake_build_chain)
    monkeypatch.setattr(align, "write_yaml", fake_write_yaml)
    monkeypatch.setattr(align, "load_file", lambda _: {})

    output = tmp_path / "out.yaml"
    data = align_items(
        db1,
        db2,
        corpus1="c1",
        corpus2="c2",
        llm=SimpleNamespace(),
        n_examples=2,
        output=output,
        guidelines="",
    )

    assert data["1"]["alignment"] == "1-1S"
    assert "2" in data
    assert "align" not in data["2"]
    assert recorded["build_chain"] == [("1", ("ex1",), "c1", "c2", "")]
    assert recorded["write_yaml"][0][0] == output
