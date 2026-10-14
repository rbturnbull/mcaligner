"""Command-line interface."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer
import yaml
from llmparser.cli import mcp_app
from llmparser.corpus import CorpusError, CorpusStore
from llmparser.mcp import AlignmentSpec, SourceSpec, load_store
from pydantic import ValidationError

from .convert import convert as convert_yaml
from .evaluate import evaluate as evaluate_links
from .evaluate import format_report, read_links
from .lexicon import TranslationTable, build_lexicon
from .rules import RuleSettings, Rules, measure

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

app = typer.Typer(help="LLM agents for word alignment of parallel texts.", no_args_is_help=True)
app.add_typer(mcp_app, name="mcp", help="llmparser's MCP server over the corpora and alignment sets.")


SourceOption = Annotated[
    list[str],
    typer.Option("--source", "-s", help="[NAME=]PATH[:ro|rw[:CONFIDENCE]] CoNLL-U source (default ro). Repeatable."),
]
AlignmentOption = Annotated[
    list[str],
    typer.Option(
        "--alignment",
        "-a",
        help="NAME=SOURCE_A,SOURCE_B,PATH[:ro|rw[:CONFIDENCE]] alignment set (default rw). Repeatable.",
    ),
]


def fail(error: Exception) -> typer.Exit:
    typer.echo(f"Error: {error}", err=True)
    return typer.Exit(1)


def open_store(sources: list[str], alignments: list[str]) -> CorpusStore:
    """A store with the given sources and alignment sets; bad specs or files exit with an error."""
    try:
        return load_store(
            [SourceSpec.parse(spec) for spec in sources], alignments=[AlignmentSpec.parse(spec) for spec in alignments]
        )
    except (CorpusError, OSError, ValidationError) as error:
        raise fail(error) from None


def write_data(data: object, output: Path | None) -> None:
    """Write YAML (or JSON for a .json path) to ``output``, or print YAML."""
    if output is not None and output.suffix == ".json":
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    else:
        text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    if output is None:
        typer.echo(text, nl=False)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")


@app.command()
def convert(
    input: Annotated[Path, typer.Argument(help="Old llmaligner YAML: {verse: {corpus_a: {...}, corpus_b: {...}, alignment}}.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Directory for the CoNLL-U and JSONL files.")] = Path("data"),
    name: Annotated[str | None, typer.Option(help="Alignment set name (file stem); default the input's stem.")] = None,
) -> None:
    """Split an old YAML file into one CoNLL-U file per corpus and a JSONL alignment set."""
    try:
        report = convert_yaml(input, output, name=name)
    except (CorpusError, OSError) as error:
        raise fail(error) from None
    typer.echo(f"{report.corpus_a}: {report.sentences_a} sentences -> {report.conllu_a}")
    typer.echo(f"{report.corpus_b}: {report.sentences_b} sentences -> {report.conllu_b}")
    typer.echo(f"Alignments: {report.pairs} pairs, {report.links} links -> {report.alignment}")
    if report.repaired_lines:
        typer.echo(f"Padded {report.repaired_lines} token lines that had fewer than 10 columns.")
    if report.dropped_links:
        typer.echo(f"Dropped {len(report.dropped_links)} links to missing words: {', '.join(report.dropped_links)}")
    typer.echo(
        f"Use them with: -s {report.conllu_a} -s {report.conllu_b} "
        f"-a {report.alignment.stem}={report.corpus_a},{report.corpus_b},{report.alignment}:ro"
    )


@app.command()
def evaluate(
    predicted: Annotated[Path, typer.Argument(help="Predicted alignment set (JSONL).")],
    gold: Annotated[Path, typer.Argument(help="Gold alignment set (JSONL); only its pairs are scored.")],
    annotated_only: Annotated[bool, typer.Option(help="Score only pairs with at least one predicted link.")] = False,
    min_confidence: Annotated[float, typer.Option(help="Ignore predicted links below this confidence.")] = 0.0,
    per_sentence: Annotated[bool, typer.Option(help="Print a row per sentence pair.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print the full report as JSON.")] = False,
) -> None:
    """Precision, recall and F1 over sure and over all links, and the alignment error rate (AER)."""
    try:
        report = evaluate_links(read_links(predicted, min_confidence), read_links(gold), annotated_only=annotated_only)
    except (CorpusError, OSError) as error:
        raise fail(error) from None
    typer.echo(report.model_dump_json(indent=2) if json_output else format_report(report, per_sentence))


@app.command()
def lexicon(
    source: SourceOption,
    alignment: AlignmentOption,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="YAML (or .json) file; default stdout.")] = None,
    use: Annotated[
        list[str] | None, typer.Option(help="Alignment sets to count (default all). Repeatable.")
    ] = None,
    min_confidence: Annotated[float, typer.Option(help="Only links at least this confident count.")] = 0.8,
    min_count: Annotated[int, typer.Option(help="Keep translations seen at least this often.")] = 1,
    top: Annotated[int | None, typer.Option(help="Keep at most this many translations per lemma.")] = None,
) -> None:
    """Export the bilingual lexicon: lemma -> aligned lemmas with counts and parts of speech."""
    store = open_store(source, alignment)
    try:
        table = TranslationTable(store, use or None, min_confidence=min_confidence)
    except CorpusError as error:
        raise fail(error) from None
    data = build_lexicon(table, min_count=min_count, top=top)
    write_data(data, output)
    if output is not None:
        typer.echo(", ".join(f"{name}: {len(entries)} lemmas" for name, entries in data.items()) + f" -> {output}")


@app.command()
def rules(
    source: SourceOption,
    alignment: AlignmentOption,
    target: Annotated[str | None, typer.Option(help="Writable alignment set to add the rules' links to.")] = None,
    measure_against: Annotated[
        str | None, typer.Option("--measure", help="Instead of writing, measure each rule's precision against this set.")
    ] = None,
    evidence: Annotated[
        list[str] | None, typer.Option(help="Alignment sets used as lexicon evidence (default all). Repeatable.")
    ] = None,
    min_count: Annotated[int, typer.Option(help="Linked occurrences needed by the lexicon rule.")] = 5,
    min_share: Annotated[float, typer.Option(help="Share of occurrences that must agree.")] = 0.95,
    show_errors: Annotated[bool, typer.Option(help="With --measure, list the links not in the reference set.")] = False,
) -> None:
    """Link near-certain word pairs without a model, or measure the rules' precision (--measure)."""
    if (target is None) == (measure_against is None):
        raise fail(ValueError("Give either --target (apply) or --measure (evaluate)."))
    store = open_store(source, alignment)
    try:
        settings = RuleSettings(min_count=min_count, min_share=min_share)
        engine = Rules(store, target or measure_against, settings, evidence=evidence or None)
        if measure_against is not None:
            report, outcomes = measure(engine, measure_against)
        else:
            report, outcomes = engine.apply(), []
    except (CorpusError, ValidationError) as error:
        raise fail(error) from None
    for name, count in report.rules.items():
        precision = f", {count.correct} in the reference (precision {count.precision:.3f})" if count.correct is not None else ""
        typer.echo(f"{name}: {count.links} links{precision}")
    typer.echo(f"{report.total} links over {report.sentences} sentence pairs" + (
        f" ({report.reference_links} reference links)" if report.reference_links is not None else ""
    ))
    for proposal, correct in outcomes:
        if show_errors and not correct:
            typer.echo(f"  not in reference: {proposal.sent_id} {proposal.source}-{proposal.target} {proposal.rule}: {proposal.reason}")
