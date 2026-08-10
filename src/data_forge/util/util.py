import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with open(path, "r") as j_file:
        return json.load(j_file)

def build_columns(column_names: list[str]):
    return ", ".join(column_names)

def build_column_cast(column_casts: dict):
    return ", ".join(f"{col_name}::{col_type}" for col_name, col_type in column_casts.items())