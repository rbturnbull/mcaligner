from __future__ import annotations

import pytest
from mcparser.corpus.alignment import Link, parse_ugarit
from mcparser.mcp import build_server
from pydantic_ai import ModelRetry
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.function import FunctionModel
from scripted import align, score, scripted

from llmaligner.agents.outputs import Alignment, Applier, Scores, TaskBatch, parse_links, parse_removals, parse_scores
from llmaligner.agents.prompts import PairItem, evidence_lines, instructions, pair_block, task_prompt, word_lines
from llmaligner.agents.team import AlignerTeam, ModelUsage
from llmaligner.agents.toolset import ReadToolset, compact, parallel_view, read_toolset, translations
from llmaligner.lexicon import TranslationTable
from llmaligner.settings import RoleSettings, Settings


def item(store, sent_id, settled="", review=""):
    aset = store.alignment("pred")
    return PairItem(
        sent_id, aset.source_a.sentence(sent_id), aset.source_b.sentence(sent_id), parse_ugarit(settled), parse_ugarit(review)
    )


# ------------------------------------------------------------ prompts


def test_instructions():
    assert "source A (ar)" in instructions("aligner", "ar", "grc", "pred", 0.8)
    text = instructions("scorer", "ar", "grc", "pred", 0.7, extra="  Be strict. ")
    assert "Links below 0.7 go back" in text and text.endswith("Be strict.\n")


def test_word_lines(store):
    lines = word_lines(store.source("ar").sentence("B10K1V1"), ["Gloss", "Nope"])
    assert lines[0] == "1 بولس بُولُس X 2 nsubj Paul"
    assert "5-6 بشيه (token of words 5-6)" in lines


def test_word_lines_skip_empty_nodes():
    from mcparser.corpus import parse_conllu

    (sentence,) = parse_conllu("1\ta\ta\tX\t_\t_\t0\troot\t_\t_\n1.1\tb\tb\tX\t_\t_\t_\t_\t0:root\t_\n")
    assert word_lines(sentence, []) == ["1 a a X 0 root"]


def test_evidence_lines(store):
    table = TranslationTable(store, ["silver"])
    pair = item(store, "B10K1V2", settled="1-1S")
    lines = evidence_lines(pair, table, "ar", "grc", 2)
    assert not any(line.startswith("A1 ") for line in lines)  # linked words get no evidence
    assert "B5 θεός: اَللّٰه×2 (of 2)" in lines and "B10 Ἰησοῦς: يَسُوع×2, مَسِيح×1 (of 3)" in lines
    assert not any("※" in line for line in lines)  # punctuation gets no evidence
    assert evidence_lines(pair, table, "ar", "grc", 0) == []
    assert evidence_lines(pair, TranslationTable(store, []), "ar", "grc", 2) == []  # no entries
    lone = TranslationTable(store, ["silver"])
    for entry in [*lone.entries["grc"].values(), *lone.entries["ar"].values()]:
        entry.by_sentence.clear()
        entry.translations.clear()
    assert evidence_lines(pair, lone, "ar", "grc", 2) == []  # entries without translations
    table.entry("grc", "θεός").unaligned += 1  # as if one occurrence elsewhere had no link
    assert "B5 θεός: اَللّٰه×2 (of 2, 1 unlinked)" in evidence_lines(pair, table, "ar", "grc", 2)


def test_pair_blocks(store):
    pair = item(store, "B10K1V1", settled="1-1S", review="2-2P")
    confidence = {"1-1": 0.95, "2-2": 0.4}
    pair.settled[0].agent = "rules"
    text = pair_block(pair, "aligner", confidence, None, ("ar", "grc"), ["Gloss"], 3)
    assert "Settled links: 1-1S 0.95 rules" in text and "Links to review: 2-2P 0.40" in text
    assert "Evidence" not in text
    scorer = pair_block(pair, "scorer", confidence, None, ("ar", "grc"), [], 3)
    assert "Links to score:\n2-2P رسول→αποστολος" in scorer
    bare = pair_block(item(store, "B10K1V1"), "aligner", {}, None, ("ar", "grc"), [], 3)
    assert "Settled links: none" in bare and "Links to review" not in bare
    prompt = task_prompt("scorer", [pair], {"B10K1V1": confidence}, None, ("ar", "grc"), [], 3)
    assert prompt.startswith("Score the listed links of these 1 sentence pairs.")


# ------------------------------------------------------------ outputs


def test_parse_links():
    batch = TaskBatch("pred", ["v1"])
    links, errors = parse_links("v1 1-2 S 0.9\nv1 3-4P 0.5\n# comment\nv1 5-6 0.7\nv2 1-1 S 0.9\nv1 1-1 S high\nnonsense", batch)
    assert [(l.key, l.sure, l.confidence) for l in links["v1"]] == [("1-2", True, 0.9), ("3-4", False, 0.5), ("5-6", True, 0.7)]
    assert errors == [
        "links line 4: pair 'v2' is not in this task",
        "links line 5: confidence 'high' is not a number",
        "links line 6: expected SENT_ID A-B S|P CONFIDENCE, got 'nonsense'",
    ]
    assert parse_links("v1 1-2 S 7", batch)[0]["v1"][0].confidence == 1.0


def test_parse_removals_and_scores():
    batch = TaskBatch("pred", ["v1"], review={"v1": parse_ugarit("1-2S")})
    removals, errors = parse_removals("v1 1-2S\nv1 3-4\nv2 1-1\nbad", batch)
    assert removals == {"v1": {"1-2", "3-4"}} and len(errors) == 2
    scores, errors = parse_scores("v1 1-2S 0.8\nv1 3-4 0.5\nv2 1-2 0.5\nv1 1-2 x\nbad", batch)
    assert scores == {"v1": {"1-2": 0.8}}
    assert [e.split(":")[1].strip()[:12] for e in errors] == ["v1 3-4 is no", "pair 'v2' is", "confidence '", "expected SEN"]


def test_applier_alignment(store):
    applier = Applier(store)
    store.set_links("pred", "B10K1V1", "1-1S 13-13S", confidence=0.95, agent="rules")
    settled = store.alignment("pred").links("B10K1V1")
    batch = TaskBatch("pred", ["B10K1V1", "B10K1V2"], settled={"B10K1V1": settled})
    with pytest.raises(ModelRetry, match=r"pair B10K1V1: Link 99-1: no word 99"):
        applier.alignment(Alignment(links="B10K1V1 99-1 S 0.9"), batch)
    with pytest.raises(ModelRetry, match="remove line 1"):
        applier.alignment(Alignment(links="", remove="nope"), batch)
    assert store.get_parallel("pred", "B10K1V2").links == ""  # nothing written after a retry
    applier.alignment(Alignment(links="B10K1V1 2-2 S 0.9\nB10K1V1 1-1 S 0.95", remove="B10K1V1 13-13", summary="ok"), batch)
    view = store.get_parallel("pred", "B10K1V1")
    assert view.links == "1-1S 2-2S" and view.agents == {"1-1": "rules", "2-2": "aligner"}
    assert store.alignment("pred").history[-1].sent_id == "B10K1V2"  # every pair is recorded, even without links


def test_applier_scores(store):
    store.set_links("pred", "B10K1V1", "1-1S 2-2P", confidence=0.9, agent="aligner")
    batch = TaskBatch("pred", ["B10K1V1"], review={"B10K1V1": store.alignment("pred").links("B10K1V1")})
    with pytest.raises(ModelRetry, match="not one of the links"):
        Applier(store).scores(Scores(scores="B10K1V1 3-3 0.5"), batch)
    Applier(store).scores(Scores(scores="B10K1V1 2-2 0.3"), batch)
    view = store.get_parallel("pred", "B10K1V1")
    assert view.links == "1-1S 2-2P" and view.confidence["2-2"] == 0.3 and view.agents == {"1-1": "aligner", "2-2": "scorer"}


# ------------------------------------------------------------ toolset


def test_compact_renderings(store):
    view = store.get_parallel("silver", "B10K1V1").model_dump()
    text = parallel_view(view)
    assert text.startswith("Pair B10K1V1 (silver)") and "Links: 1-1S:1.00 2-2S:1.00" in text
    assert parallel_view({**view, "links": ""}).endswith("Links: none")
    result = store.translation_candidates("رَسُول").model_dump()
    assert translations(result).startswith("رَسُول (side a): 1 occurrences, 0 unlinked. Linked to: ἀπόστολος×1.\nExamples: ")
    assert translations({**result, "candidates": [], "examples": []}).endswith("Linked to: nothing.")
    assert compact("get_parallel", {"bad": 1}) == {"bad": 1}
    assert compact("analyse_form", store.analyse_form("رسول").model_dump()).startswith("1 matches")
    assert compact("unknown_tool", [1]) == [1]


def test_read_toolset_normalise():
    assert ReadToolset.normalise({"alignments": '["a", "b"]', "x": 1}) == {"alignments": ["a", "b"], "x": 1}
    assert ReadToolset.normalise({"alignments": "silver"}) == {"alignments": ["silver"]}
    assert ReadToolset.normalise({"sources": '"ar"'}) == {"sources": ["ar"]}
    assert ReadToolset.normalise({"alignments": ["a"]}) == {"alignments": ["a"]}


@pytest.mark.anyio
async def test_read_toolset_calls(store):
    toolset = read_toolset(MCPToolset(build_server(store)))
    async with toolset:
        model = scripted(
            align(),
            tools=lambda prompt: [
                ("translation_candidates", {"lemma": "رَسُول", "alignments": '["silver"]'}),
                ("get_parallel", {"alignment": "silver", "sent_id": "B10K1V2"}),
            ],
        )
        team = AlignerTeam(store, "pred", Settings(), models={"aligner": model}, toolset=toolset)
        await team.run("aligner", "## Pair B10K1V1", TaskBatch("pred", ["B10K1V1"]))
        assert model.returns[0].startswith("رَسُول (side a)") and model.returns[1].startswith("Pair B10K1V2 (silver)")
        with pytest.raises(ModelRetry, match="not available"):
            await toolset.call_tool("set_links", {}, None, None)  # type: ignore[arg-type]


# ------------------------------------------------------------ team


@pytest.mark.anyio
async def test_team_runs_and_counts(store):
    aligner, scorer = scripted(align("1-1 S 0.9")), scripted(score(0.5))
    settings = Settings(strong_thinking="low", roles={"scorer": RoleSettings(instructions="Be strict.")})
    team = AlignerTeam(store, "pred", settings, models={"aligner": aligner, "*": scorer}, toolset=read_toolset(MCPToolset(build_server(store))))
    assert team.model_settings("aligner")["thinking"] == "low" and "thinking" not in team.model_settings("scorer")
    async with team:
        answer = await team.run("aligner", "## Pair B10K1V1", TaskBatch("pred", ["B10K1V1"]))
        assert answer.links == "B10K1V1 1-1 S 0.9"
        review = {"B10K1V1": store.alignment("pred").links("B10K1V1")}
        await team.run("scorer", "## Pair B10K1V1\nLinks to score:\n1-1S x→y", TaskBatch("pred", ["B10K1V1"], review=review))
    assert store.get_parallel("pred", "B10K1V1").confidence == {"1-1": 0.5}
    assert "Be strict." in str(team.agent("scorer")._instructions)
    assert set(team.usage) == {"function:respond:"} or len(team.usage) == 1
    total = team.total()
    assert total.tasks == 2 and total.cost is None  # scripted models have no price


def test_team_models_and_total(store):
    team = AlignerTeam(store, "pred", Settings())
    assert team.model("aligner") == "anthropic:claude-opus-5-5" and team.model("scorer") == "anthropic:claude-sonnet-5-5"
    assert AlignerTeam.model_name(FunctionModel(lambda m, i: None)).startswith("function")
    team.usage = {"a": ModelUsage(tasks=1, requests=2, cost=0.5), "b": ModelUsage(tasks=1, cost=0.25)}
    assert team.total().cost == 0.75 and team.total().requests == 2
