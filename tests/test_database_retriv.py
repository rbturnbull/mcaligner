import pytest
from types import SimpleNamespace
from pathlib import Path

retriv = pytest.importorskip("retriv")

from llmaligner.database import database_retriv as mod
from llmaligner.database.database_retriv import DatabaseRetriv


def test_iter_yields_docs(monkeypatch):
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(index_name="myindex")

    def fake_docs_path(index_name):
        assert index_name == "myindex"
        return Path("/tmp/fake.jsonl")

    def fake_read_jsonl(path, generator=False):
        assert path == Path("/tmp/fake.jsonl")
        assert generator is True
        return iter([{"id": 1}, {"id": 2}])

    monkeypatch.setattr(mod, "docs_path", fake_docs_path)
    monkeypatch.setattr(mod, "read_jsonl", fake_read_jsonl)

    assert list(db) == [{"id": 1}, {"id": 2}]


def test_iter_requires_loaded_db():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = None

    with pytest.raises(RuntimeError):
        next(iter(db))


def test_getitem_single_id():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(get_doc=lambda doc_id: {"id": doc_id})

    assert db["doc_123"] == {"id": "doc_123"}


def test_getitem_multiple_ids():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(get_docs=lambda ids: [{"id": i} for i in ids])

    assert db[("doc_123", "doc_456")] == [{"id": "doc_123"}, {"id": "doc_456"}]
    assert db[["doc_123", "doc_456"]] == [{"id": "doc_123"}, {"id": "doc_456"}]


def test_getitem_requires_loaded_db():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = None

    with pytest.raises(RuntimeError):
        _ = db["doc_123"]
