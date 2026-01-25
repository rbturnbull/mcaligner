import pytest
from types import SimpleNamespace
from pathlib import Path
import os

retriv = pytest.importorskip("retriv")

from llmaligner.database import database_retriv as mod
from llmaligner.database.database_retriv import (
    DatabaseRetriv,
    build_id_set,
    build_retriv_collection,
    build_database,
    search_database,
)


def test_iter_yields_docs(monkeypatch):
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(index_name="myindex")
    db.path = Path("/tmp/base")

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
    db.path = Path("/tmp/base")

    with pytest.raises(RuntimeError):
        next(iter(db))


def test_build_retriv_collection_reads_yaml(tmp_path):
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text(
        "doc1:\n"
        "  id: doc1\n"
        "  text: hello\n"
        "doc2:\n"
        "  id: doc2\n"
        "  text: goodbye\n"
    )

    collection = build_retriv_collection(yaml_path)

    assert collection == [
        {"id": "doc1", "text": "hello"},
        {"id": "doc2", "text": "goodbye"},
    ]


def test_call_requires_loaded_db():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = None
    db.path = Path("/tmp/base")

    with pytest.raises(RuntimeError):
        db("query", k=2)


def test_call_uses_search_with_cutoff():
    def fake_search(query, return_docs=False, cutoff=10):
        assert query == "hello"
        assert return_docs is True
        assert cutoff == 4
        return [{"id": "doc1"}]

    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(search=fake_search)
    db.path = Path("/tmp/base")

    assert db("hello", k=4) == [{"id": "doc1"}]


def test_getitem_single_id():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(get_doc=lambda doc_id: {"id": doc_id})
    db.path = Path("/tmp/base")

    assert db["doc_123"] == {"id": "doc_123"}


def test_getitem_multiple_ids():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(get_docs=lambda ids: [{"id": i} for i in ids])
    db.path = Path("/tmp/base")

    assert db[("doc_123", "doc_456")] == [{"id": "doc_123"}, {"id": "doc_456"}]
    assert db[["doc_123", "doc_456"]] == [{"id": "doc_123"}, {"id": "doc_456"}]


def test_getitem_requires_loaded_db():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = None
    db.path = Path("/tmp/base")

    with pytest.raises(RuntimeError):
        _ = db["doc_123"]


def test_getitem_invalid_key_type():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(get_doc=lambda _: None, get_docs=lambda _: [])
    db.path = Path("/tmp/base")

    with pytest.raises(TypeError):
        _ = db[123]


def test_similarity_search_wraps_results():
    def fake_search(query, return_docs=False, cutoff=10):
        assert query == "hello"
        assert return_docs is True
        assert cutoff == 3
        return [{"id": "doc1"}]

    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(search=fake_search)
    db.path = Path("/tmp/base")

    results = db.similarity_search("hello", k=3)

    assert len(results) == 1
    assert results[0].metadata == {"id": "doc1"}


def test_search_database_calls_db():
    calls = []

    class DummyDB:
        def __call__(self, query, k=10):
            calls.append((query, k))
            return [{"id": "doc1"}]

    db = DummyDB()
    assert search_database(db, "hi", cutoff=5) == [{"id": "doc1"}]
    assert calls == [("hi", 5)]


def test_build_database_delegates_to_classmethod(monkeypatch, tmp_path):
    calls = []

    def fake_build(yaml_path, output_path, index_name="index"):
        calls.append((yaml_path, output_path, index_name))
        return "built"

    monkeypatch.setattr(DatabaseRetriv, "build", classmethod(lambda cls, y, o, index_name="index": fake_build(y, o, index_name)))

    yaml_path = tmp_path / "input.yaml"
    output_path = tmp_path / "out"
    result = build_database(yaml_path, output_path, index_name="custom")

    assert result == "built"
    assert calls == [(yaml_path, output_path, "custom")]


def test_build_indexes_and_returns_instance(monkeypatch, tmp_path):
    collection = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    calls = {"index": [], "init": []}

    class FakeSR:
        def __init__(self, index_name="index"):
            calls["init"].append(index_name)
            self.index_name = index_name

        def index(self, batch, show_progress=False):
            calls["index"].append((list(batch), show_progress))

    class FakeProgress:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_task(self, _label, total=0):
            return 1

        def update(self, _task_id, advance=0):
            return None

    monkeypatch.setattr(mod, "build_retriv_collection", lambda _: collection)
    monkeypatch.setattr(mod, "SparseRetriever", FakeSR)
    monkeypatch.setattr(mod, "Progress", FakeProgress)
    monkeypatch.setattr(DatabaseRetriv, "load", lambda self, path: setattr(self, "db", "loaded"))

    yaml_path = tmp_path / "input.yaml"
    output_path = tmp_path / "out"

    result = DatabaseRetriv.build(yaml_path, output_path, index_name="custom")

    assert isinstance(result, DatabaseRetriv)
    assert result.index_name == "custom"
    assert result.path == output_path
    assert output_path.exists()
    assert calls["init"] == ["custom"]
    assert calls["index"] == [(collection, False)]


def test_load_sets_env_and_db(monkeypatch, tmp_path):
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.index_name = "myindex"

    created = {}

    def fake_load(index_name="index"):
        created["index_name"] = index_name
        return SimpleNamespace()

    monkeypatch.setattr(mod.SparseRetriever, "load", staticmethod(fake_load))

    path = tmp_path / "db"
    path.mkdir()
    db.load(path)

    assert os.environ["RETRIV_BASE_PATH"] == str(path)
    assert created["index_name"] == "myindex"
    assert isinstance(db.db, SimpleNamespace)


def test_build_id_set_initializes_mapping():
    class FakeSR:
        def __init__(self):
            self.id_mapping = None
            self.called = False

        def initialize_id_mapping(self):
            self.called = True
            self.id_mapping = {0: "a", 1: "b"}

    sr = FakeSR()
    assert build_id_set(sr) == {"a", "b"}
    assert sr.called is True


def test_contains_uses_id_set():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = SimpleNamespace(id_mapping={0: "x", 1: "y"})
    db.path = Path("/tmp/base")

    assert "x" in db
    assert "z" not in db


def test_contains_requires_loaded_db():
    db = DatabaseRetriv.__new__(DatabaseRetriv)
    db.db = None
    db.path = Path("/tmp/base")

    with pytest.raises(RuntimeError):
        _ = "x" in db
