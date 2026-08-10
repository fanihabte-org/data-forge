import json

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Context:
    base_url: str
    chunk_size: int
    client_id: str
    client_secret: str
    export_path: str
    grant_type: str
    marking_column: dict
    tables: dict
    databases: dict

    @classmethod
    def load_context_from(cls, file_path: Path) -> "Context":
        manifest = _read_resource_file(file_path=file_path)
        return cls(**manifest)

    def get_columns(self, table_name: str, source: str) -> list[str]:
        columns_details = self.tables[source][table_name]
        column_names = []

        for column in columns_details:
            column_names.append(column["name"])

        return column_names

    def get_tables(self, source: str) -> list[str]:
        return list(self.tables[source].keys())

    def get_marking_column(self, source: str, table_name: str) -> str:
        return self.marking_column[source][table_name]

    def get_column_cast(self, table: str, source) -> dict:
        columns = self.tables[source][table]
        column_cast = {}
        for column in columns:
            column_cast[column["name"]] = column["type"]

        return column_cast


def _read_resource_file(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} is not invalid file path.")

    with open(file_path, 'r') as file:
        config_data = json.load(file)

    return config_data
