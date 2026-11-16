from __future__ import annotations

import json
import runpy
import sys

import pytest
import yaml

from typer.testing import CliRunner

from mcaligner.cli import app

runner = CliRunner()


def test_mcp_config(files):
    result = runner.invoke(
        app,
        ["mcp", "config", "-s", f"ar={files.conllu_a}", "-s", f"grc={files.conllu_b}",
         "-a", f"silver=ar,grc,{files.alignment}:ro"],
    )  # fmt: skip
    assert result.exit_code == 0, result.output
    args = json.loads(result.output)["mcpServers"]["mcaligner"]["args"]
    assert "--alignment" in args


def test_main_module(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["mcaligner", "--help"])
    with pytest.raises(SystemExit) as exit:
        runpy.run_module("mcaligner", run_name="__main__")
    assert exit.value.code == 0 and "evaluate" in capsys.readouterr().out


def specs(files):
    return ["-s", f"ar={files.conllu_a}", "-s", f"grc={files.conllu_b}", "-a", f"silver=ar,grc,{files.alignment}:ro"]


def test_evaluate_command(files, tmp_path):
    gold = str(files.alignment)
    result = runner.invoke(app, ["evaluate", gold, gold, "--per-sentence"])
    assert result.exit_code == 0, result.output
    assert "B10K1V2" in result.output and "1.000/1.000/1.000" in result.output
    result = runner.invoke(app, ["evaluate", gold, gold, "--json", "--annotated-only", "--min-confidence", "0.5"])
    assert json.loads(result.output)["sentences"] == 3
    result = runner.invoke(app, ["evaluate", str(tmp_path / "missing.jsonl"), gold])
    assert result.exit_code == 1 and "Error:" in result.output


def test_lexicon_command(files, tmp_path):
    result = runner.invoke(app, ["lexicon", *specs(files)])
    assert result.exit_code == 0, result.output
    assert yaml.safe_load(result.output)["ar"]["رَسُول"]["alignments"]["ἀπόστολος"]["count"] == 1
    out = tmp_path / "lex" / "lexicon.json"
    result = runner.invoke(app, ["lexicon", *specs(files), "-o", str(out), "--use", "silver", "--top", "2"])
    assert result.exit_code == 0 and "ar: " in result.output
    assert "رَسُول" in json.loads(out.read_text(encoding="utf-8"))["ar"]
    out = tmp_path / "lexicon.yaml"
    runner.invoke(app, ["lexicon", *specs(files), "-o", str(out)])
    assert "رَسُول" in yaml.safe_load(out.read_text(encoding="utf-8"))["ar"]


def test_lexicon_errors(files, tmp_path):
    result = runner.invoke(app, ["lexicon", *specs(files), "--use", "nope"])
    assert result.exit_code == 1 and "No alignment named 'nope'" in result.output
    result = runner.invoke(app, ["lexicon", "-s", str(tmp_path / "missing.conllu"), "-a", "x=a,b,c.jsonl"])
    assert result.exit_code == 1 and "Error:" in result.output


def test_rules_command(files):
    result = runner.invoke(app, ["rules", *specs(files), "--measure", "silver", "--show-errors", "--min-count", "1"])
    assert result.exit_code == 0, result.output
    assert "names: " in result.output and "reference links" in result.output
    pred = files.alignment.parent / "pred.jsonl"
    args = [*specs(files), "-a", f"pred=ar,grc,{pred}", "--target", "pred", "--evidence", "silver", "--min-count", "1"]
    result = runner.invoke(app, ["rules", *args])
    assert result.exit_code == 0, result.output
    assert "over 3 sentence pairs" in result.output and "precision" not in result.output and pred.is_file()


def test_rules_errors(files):
    gold = files.alignment.parent / "gold.jsonl"
    gold.write_text('{"sent_id": "B10K1V1", "links": [{"source": "1", "target": "2"}]}\n', encoding="utf-8")
    with_gold = [*specs(files), "-a", f"gold=ar,grc,{gold}:ro"]
    result = runner.invoke(app, ["rules", *with_gold, "--measure", "gold", "--show-errors"])
    assert result.exit_code == 0 and "not in reference: B10K1V1 13-13 names" in result.output
    result = runner.invoke(app, ["rules", *specs(files)])
    assert result.exit_code == 1 and "either --target" in result.output
    result = runner.invoke(app, ["rules", *with_gold, "--target", "gold"])
    assert result.exit_code == 1 and "read-only" in result.output
    result = runner.invoke(app, ["rules", *specs(files), "--measure", "silver", "--min-share", "0.2"])
    assert result.exit_code == 1 and "Error:" in result.output


@pytest.fixture
def scripted_team(monkeypatch):
    """Make `run` use scripted models instead of real ones."""
    from scripted import align, score, scripted

    import mcaligner.cli as cli
    from mcaligner.agents.team import AlignerTeam

    models = {"aligner": scripted(align("2-2 S 0.9")), "scorer": scripted(score(0.9))}
    monkeypatch.setattr(cli, "AlignerTeam", lambda store, target, settings: AlignerTeam(store, target, settings, models=models))
    return models


def test_run_command(files, scripted_team, tmp_path):
    pred = files.alignment.parent / "pred.jsonl"
    report = tmp_path / "report.json"
    args = [*specs(files), "-a", f"pred=ar,grc,{pred}", "--target", "pred", "--max-sentences", "2",
            "--rounds", "1", "--strong-thinking", "low", "--report", str(report)]  # fmt: skip
    result = runner.invoke(app, ["run", *args])
    assert result.exit_code == 0, result.output
    assert "Rules linked" in result.output and "Round 1: aligned 2 pairs, scored 2" in result.output
    assert "total: 2 tasks" in result.output and "no price" in result.output  # one aligner, one scorer task
    assert json.loads(report.read_text(encoding="utf-8"))["pairs"] == 2
    assert len(pred.with_name("pred.jsonl.runs.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    result = runner.invoke(app, ["run", *args[:-2], "--sentence", "B10K1V3", "--no-scorer"])
    assert result.exit_code == 0 and "aligned 1 pairs, scored 0" in result.output


def test_run_reports_failures_and_prices(files, monkeypatch, tmp_path):
    import mcaligner.cli as cli
    from mcaligner.agents.team import ModelUsage
    from mcaligner.pipeline import RunReport, TaskResult
    from mcaligner.rules import RulesReport

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
    pred = files.alignment.parent / "pred.jsonl"
    result = runner.invoke(app, ["run", *specs(files), "-a", f"pred=ar,grc,{pred}", "--target", "pred"])
    assert result.exit_code == 0, result.output
    assert "1 failed tasks" in result.output and "$0.0123" in result.output


def test_run_errors(files, monkeypatch, tmp_path):
    pred = files.alignment.parent / "pred.jsonl"
    base = ["run", *specs(files), "-a", f"pred=ar,grc,{pred}"]
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

    import mcaligner.cli as cli
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


def test_mcp_config_runs_mcaligner(files):
    result = runner.invoke(app, ["mcp", "config", *specs(files)])
    assert result.exit_code == 0, result.output
    entry = json.loads(result.output)["mcpServers"]["mcaligner"]
    assert entry["args"][:4] == ["-m", "mcaligner", "mcp", "serve"]


def test_mcp_serve(files, monkeypatch):
    ran = []
    monkeypatch.setattr("mcp.server.MCPServer.run", lambda self, *args, **kwargs: ran.append((args, kwargs)))
    assert runner.invoke(app, ["mcp", "serve", *specs(files)]).exit_code == 0
    assert runner.invoke(app, ["mcp", "serve", *specs(files), "--transport", "streamable-http", "--port", "9"]).exit_code == 0
    assert ran[0][0] == ("stdio",) and ran[1][0] == ("streamable-http",) and ran[1][1]["port"] == 9
