from __future__ import annotations

import pytest
from mcparser.corpus import NotFoundError, ReadOnlyError
from mcparser.mcp import build_server
from pydantic_ai.exceptions import UserError
from pydantic_ai.mcp import MCPToolset
from scripted import align, pairs, score, scripted

from llmaligner.agents.team import AlignerTeam
from llmaligner.agents.toolset import read_toolset
from llmaligner.pipeline import Pipeline
from llmaligner.settings import RoleSettings, Settings


def make(store, aligner, scorer=None, sent_ids=None, **fields):
    settings = Settings(**fields)
    models = {"aligner": aligner, "scorer": scorer or scripted(score(0.9))}
    team = AlignerTeam(store, "pred", settings, models=models, toolset=read_toolset(MCPToolset(build_server(store))))
    lines: list[str] = []
    return Pipeline(store, "pred", team, settings, sent_ids=sent_ids, progress=lines.append), lines


@pytest.mark.anyio
async def test_run_two_rounds(store):
    aligner = scripted(lambda prompt: align("2-2 S 0.9", "3-3 P 0.5")(prompt))
    # the scorer finds 3-3 doubtful the first time: the aligner reviews it in round 2 and drops it
    scorer = scripted(score(lambda sent_id, key: 0.4 if key == "3-3" else 0.9))
    pipeline, lines = make(store, aligner, scorer, batch_sentences=2)
    report = await pipeline.run()
    assert lines[0] == "Rules linked 4 word pairs."  # Paul, Ephesus, Jesus ×2 (names)
    first, second = report.rounds
    assert (first.aligned, first.scored, first.tasks) == (3, 3, 4)  # 2 aligner + 2 scorer tasks (batches of 2)
    assert first.low_confidence == 3 and first.changed == 3
    # 2-2 sent again unchanged keeps the scorer's rating; 3-3 changed (0.4 -> 0.5), so it is rated again
    assert second.aligned == 3 and second.scored == 3
    assert "Links to review: 3-3P 0.40 scorer" in aligner.prompts[2]
    # the scorer agreed with 0.9, so 2-2 is unchanged and still the aligner's (the pipeline remembers it was rated)
    assert "Settled links: 1-1S 0.95 rules, 2-2S 0.90 aligner, 13-13S 0.95 rules" in aligner.prompts[2]
    assert report.low_confidence == 3 and report.pairs == 3 and report.links == 10
    assert report.rules.rules["names"].links == 4 and report.total.tasks == 8
    assert [t.role for t in report.tasks] == ["aligner", "aligner", "scorer", "scorer"] * 2


@pytest.mark.anyio
async def test_run_stops_when_settled(store):
    pipeline, lines = make(store, scripted(align("2-2 S 0.9")), rounds=3, concurrency=2)
    report = await pipeline.run()
    assert len(report.rounds) == 1 and report.rounds[0].low_confidence == 0
    assert report.mean_confidence > 0.9 and lines[-1].startswith("Round 1: ")


@pytest.mark.anyio
async def test_run_stops_when_nothing_changes(store):
    pipeline, _ = make(store, scripted(lambda prompt: {"links": ""}), rounds=3, roles={"scorer": RoleSettings(enabled=False)})
    pipeline.store.set_links("pred", "B10K1V1", "2-2S", confidence=0.3, agent="person")
    report = await pipeline.run()
    assert len(report.rounds) == 1 and report.rounds[0].scored == 0
    assert report.rounds[0].changed == 1  # the aligner dropped the doubtful link
    report = await pipeline.run()
    assert report.rounds[0].aligned == 0 and report.rounds[0].tasks == 0


@pytest.mark.anyio
async def test_failed_task_is_recorded(store):
    def broken(prompt):
        raise RuntimeError("boom")

    pipeline, lines = make(store, scripted(broken), sent_ids=["B10K1V2"])
    report = await pipeline.run(rounds=1)
    assert report.tasks[0].error == "RuntimeError: boom" and "FAILED" in lines[1]
    assert report.pairs == 1


@pytest.mark.anyio
async def test_user_error_stops_the_run(store):
    def missing_key(prompt):
        raise UserError("no API key")

    pipeline, _ = make(store, scripted(missing_key))
    with pytest.raises(UserError):
        await pipeline.run()


@pytest.mark.anyio
async def test_empty_selection(store):
    pipeline, _ = make(store, scripted(align()), sent_ids=[])
    report = await pipeline.run()
    assert report.pairs == 0 and report.mean_confidence == 0.0 and report.rounds[0].tasks == 0


def test_pipeline_checks(store):
    with pytest.raises(NotFoundError):
        make(store, scripted(align()), sent_ids=["nope"])
    settings = Settings()
    with pytest.raises(ReadOnlyError):
        Pipeline(store, "silver", AlignerTeam(store, "silver", settings), settings)


def test_batches(store):
    pipeline, _ = make(store, scripted(align()), batch_sentences=5, batch_words=60)
    items = pipeline.to_align()
    assert [len(batch) for batch in pipeline.batches(items)] == [2, 1]  # verse 3 does not fit in 60 words with 1 and 2
    assert pairs("## Pair a\n## Pair b") == ["a", "b"]


@pytest.mark.anyio
async def test_round_limit(store):
    pipeline, _ = make(store, scripted(align("3-3 P 0.5")), roles={"scorer": RoleSettings(enabled=False)})
    report = await pipeline.run(rounds=1)
    assert len(report.rounds) == 1 and report.rounds[0].changed == 3 and report.low_confidence == 3
