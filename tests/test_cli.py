from __future__ import annotations

import json
import runpy
import sys

import pytest
import yaml

from conftest import ARABIC, SAMPLE
from typer.testing import CliRunner

from llmaligner.cli import app

runner = CliRunner()


def test_convert_command(tmp_path):
    result = runner.invoke(app, ["convert", str(SAMPLE), "-o", str(tmp_path), "--name", "silver"])
    assert result.exit_code == 0, result.output
    assert "3 pairs" in result.output and (tmp_path / "silver.jsonl").is_file()
    assert f"-a silver={ARABIC}," in result.output


def test_convert_reports_repairs(tmp_path):
    data = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
    verse = data["B10K1V1"]
    verse[ARABIC]["conllu"] = verse[ARABIC]["conllu"].replace("\t_\t_\t_\t_\t_\t_\t_\t_\n", "\t_\t_\t_\t_\t_\t_\t_\n", 1)
    verse["alignment"] = "99-1S " + verse["alignment"]
    path = tmp_path / "in.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = runner.invoke(app, ["convert", str(path), "-o", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    assert "Padded 1 token lines" in result.output
    assert "Dropped 1 links to missing words: B10K1V1 99-1S" in result.output


def test_convert_errors(tmp_path):
    result = runner.invoke(app, ["convert", str(tmp_path / "missing.yaml")])
    assert result.exit_code == 1 and "Error:" in result.output
    path = tmp_path / "bad.yaml"
    path.write_text("v: {a: {}}\n", encoding="utf-8")
    result = runner.invoke(app, ["convert", str(path)])
    assert result.exit_code == 1 and "two corpora" in result.output


def test_mcp_config(converted):
    result = runner.invoke(
        app,
        ["mcp", "config", "-s", f"ar={converted.conllu_a}", "-s", f"grc={converted.conllu_b}",
         "-a", f"silver=ar,grc,{converted.alignment}:ro"],
    )  # fmt: skip
    assert result.exit_code == 0, result.output
    args = json.loads(result.output)["mcpServers"]["conllu"]["args"]
    assert "--alignment" in args


def test_main_module(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["llmaligner", "--help"])
    with pytest.raises(SystemExit) as exit:
        runpy.run_module("llmaligner", run_name="__main__")
    assert exit.value.code == 0 and "convert" in capsys.readouterr().out


def specs(converted):
    return ["-s", f"ar={converted.conllu_a}", "-s", f"grc={converted.conllu_b}", "-a", f"silver=ar,grc,{converted.alignment}:ro"]


def test_evaluate_command(converted, tmp_path):
    gold = str(converted.alignment)
    result = runner.invoke(app, ["evaluate", gold, gold, "--per-sentence"])
    assert result.exit_code == 0, result.output
    assert "B10K1V2" in result.output and "1.000/1.000/1.000" in result.output
    result = runner.invoke(app, ["evaluate", gold, gold, "--json", "--annotated-only", "--min-confidence", "0.5"])
    assert json.loads(result.output)["sentences"] == 3
    result = runner.invoke(app, ["evaluate", str(tmp_path / "missing.jsonl"), gold])
    assert result.exit_code == 1 and "Error:" in result.output


def test_lexicon_command(converted, tmp_path):
    result = runner.invoke(app, ["lexicon", *specs(converted)])
    assert result.exit_code == 0, result.output
    assert yaml.safe_load(result.output)["ar"]["رَسُول"]["alignments"]["ἀπόστολος"]["count"] == 1
    out = tmp_path / "lex" / "lexicon.json"
    result = runner.invoke(app, ["lexicon", *specs(converted), "-o", str(out), "--use", "silver", "--top", "2"])
    assert result.exit_code == 0 and "ar: " in result.output
    assert "رَسُول" in json.loads(out.read_text(encoding="utf-8"))["ar"]
    out = tmp_path / "lexicon.yaml"
    runner.invoke(app, ["lexicon", *specs(converted), "-o", str(out)])
    assert "رَسُول" in yaml.safe_load(out.read_text(encoding="utf-8"))["ar"]


def test_lexicon_errors(converted, tmp_path):
    result = runner.invoke(app, ["lexicon", *specs(converted), "--use", "nope"])
    assert result.exit_code == 1 and "No alignment named 'nope'" in result.output
    result = runner.invoke(app, ["lexicon", "-s", str(tmp_path / "missing.conllu"), "-a", "x=a,b,c.jsonl"])
    assert result.exit_code == 1 and "Error:" in result.output


def test_rules_command(converted):
    result = runner.invoke(app, ["rules", *specs(converted), "--measure", "silver", "--show-errors", "--min-count", "1"])
    assert result.exit_code == 0, result.output
    assert "names: " in result.output and "reference links" in result.output
    pred = converted.alignment.parent / "pred.jsonl"
    args = [*specs(converted), "-a", f"pred=ar,grc,{pred}", "--target", "pred", "--evidence", "silver", "--min-count", "1"]
    result = runner.invoke(app, ["rules", *args])
    assert result.exit_code == 0, result.output
    assert "over 3 sentence pairs" in result.output and "precision" not in result.output and pred.is_file()


def test_rules_errors(converted):
    gold = converted.alignment.parent / "gold.jsonl"
    gold.write_text('{"sent_id": "B10K1V1", "links": [{"source": "1", "target": "2"}]}\n', encoding="utf-8")
    with_gold = [*specs(converted), "-a", f"gold=ar,grc,{gold}:ro"]
    result = runner.invoke(app, ["rules", *with_gold, "--measure", "gold", "--show-errors"])
    assert result.exit_code == 0 and "not in reference: B10K1V1 13-13 names" in result.output
    result = runner.invoke(app, ["rules", *specs(converted)])
    assert result.exit_code == 1 and "either --target" in result.output
    result = runner.invoke(app, ["rules", *with_gold, "--target", "gold"])
    assert result.exit_code == 1 and "read-only" in result.output
    result = runner.invoke(app, ["rules", *specs(converted), "--measure", "silver", "--min-share", "0.2"])
    assert result.exit_code == 1 and "Error:" in result.output


@pytest.fixture
def scripted_team(monkeypatch):
    """Make `run` use scripted models instead of real ones."""
    from scripted import align, score, scripted

    import llmaligner.cli as cli
    from llmaligner.agents.team import AlignerTeam

    models = {"aligner": scripted(align("2-2 S 0.9")), "scorer": scripted(score(0.9))}
    monkeypatch.setattr(cli, "AlignerTeam", lambda store, target, settings: AlignerTeam(store, target, settings, models=models))
    return models


def test_run_command(converted, scripted_team, tmp_path):
    pred = converted.alignment.parent / "pred.jsonl"
    report = tmp_path / "report.json"
    args = [*specs(converted), "-a", f"pred=ar,grc,{pred}", "--target", "pred", "--max-sentences", "2",
            "--rounds", "1", "--strong-thinking", "low", "--report", str(report)]  # fmt: skip
    result = runner.invoke(app, ["run", *args])
    assert result.exit_code == 0, result.output
    assert "Rules linked" in result.output and "Round 1: aligned 2 pairs, scored 2" in result.output
    assert "total: 2 tasks" in result.output and "no price" in result.output  # one aligner, one scorer task
    assert json.loads(report.read_text(encoding="utf-8"))["pairs"] == 2
    assert len(pred.with_name("pred.jsonl.runs.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    result = runner.invoke(app, ["run", *args[:-2], "--sentence", "B10K1V3", "--no-scorer"])
    assert result.exit_code == 0 and "aligned 1 pairs, scored 0" in result.output


def test_run_reports_failures_and_prices(converted, monkeypatch, tmp_path):
    import llmaligner.cli as cli
    from llmaligner.agents.team import ModelUsage
    from llmaligner.pipeline import RunReport, TaskResult
    from llmaligner.rules import RulesReport

    usage = ModelUsage(tasks=1, requests=1, input_tokens=10, output_tokens=5, cost=0.0123)

    class FakePipeline:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self):
            return RunReport(
                target="pred", pairs=1, links=0, low_confidence=0, mean_confidence=0.0, rounds=[], rules=RulesReport(),
                tasks=[TaskResult(round=1, role="aligner", sent_ids=["x"], error="boom")], total=usage, usage={"m": usage},
            )  # fmt: skip

    monkeypatch.setattr(cli, "Pipeline", FakePipeline)
    pred = converted.alignment.parent / "pred.jsonl"
    result = runner.invoke(app, ["run", *specs(converted), "-a", f"pred=ar,grc,{pred}", "--target", "pred"])
    assert result.exit_code == 0, result.output
    assert "1 failed tasks" in result.output and "$0.0123" in result.output


def test_run_errors(converted, monkeypatch, tmp_path):
    pred = converted.alignment.parent / "pred.jsonl"
    base = ["run", *specs(converted), "-a", f"pred=ar,grc,{pred}"]
    result = runner.invoke(app, [*base, "--target", "nope"])
    assert result.exit_code == 1 and "No alignment named 'nope'" in result.output
    result = runner.invoke(app, [*base, "--target", "pred", "--strong-thinking", "lots"])
    assert result.exit_code == 1 and "Thinking must be" in result.output
    result = runner.invoke(app, [*base, "--target", "pred", "--threshold", "2"])
    assert result.exit_code == 1 and "Error:" in result.output
    bad = tmp_path / "bad.yaml"
    bad.write_text("rounds: zero\n", encoding="utf-8")
    result = runner.invoke(app, [*base, "--target", "pred", "--settings", str(bad)])
    assert result.exit_code == 1 and "Error:" in result.output

    import llmaligner.cli as cli
    from pydantic_ai.exceptions import UserError

    class NoKey:
        def __init__(self, *args, **kwargs):
            pass

        async def run(self):
            raise UserError("Set ANTHROPIC_API_KEY")

    monkeypatch.setattr(cli, "Pipeline", NoKey)
    result = runner.invoke(app, [*base, "--target", "pred"])
    assert result.exit_code == 1 and "ANTHROPIC_API_KEY" in result.output


def test_settings_command(tmp_path):
    result = runner.invoke(app, ["settings"])
    assert result.exit_code == 0 and "strong_model: anthropic:claude-opus-5-5" in result.output
    path = tmp_path / "s.yaml"
    path.write_text("rounds: 5\n", encoding="utf-8")
    assert "rounds: 5" in runner.invoke(app, ["settings", "--settings", str(path)]).output
    assert runner.invoke(app, ["settings", "--settings", str(tmp_path / "missing.yaml")]).exit_code == 1
