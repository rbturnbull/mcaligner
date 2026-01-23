from pathlib import Path
from .database import DatabaseBase


def merge_data(database1:DatabaseBase, database2:DatabaseBase) -> dict:
    """ Merge documents from two databases into a single dict """
    data = {}
    for item in database1:
    for db in (database1, database2):
        for item in db.iter_items():
            item_id = item.get("id")
            if item_id is None:
                continue
            if item_id in data:
                # Merge fields from both databases
                data[item_id].update(item)
            else:
                data[item_id] = item
    return data

def align_items(database1:DatabaseBase, database2:DatabaseBase, llm, n_examples:int, output:Path):
    """ Parse items in input YAML file using LLM and example database, write output YAML file """


    # Merge documents from both databases
    data = merge_data(database1, database2)
