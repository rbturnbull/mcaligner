from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcparser.corpus import CorpusStore
from pydantic_ai import models

from mcaligner.convert import convert

models.ALLOW_MODEL_REQUESTS = False  # never call a real model from the tests

DATA = Path(__file__).parent / "data"
SAMPLE = DATA / "sample.yaml"
ARABIC = "ArabGr1-Arabic-Ephesians-Parsed"
GREEK = "ArabGr1-GreekVorlage-Ephesians-Parsed"


@pytest.fixture
def converted(tmp_path: Path):
    """The 3-verse sample converted to CoNLL-U + JSONL in a temporary directory."""
    return convert(SAMPLE, tmp_path / "data", name="silver")


@pytest.fixture
def store(converted) -> CorpusStore:
    """Arabic + Greek sources, the silver alignments (read-only) and an empty writable set ``pred``."""
    store = CorpusStore()
    store.add_source("ar", converted.conllu_a)
    store.add_source("grc", converted.conllu_b)
    store.add_alignment("silver", "ar", "grc", converted.alignment, mode="ro")
    store.add_alignment("pred", "ar", "grc", converted.alignment.parent / "pred.jsonl")
    return store


@pytest.fixture
def anyio_backend():
    return "asyncio"


def conllu(sentences: dict[str, str]) -> str:
    """Tiny CoNLL-U from ``{sent_id: "form/lemma/UPOS[/MISC] ..."}`` (heads: all on word 1)."""
    blocks = []
    for sent_id, words in sentences.items():
        lines = [f"# sent_id = {sent_id}"]
        for index, item in enumerate(words.split(), start=1):
            form, lemma, upos, *misc = item.split("/")
            head, deprel = ("0", "root") if index == 1 else ("1", "dep")
            lines.append("\t".join([str(index), form, lemma, upos, "_", "_", head, deprel, "_", misc[0] if misc else "_"]))
        blocks.append("\n".join(lines) + "\n\n")
    return "".join(blocks)


def parallel_store(tmp_path, a: dict[str, str], b: dict[str, str], silver: dict[str, str] | None = None) -> CorpusStore:
    """Sources ``a`` and ``b``, a read-only set ``silver`` (Ugarit text per sent_id) and an empty writable set ``pred``."""
    (tmp_path / "a.conllu").write_text(conllu(a), encoding="utf-8")
    (tmp_path / "b.conllu").write_text(conllu(b), encoding="utf-8")
    lines = []
    for sent_id, links in (silver or {}).items():
        items = [{"source": l.split("-")[0], "target": l.split("-")[1]} for l in links.split()]
        lines.append(json.dumps({"sent_id": sent_id, "links": items}))
    (tmp_path / "silver.jsonl").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    store = CorpusStore()
    store.add_source("a", tmp_path / "a.conllu")
    store.add_source("b", tmp_path / "b.conllu")
    store.add_alignment("silver", "a", "b", tmp_path / "silver.jsonl", mode="ro")
    store.add_alignment("pred", "a", "b", tmp_path / "pred.jsonl")
    return store
