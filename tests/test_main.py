import pytest
from pathlib import Path
from unittest.mock import ANY

from typer.testing import CliRunner

import llmaligner.main as main


def test_db_command_calls_build_database(tmp_path, monkeypatch):
    runner = CliRunner()
    calls = []

    def fake_build_database(yaml_path, output_path):
        calls.append((yaml_path, output_path))

    monkeypatch.setattr(main, "build_database", fake_build_database)

    input_path = Path("tests/test_data/sample.yaml")
    output_path = tmp_path / "db"

    result = runner.invoke(main.app, ["db", str(input_path), str(output_path)])

    assert result.exit_code == 0
    assert calls == [(input_path, output_path)]


def test_align_command_calls_align_items(tmp_path, monkeypatch):
    runner = CliRunner()
    calls = {"load": [], "align": []}

    def fake_load_database(path):
        calls["load"].append(Path(path))
        return f"db:{Path(path).name}"

    def fake_align_items(
        database1,
        database2,
        corpus1,
        corpus2,
        llm,
        n_examples,
        output,
        guidelines,
        ignore_existing,
    ):
        calls["align"].append(
            (
                database1,
                database2,
                corpus1,
                corpus2,
                llm,
                n_examples,
                output,
                guidelines,
                ignore_existing,
            )
        )

    monkeypatch.setattr(main, "load_database", fake_load_database)
    monkeypatch.setattr(main, "align_items", fake_align_items)

    db1 = tmp_path / "db1"
    db2 = tmp_path / "db2"
    output = tmp_path / "out.yaml"
    guidelines = Path("tests/test_data/guidelines.txt")

    result = runner.invoke(
        main.app,
        [
            "align",
            "--db1",
            str(db1),
            "--db2",
            str(db2),
            "--output",
            str(output),
            "--n-examples",
            "7",
            "--model",
            "dummy",
            "--temperature",
            "0.7",
            "--api-key",
            "key123",
            "--no-ignore-existing",
            "--guidelines",
            str(guidelines),
        ],
    )

    assert result.exit_code == 0, (
        f"stdout:\\n{result.stdout}\\n"
        f"exception: {result.exception!r}"
    )
    assert calls["load"] == [db1, db2]
    assert calls["align"] == [
        (
            "db:db1",
            "db:db2",
            "db1",
            "db2",
            ANY,
            7,
            output,
            "Be precise.\n",
            False,
        )
    ]
