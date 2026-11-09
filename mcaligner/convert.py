"""Convert the old YAML format (both parses + an alignment per verse) to CoNLL-U and JSON Lines.

The old mcaligner kept everything in one YAML file::

    B10K1V1:
      ArabGr1-Arabic-Ephesians-Parsed:  {text: ..., verse: ..., conllu: ..., id: B10K1V1}
      ArabGr1-GreekVorlage-Ephesians-Parsed: {...}
      alignment: 1-1S 2-2S 3-3P

:func:`convert` writes one CoNLL-U file per corpus (``sent_id`` = the verse id,
``# text`` and the other fields as comments) and the alignments as an
MCParser alignment set (JSON Lines), which can then be loaded read-only as
silver data or used as the start of a writable set.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from mcparser.corpus import CorpusError, Sentence, format_conllu, parse_conllu
from mcparser.corpus.alignment import Link, parse_ugarit
from pydantic import BaseModel, Field

ALIGNMENT_KEYS = ("alignment", "align")
SKIPPED_FIELDS = ("conllu", "id", "text")


class ConvertReport(BaseModel):
    corpus_a: str
    corpus_b: str
    conllu_a: Path
    conllu_b: Path
    alignment: Path
    sentences_a: int
    sentences_b: int
    pairs: int = Field(description="Verses with links.")
    links: int
    dropped_links: list[str] = Field(default_factory=list, description="'sent_id link' for links to missing words.")
    repaired_lines: int = Field(0, description="Token lines with fewer than 10 columns, padded with '_'.")


def corpus_names(data: dict) -> tuple[str, str]:
    """The two corpus keys, in the order of the first verse that has them."""
    for item in data.values():
        names = [key for key, value in item.items() if key not in ALIGNMENT_KEYS and isinstance(value, dict)]
        if len(names) >= 2:
            return names[0], names[1]
    raise CorpusError("No verse has two corpora; expected {verse: {corpus_a: {...}, corpus_b: {...}, alignment: ...}}.")


def _pad(conllu: str) -> tuple[str, int]:
    """Pad token lines with missing trailing columns (seen on some multiword lines) to 10 columns."""
    lines, repaired = [], 0
    for line in conllu.splitlines():
        cells = line.split("\t")
        if not line.startswith("#") and 1 < len(cells) < 10:
            cells += ["_"] * (10 - len(cells))
            repaired += 1
        lines.append("\t".join(cells))
    return "\n".join(lines), repaired


def build_sentence(sent_id: str, item: dict) -> tuple[Sentence, int]:
    """One verse of one corpus as a sentence with ``sent_id``, ``text`` and the other fields as comments."""
    conllu, repaired = _pad(item.get("conllu") or "")
    try:
        (sentence,) = parse_conllu(conllu)
    except ValueError:
        raise CorpusError(f"Verse {sent_id}: expected exactly one sentence of CoNLL-U.") from None
    except CorpusError as error:
        raise CorpusError(f"Verse {sent_id}: {error}") from None
    sentence.set_meta("sent_id", sent_id)
    if item.get("text"):
        sentence.set_meta("text", " ".join(str(item["text"]).split()))
    for key, value in item.items():
        if key not in SKIPPED_FIELDS and value is not None:
            sentence.set_meta(key, " ".join(str(value).split()))
    return sentence, repaired


def _links(sent_id: str, text: str, a: Sentence, b: Sentence, dropped: list[str]) -> list[Link]:
    ids_a, ids_b = {word.id for word in a.words}, {word.id for word in b.words}
    links: dict[str, Link] = {}
    for link in parse_ugarit(text):
        if link.source in ids_a and link.target in ids_b:
            links.setdefault(link.key, link)
        else:
            dropped.append(f"{sent_id} {link.ugarit()}")
    return sorted(links.values(), key=lambda link: (int(link.source), int(link.target)))


def convert(input_path: Path | str, output: Path | str, name: str | None = None) -> ConvertReport:
    """Write ``<corpus A>.conllu``, ``<corpus B>.conllu`` and ``<name>.jsonl`` (default: the input's stem) to ``output``."""
    input_path, output = Path(input_path), Path(output)
    data = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
    corpus_a, corpus_b = corpus_names(data)
    sentences: dict[str, list[Sentence]] = {corpus_a: [], corpus_b: []}
    lines, dropped, repaired = [], [], 0
    links_total = 0
    for verse_id, item in data.items():
        sent_id = str(verse_id)
        pair = []
        for corpus in (corpus_a, corpus_b):
            if not isinstance(item.get(corpus), dict):
                continue
            sentence, fixed = build_sentence(sent_id, item[corpus])
            sentences[corpus].append(sentence)
            repaired += fixed
            pair.append(sentence)
        text = next((item[key] for key in ALIGNMENT_KEYS if item.get(key)), None)
        if len(pair) == 2 and text:
            links = _links(sent_id, str(text), pair[0], pair[1], dropped)
            if links:
                links_total += len(links)
                record = {"sent_id": sent_id, "links": [link.model_dump(exclude_none=True) for link in links]}
                lines.append(json.dumps(record, ensure_ascii=False))
    output.mkdir(parents=True, exist_ok=True)
    paths = {corpus: output / f"{corpus}.conllu" for corpus in sentences}
    for corpus, path in paths.items():
        path.write_text(format_conllu(sentences[corpus]), encoding="utf-8")
    alignment = output / f"{name or input_path.stem}.jsonl"
    alignment.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return ConvertReport(
        corpus_a=corpus_a,
        corpus_b=corpus_b,
        conllu_a=paths[corpus_a],
        conllu_b=paths[corpus_b],
        alignment=alignment,
        sentences_a=len(sentences[corpus_a]),
        sentences_b=len(sentences[corpus_b]),
        pairs=len(lines),
        links=links_total,
        dropped_links=dropped,
        repaired_lines=repaired,
    )
