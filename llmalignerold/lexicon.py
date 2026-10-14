from __future__ import annotations

from collections import defaultdict
from typing import Any

import conllu


def _iter_tokens(conllu_text: str):
    if not conllu_text:
        return
    for sent in conllu.parse(conllu_text):
        for token in sent:
            token_id = token.get("id")
            if not isinstance(token_id, int):
                continue
            yield token


def _token_lemma(token: dict[str, Any]) -> str:
    lemma = token.get("lemma")
    if lemma in (None, "", "_"):
        lemma = token.get("form")
    return lemma or ""


def _parse_alignment(alignment: str | None) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    map_1_to_2: dict[int, set[int]] = defaultdict(set)
    map_2_to_1: dict[int, set[int]] = defaultdict(set)

    if not alignment:
        return map_1_to_2, map_2_to_1

    for link in alignment.split():
        link = link.strip()
        if not link:
            continue
        if link[-1] in {"S", "P"}:
            link = link[:-1]
        if "-" not in link:
            continue
        left, right = link.split("-", 1)
        try:
            left_id = int(left)
            right_id = int(right)
        except ValueError:
            continue
        map_1_to_2[left_id].add(right_id)
        map_2_to_1[right_id].add(left_id)

    return map_1_to_2, map_2_to_1


def _empty_lexicon_entry():
    return {
        "occurrences": 0,
        "no_alignments": 0,
        "alignments": defaultdict(int),
        "pos_counts": defaultdict(int),
    }


def build_lexicon(data: dict, corpus1: str, corpus2: str) -> tuple[dict, dict]:
    """
    Build lexicons for both corpora from alignment data.
    Returns (lexicon1, lexicon2).
    """
    lex1: dict[str, dict[str, Any]] = defaultdict(_empty_lexicon_entry)
    lex2: dict[str, dict[str, Any]] = defaultdict(_empty_lexicon_entry)

    for item in data.values():
        item1 = item.get(corpus1)
        item2 = item.get(corpus2)
        if item1 is None or item2 is None:
            continue

        alignment = item.get("alignment") or item.get("align")
        map_1_to_2, map_2_to_1 = _parse_alignment(alignment)

        conllu1 = item1.get("conllu", "")
        conllu2 = item2.get("conllu", "")

        tokens1 = {t["id"]: t for t in _iter_tokens(conllu1)}
        tokens2 = {t["id"]: t for t in _iter_tokens(conllu2)}

        for token_id, token in tokens1.items():
            lemma = _token_lemma(token)
            entry = lex1[lemma]
            entry["occurrences"] += 1
            pos = token.get("upos")
            if pos:
                entry["pos_counts"][pos] += 1
            aligned_ids = map_1_to_2.get(token_id)
            if not aligned_ids:
                entry["no_alignments"] += 1
                continue
            for other_id in aligned_ids:
                other_token = tokens2.get(other_id)
                if other_token is None:
                    continue
                other_lemma = _token_lemma(other_token)
                entry["alignments"][other_lemma] += 1

        for token_id, token in tokens2.items():
            lemma = _token_lemma(token)
            entry = lex2[lemma]
            entry["occurrences"] += 1
            pos = token.get("upos")
            if pos:
                entry["pos_counts"][pos] += 1
            aligned_ids = map_2_to_1.get(token_id)
            if not aligned_ids:
                entry["no_alignments"] += 1
                continue
            for other_id in aligned_ids:
                other_token = tokens1.get(other_id)
                if other_token is None:
                    continue
                other_lemma = _token_lemma(other_token)
                entry["alignments"][other_lemma] += 1

    # Convert nested defaultdicts to plain dicts for serialization
    def finalize(lexicon: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        out = {}
        for lemma in sorted(lexicon.keys()):
            entry = lexicon[lemma]
            pos_counts = entry["pos_counts"]
            part_of_speech = None
            if pos_counts:
                part_of_speech = max(pos_counts.items(), key=lambda x: x[1])[0]
            out[lemma] = {
                "occurrences": entry["occurrences"],
                "no_alignments": entry["no_alignments"],
                "part_of_speech": part_of_speech,
                "alignments": dict(entry["alignments"]),
            }
        return out

    return finalize(lex1), finalize(lex2)
