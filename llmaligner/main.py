from pathlib import Path
import typer
import llmloader

from .database import load_database, build_database
from .align import align_items

app = typer.Typer()

@app.command()
def db(
    input:Path = typer.Argument(..., help="Path to input CoNNL-U/YAML file"),
    output:Path = typer.Argument(..., help="Path to output database"),
):
    """ Build database of examples from a CoNLL-U file or a YAML file with CoNLL-U parsing. """
    build_database(
        yaml_path=input,
        output_path=output,
    )


@app.command()
def align(
    db1:Path = typer.Option(..., help="Path to first database (see `db` command)"),
    db2:Path = typer.Option(..., help="Path to second database (see `db` command)"),
    guidelines:Path = typer.Option(None, help="Path to guidelines file (optional)"),
    output:Path = typer.Option(..., help="Path to output YAML file"),
    n_examples:int = typer.Option(10, help="Number of examples to include in the prompt"),
    model:str = typer.Option("claude-sonnet-4-5-20250929", help="LLM model to use"),
    temperature:float = typer.Option(0.2, help="LLM temperature"),
    api_key:str = typer.Option(None, help="API key for LLM"),
    ignore_existing:bool = typer.Option(True, help="Ignore items that already have 'align' field in the output"),
):
    """ Parse items in input YAML file using LLM and example database, write output YAML file. """
    llm = llmloader.load(model, temperature=temperature, api_key=api_key)

    # Load databases
    database1 = load_database(db1)
    database2 = load_database(db2)

    if guidelines is not None:
        guidelines = guidelines.read_text()

    align_items(
        database1, 
        database2, 
        corpus1=Path(db1).stem, 
        corpus2=Path(db2).stem,
        llm=llm, 
        n_examples=n_examples,
        output=output, 
        guidelines=guidelines, 
        ignore_existing=ignore_existing,
    )

