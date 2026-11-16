"""Sphinx configuration for mcaligner."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

project = "mcaligner"
author = "Robert Turnbull"
copyright = "2026, Robert Turnbull"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
source_suffix = {".md": "markdown"}
exclude_patterns = ["_build"]
html_theme = "furo"
html_title = "mcaligner"
html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "mcaligner-text.svg",
    "dark_logo": "mcaligner-text-dark.svg",
    "sidebar_hide_name": True,
}
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {"members": True, "show-inheritance": True}
suppress_warnings = ["myst.xref_missing"]

CLI_COMMANDS = [
    [], ["rules"], ["run"], ["evaluate"], ["lexicon"], ["settings"], ["mcp", "serve"], ["mcp", "config"],
]  # fmt: skip


def write_cli_reference(app) -> None:
    """Render ``--help`` for every command into ``_generated/cli.md`` (typer vendors click, so sphinx-click cannot)."""
    from typer.testing import CliRunner

    from mcaligner.cli import app as cli

    runner = CliRunner()
    parts = ["# CLI reference\n", "Generated from the command-line help at build time.\n"]
    for command in CLI_COMMANDS:
        result = runner.invoke(cli, [*command, "--help"], prog_name="mcaligner", env={"COLUMNS": "100", "NO_COLOR": "1", "TERM": "dumb"})
        title = " ".join(["mcaligner", *command])
        parts.append(f"## `{title}`\n\n```text\n{result.output.strip()}\n```\n")
    target = Path(app.srcdir) / "_generated" / "cli.md"
    target.parent.mkdir(exist_ok=True)
    text = "\n".join(parts)
    if not target.exists() or target.read_text(encoding="utf-8") != text:
        target.write_text(text, encoding="utf-8")


def setup(app):
    app.connect("builder-inited", write_cli_reference)
