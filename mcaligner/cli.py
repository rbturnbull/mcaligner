"""Command-line interface."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import anyio
import typer
import yaml
from mcparser.corpus import CorpusError, CorpusStore
from mcparser.mcp import AlignmentSpec, SourceSpec, load_store
from pydantic import ValidationError
from pydantic_ai.exceptions import UserError

from .evaluate import evaluate as evaluate_links
from .evaluate import format_report, read_links
from .mcp.cli import mcp_app
from .lexicon import TranslationTable, build_lexicon
from .agents.team import AlignerTeam
from .pipeline import Pipeline, RunReport
from .rules import RuleSettings, Rules, measure
from .settings import Settings, parse_thinking

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

app = typer.Typer(help="LLM agents for word alignment of parallel texts.", no_args_is_help=True)
app.add_typer(mcp_app, name="mcp", help="MCP server over the corpora and alignment sets, with alignment exploration tools.")


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


def name_list(value: str | None) -> list[str] | None:
    """``"a,b"`` -> ``["a", "b"]``; ``"none"`` or an empty string -> ``[]``; None stays None."""
    if value is None:
        return None
    return [] if value.strip() in ("", "none") else [name.strip() for name in value.split(",") if name.strip()]


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


def load_settings(path: Path | None) -> Settings:
    try:
        return Settings.from_file(path) if path else Settings()
    except (OSError, ValidationError, yaml.YAMLError) as error:
        raise fail(error) from None


def thinking_option(value: str | None) -> object:
    try:
        return parse_thinking(value) if value is not None else None
    except ValueError as error:
        raise fail(error) from None


def print_report(report: RunReport) -> None:
    typer.echo(f"Rules: {report.rules.total} links {({k: v.links for k, v in report.rules.rules.items()})}")
    for row in report.rounds:
        typer.echo(
            f"Round {row.round}: aligned {row.aligned} pairs, scored {row.scored}, {row.tasks} tasks, "
            f"{row.changed} pairs changed, {row.rule_links} rule links, {row.low_confidence} links below threshold"
        )
    failed = [task for task in report.tasks if task.error]
    if failed:
        typer.echo(f"{len(failed)} failed tasks (see the report).")
    for role in ("aligner", "scorer"):
        tasks = [task for task in report.tasks if task.role == role]
        if tasks:
            tools: dict[str, int] = {}
            for task in tasks:
                for name, count in task.details.tools.items():
                    tools[name] = tools.get(name, 0) + count
            called = ", ".join(f"{name} {count}" for name, count in sorted(tools.items())) or "none"
            retries = sum(len(task.details.retries) for task in tasks)
            typer.echo(f"{role}: {len(tasks)} tasks, {sum(task.details.requests for task in tasks)} requests, {retries} retries; tool calls: {called}")
    typer.echo(
        f"{report.pairs} pairs, {report.links} links, mean confidence {report.mean_confidence}, "
        f"{report.low_confidence} below threshold."
    )
    for name, usage in [*report.usage.items(), ("total", report.total)]:
        cost = f"${usage.cost:.4f}" if usage.cost is not None else "no price"
        typer.echo(
            f"{name}: {usage.tasks} tasks, {usage.requests} requests, {usage.input_tokens} input tokens "
            f"({usage.cache_read_tokens} cache reads, {usage.cache_write_tokens} cache writes), "
            f"{usage.output_tokens} output tokens, {cost}"
        )


@app.command()
def run(
    source: SourceOption,
    alignment: AlignmentOption,
    target: Annotated[str, typer.Option(help="Writable alignment set to fill (an --alignment name).")],
    evidence: Annotated[list[str] | None, typer.Option(help="Alignment sets used as evidence (default all). Repeatable.")] = None,
    sentence: Annotated[list[str] | None, typer.Option("--sentence", help="Only these pairs (sent_id). Repeatable.")] = None,
    max_sentences: Annotated[int | None, typer.Option(help="Only the first N pairs (after --sentence).")] = None,
    settings_path: Annotated[Path | None, typer.Option("--settings", help="YAML settings file (see `settings`).")] = None,
    rounds: Annotated[int | None, typer.Option(help="Maximum align/score rounds.")] = None,
    concurrency: Annotated[int | None, typer.Option(help="Agent tasks at the same time.")] = None,
    batch_sentences: Annotated[int | None, typer.Option(help="Sentence pairs per agent task.")] = None,
    threshold: Annotated[float | None, typer.Option(help="Links below this confidence are revisited.")] = None,
    model: Annotated[str | None, typer.Option(help="One model for every role (overrides the tiers).")] = None,
    strong_model: Annotated[str | None, typer.Option(help="Strong tier model (aligner).")] = None,
    efficient_model: Annotated[str | None, typer.Option(help="Efficient tier model (scorer).")] = None,
    light_model: Annotated[str | None, typer.Option(help="Light tier model.")] = None,
    aligner_model: Annotated[str | None, typer.Option(help="Model for the aligner (overrides its tier).")] = None,
    scorer_model: Annotated[str | None, typer.Option(help="Model for the scorer (overrides its tier).")] = None,
    strong_thinking: Annotated[str | None, typer.Option(help="Reasoning effort for the strong tier: off, on, minimal..xhigh.")] = None,
    efficient_thinking: Annotated[str | None, typer.Option(help="Reasoning effort for the efficient tier.")] = None,
    scorer: Annotated[bool | None, typer.Option("--scorer/--no-scorer", help="Run the scorer (default from settings: on).")] = None,
    guidelines: Annotated[
        str | None, typer.Option(help="Annotation guidelines for the agents: a bundled name (grc-lat, the default), a file path, or none.")
    ] = None,
    columns: Annotated[
        str | None, typer.Option(help="Columns shown for each word after id and form, e.g. lemma,upos,head,deprel,feats; none = forms only.")
    ] = None,
    tools: Annotated[
        str | None, typer.Option(help="Read tools the agents may call: all, none, or a comma-separated list.")
    ] = None,
    link_punctuation: Annotated[
        bool | None, typer.Option("--link-punctuation/--no-link-punctuation", help="Allow links to punctuation (default: dropped in code).")
    ] = None,
    report_path: Annotated[Path | None, typer.Option("--report", help="Write the run report (JSON) here.")] = None,
) -> None:
    """Align with rules, then aligner/scorer agents; prints tokens and estimated cost."""
    base = load_settings(settings_path)
    try:
        settings = base.with_overrides(
            model=model, role_models={"aligner": aligner_model, "scorer": scorer_model}, scorer=scorer,
            rounds=rounds, concurrency=concurrency, batch_sentences=batch_sentences, threshold=threshold,
            strong_model=strong_model, efficient_model=efficient_model, light_model=light_model,
            strong_thinking=thinking_option(strong_thinking), efficient_thinking=thinking_option(efficient_thinking),
            guidelines=guidelines, link_punctuation=link_punctuation,
            columns=name_list(columns), tools=None if tools in (None, "all") else name_list(tools),
        )  # fmt: skip
    except ValidationError as error:
        raise fail(error) from None
    store = open_store(source, alignment)
    try:
        aset = store.alignment(target)
        ids_b = {s.sent_id for s in aset.source_b.sentences}
        ids = list(sentence) if sentence else [s.sent_id for s in aset.source_a.sentences if s.sent_id in ids_b]
        pipeline = Pipeline(
            store, target, AlignerTeam(store, target, settings), settings, sent_ids=ids[:max_sentences],
            evidence=evidence or None, progress=typer.echo,
        )  # fmt: skip
        report = anyio.run(pipeline.run)
    except (CorpusError, UserError) as error:
        raise fail(error) from None
    print_report(report)
    with aset.path.with_name(aset.path.name + ".runs.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(report.model_dump_json() + "\n")
    if report_path is not None:
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


@app.command("settings")
def show_settings(
    settings_path: Annotated[Path | None, typer.Option("--settings", help="YAML settings file to check and show.")] = None,
) -> None:
    """Print the settings (defaults, or a file's values with defaults filled in) as YAML."""
    typer.echo(load_settings(settings_path).to_yaml(), nl=False)
