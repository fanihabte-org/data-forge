from pathlib import Path

import yaml
from pydantic import ConfigDict, BaseModel


class Column(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    type: str
    nullability: str


class Table(BaseModel):
    name: str
    marking_column: str
    primary_keys: list[str]
    columns: list[Column]

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.columns]

    @property
    def type_cast(self) -> dict:
        return {col.name: col.type for col in self.columns}

    @property
    def mc_index(self) -> int:
        return self.column_names.index(self.marking_column)


class Catalog(BaseModel):
    source_name: str
    tables: dict[str, Table]

    @classmethod
    def load_catalog(cls, source_folder: Path) -> "Catalog":
        tables_dict = {}
        for schema_file in source_folder.glob("*.yaml"):
            with schema_file.open(mode="r", encoding="utf-8") as f:
                table_schema = yaml.safe_load(f)
                tables_dict[schema_file.stem] = Table(
                    name=schema_file.stem,
                    columns=table_schema["columns"],
                    marking_column=table_schema["marking_column"],
                    primary_keys=table_schema["primary_keys"]
                )

        return cls(
            source_name=source_folder.stem,
            tables=tables_dict
        )


class SalesForceConfig(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    grant_type: str

    def get_client_id(self) -> str:
        return self.client_id

    def get_client_secret(self) -> str:
        return self.client_secret

    def get_grant_type(self) -> str:
        return self.grant_type

    def get_base_url(self) -> str:
        return self.base_url


class PipelineConfig(BaseModel):
    chunk_size: int
    export_path: str
    watermark_table_schema: str
    watermark_table_name: str

    def get_export_path(self) -> str:
        return self.export_path

    def get_chunk_size(self) -> int:
        return self.chunk_size
