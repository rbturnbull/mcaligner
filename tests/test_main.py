from pathlib import Path

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
