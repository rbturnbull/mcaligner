"""``mcaligner mcp serve|config``: MCParser's options, with the alignment tools added."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from mcparser.cli import (
    AlignmentOption,
    CorpusOption,
    RootKeyOption,
    SourceOption,
    Transport,
    _alignments,
    _corpora,
    _load,
    _specs,
)
from mcparser.mcp import claude_desktop_config

from .server import build_server

mcp_app = typer.Typer(help="The alignment MCP server: MCParser's tools plus alignment exploration.", no_args_is_help=True)

NameOption = Annotated[str, typer.Option(help="Server name shown to MCP clients.")]
ReadOnlyOption = Annotated[bool, typer.Option("--read-only", help="Register only the read-only tools.")]


@mcp_app.command("serve")
def serve(
    source: SourceOption,
    transport: Annotated[Transport, typer.Option(help="MCP transport.")] = Transport.STDIO,
    host: Annotated[str, typer.Option(help="Host for streamable-http.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port for streamable-http.")] = 8000,
    read_only: ReadOnlyOption = False,
    root_key: RootKeyOption = "Root",
    name: NameOption = "mcaligner",
    alignment: AlignmentOption = None,
    corpus: CorpusOption = None,
) -> None:
    """Serve sources and alignment sets over MCP (stdio for Claude Desktop, or streamable HTTP)."""
    store = _load(_specs(source), root_key, _alignments(alignment), _corpora(corpus))
    server = build_server(store, name=name, allow_edits=not read_only)
    if transport is Transport.STDIO:
        server.run("stdio")
    else:
        server.run("streamable-http", host=host, port=port)


@mcp_app.command("config")
def config(
    source: SourceOption,
    read_only: ReadOnlyOption = False,
    root_key: RootKeyOption = "Root",
    name: NameOption = "mcaligner",
    alignment: AlignmentOption = None,
    corpus: CorpusOption = None,
) -> None:
    """Print the JSON to add to Claude Desktop's claude_desktop_config.json."""
    entry = claude_desktop_config(
        _specs(source), name=name, read_only=read_only, root_key=root_key,
        alignments=_alignments(alignment), corpora=_corpora(corpus),
    )  # fmt: skip
    for server in entry["mcpServers"].values():
        server["args"][1] = "mcaligner"
    typer.echo(json.dumps(entry, indent=2))
