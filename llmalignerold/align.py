from pathlib import Path
from rich.progress import track

from .database import DatabaseBase
from .io import write_yaml, load_file
from .prompt import build_chain


def retrieve_examples(
    database1:DatabaseBase, 
    database2:DatabaseBase, 
    item:dict, 
    corpus1:str, 
    corpus2:str, 
    n_examples:int,
) -> list[str]:
    """ Retrieve example IDs from both databases based on similarity to the given item """
    query1 = item[corpus1]["text"]
    query2 = item[corpus2]["text"]

    results1 = database1(query1, k=n_examples)
    results2 = database2(query2, k=n_examples)

    example_ids = [example['id'] for example in results1[:n_examples//3]]
    example_ids += [example['id'] for example in results2[:n_examples//3] if example['id'] not in example_ids]

    # Sort by score
    remaining_examples = sorted(
        results1[n_examples//3:] + results2[n_examples//3:], 
        key=lambda x: x.get('score', 0), 
        reverse=True,
    )

    for example in remaining_examples:
        if len(example_ids) >= n_examples:
            break
        if example['id'] not in example_ids:
            example_ids.append(example['id'])

    return example_ids


def merge_data(database1:DatabaseBase, database2:DatabaseBase, corpus1:str, corpus2:str) -> dict:
    """ Merge documents from two databases into a single dict """
    data = {}
    for item1 in database1:
        item_id = item1.get("id")
        assert item_id is not None, "All items must have an 'id' field"

        item2 = database2[item_id] if item_id in database2 else None
        data[item_id] = {
            corpus1: item1,
            corpus2: item2,
        }
    
    added_items = set(data.keys())
    for item2 in database2:
        item_id = item2.get("id")
        if item_id is None or item_id in added_items:
            continue
        data[item_id] = {
            corpus1: None,
            corpus2: item2,
        }
    return data


def align_items(
    database1:DatabaseBase, 
    database2:DatabaseBase, 
    corpus1:str, 
    corpus2:str,
    llm,
    n_examples:int, 
    output:Path,
    guidelines:str|None = None,
    ignore_existing:bool = True,
) -> None:
    """ Parse items in input YAML file using LLM and example database, write output YAML file """

    # Merge documents from both databases
    data = merge_data(database1, database2, corpus1, corpus2)
    if output is not None:
        existing_data = load_file(output)
        if set(existing_data.keys()) == set(data.keys()):
            print(f"Loading existing data from {output}")
            data = existing_data

    for item_id, item in track(data.items(), total=len(data), description="Aligning parallel texts..."):
        if ignore_existing and 'alignment' in item:
            continue

        if item[corpus1] is None:
            print(f"Item {item_id} missing from corpus '{corpus1}'")
            continue
        if item[corpus2] is None:
            print(f"Item {item_id} missing from corpus '{corpus2}'")
            continue

        # Retrieve examples
        example_ids = retrieve_examples(
            database1, 
            database2, 
            item, 
            corpus1, 
            corpus2, 
            n_examples,
        )

        # Create prompt
        chain = build_chain(llm, data, item_id, example_ids, corpus1, corpus2, guidelines)

        # Call LLM to get alignment
        item['alignment'] = chain.invoke({})

        # Write output YAML file
        if output is not None:
            write_yaml(data, output)

    return data