from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from types import SimpleNamespace

import conllu
from retriv import SparseRetriever
from retriv.paths import docs_path
from oneliner_utils import read_jsonl

from rich.progress import Progress, track

from .database_base import DEFAULT_NUM_RESULTS, DatabaseBase
from ..io import yaml_to_dict

def build_retriv_collection(yaml_path: Path) -> list[dict[str, Any]]:
    """
    """
    data_as_dict = yaml_to_dict(yaml_path)
    collection = list(data_as_dict.values())
    return collection


class DatabaseRetriv(DatabaseBase):
    def __init__(self, path: Path | str, index_name: str = "index"):
        self.index_name = index_name
        self.db: SparseRetriever | None = None
        super().__init__(path)

    @classmethod
    def build(cls, yaml_path: Path, output_path: Path, index_name: str = "index") -> "DatabaseRetriv":
        """
        Build a retriv sparse index (BM25) called 'index' and persist it under output_path.

        retriv stores indices under a "base path". We set RETRIV_BASE_PATH so you fully control
        where the index lives on disk.
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        os.environ["RETRIV_BASE_PATH"] = str(output_path)

        collection = build_retriv_collection(yaml_path)
        print(f"Indexing {len(collection)} items into retriv base path: {output_path}")

        sr = SparseRetriever(index_name=index_name)

        batch_size = 2_000
        with Progress() as progress:
            task = progress.add_task("[cyan]Indexing documents...", total=len(collection))
            for start in range(0, len(collection), batch_size):
                batch = collection[start : start + batch_size]
                sr.index(batch, show_progress=False)
                progress.update(task, advance=len(batch))

        return cls(output_path, index_name=index_name)

    def load(self, path: Path | str) -> None:
        path = Path(path)
        assert path.exists(), f"Database path {path} does not exist"

        os.environ["RETRIV_BASE_PATH"] = str(path)
        self.db = SparseRetriever(index_name=self.index_name)

    def __call__(self, query: str, k: int = DEFAULT_NUM_RESULTS) -> list[dict]:
        if self.db is None:
            raise RuntimeError("Database is not loaded.")
        return self.db.search(query, return_docs=True, cutoff=k)

    def __iter__(self):
        if self.db is None:
            raise RuntimeError("Database is not loaded.")
        for doc in read_jsonl(docs_path(self.db.index_name), generator=True):
            yield doc

    def __getitem__(self, key: str | tuple[str, ...] | list[str]):
        if self.db is None:
            raise RuntimeError("Database is not loaded.")
        if isinstance(key, str):
            return self.db.get_doc(key)
        if isinstance(key, (list, tuple)):
            return self.db.get_docs(list(key))
        raise TypeError("Key must be a string or a list/tuple of strings.")

    def similarity_search(self, query: str, k: int = DEFAULT_NUM_RESULTS):
        if self.db is None:
            raise RuntimeError("Database is not loaded.")
        results = self.db.search(query, return_docs=True, cutoff=k)
        return [SimpleNamespace(metadata=result) for result in results]


def build_database(yaml_path: Path, output_path: Path, index_name: str = "index") -> DatabaseRetriv:
    return DatabaseRetriv.build(yaml_path, output_path, index_name=index_name)


def load_database(path: Path | str, index_name: str = "index") -> DatabaseRetriv:
    return DatabaseRetriv(path, index_name=index_name)


def search_database(db: DatabaseRetriv, query: str, cutoff: int = 10) -> list[dict[str, Any]]:
    return db(query, k=cutoff)
