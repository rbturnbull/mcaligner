from pathlib import Path
from .database import DatabaseBase
from .io import write_yaml

def merge_data(database1:DatabaseBase, database2:DatabaseBase, corpus1:str, corpus2:str) -> dict:
    """ Merge documents from two databases into a single dict """
    data = {}
    for item1 in database1:
        item_id = item1.get("id")
        assert item_id is not None, "All items must have an 'id' field"
        item2 = database2.get(item_id, None)
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

    for item_id, item in data.items():
        if ignore_existing and 'alignment' in item:
            print(f"Skipping existing alignment for item {item_id}")
            continue

        if item[corpus1] is None:
            print(f"Item {item_id} missing from corpus {corpus1}")
            continue
        if item[corpus2] is None:
            print(f"Item {item_id} missing from corpus {corpus2}")
            continue

        # Retrieve examples
        examples = retrieve_examples(
            database1, 
            database2, 
            item, 
            corpus1, 
            corpus2, 
            n_examples,
        )

        # Create prompt
        chain = build_chain(item, examples)

        # Call LLM to get alignment
        item['align'] = chain.invoke({})

        # Write output YAML file
        if output is not None:
            write_yaml(data, output)

    return data