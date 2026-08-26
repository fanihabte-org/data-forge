import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dataclasses import dataclass
from data_forge.db_engine.engine import DBEngine


class Column(BaseModel):
    name: str
    type: str
    nullability: str


class Table(BaseModel):
    name: str
    columns: list[Column]
    marking_column: Optional[str] = None

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.columns]

    @property
    def type_cast(self) -> dict:
        return {col.name: col.type for col in self.columns}


class Catalog(BaseModel):
    source_name: str
    tables: dict[str, Table]

    @classmethod
    def load_catalog(cls, source_folder: Path) -> "Catalog":
        tables_dict = {}
        for schema_file in source_folder.glob("*.yaml"):
            with schema_file.open(mode="r", encoding="utf-8") as f:
                tables_dict[schema_file.stem] = Table(
                    name=schema_file.stem,
                    columns=yaml.safe_load(f)["columns"])

        return cls(
            source_name=source_folder.stem,
            tables=tables_dict
        )


class SalesForceConfig(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    grant_type: str


class PipelineConfig(BaseModel):
    chunk_size: int
    export_path: str


@dataclass(frozen=True)
class Context:
    pipeline_config: PipelineConfig
    salesforce_config: SalesForceConfig
    catalogs: dict[str, Catalog]
    databases: dict[str, DBEngine]

    @classmethod
    def load_context(cls, folder_path: Path) -> "Context":
        return cls(
            pipeline_config=cls._load_pipeline_config(folder_path / "pipeline_config.yaml"),
            salesforce_config=cls._load_salesforce_config(folder_path / "salesforce_config.yaml"),
            catalogs=cls._load_catalogs(folder_path / "table_schemas"),
            databases=cls._load_databases(folder_path / "db_secrets.yaml")
        )

    @staticmethod
    def _load_pipeline_config(secrets_path: Path):
        with secrets_path.open() as pcf:
            return PipelineConfig(**yaml.safe_load(pcf))

    @staticmethod
    def _load_databases(secrets_path: Path):
        with secrets_path.open() as sfp:
            data = yaml.safe_load(sfp)["databases"]
            return {
                db_name: DBEngine(**db_secrets)
                for db_name, db_secrets in data.items()
            }

    @staticmethod
    def _load_salesforce_config(config_path: Path):
        with config_path.open() as cfp:
            return SalesForceConfig(**yaml.safe_load(cfp))

    @classmethod
    def _load_catalogs(cls, table_schema_folder: Path):
        return {
            source_folder.stem: Catalog.load_catalog(source_folder=source_folder)
            for source_folder in filter(Path.is_dir, table_schema_folder.iterdir())
        }

    def get_catalog(self, source: str) -> Catalog:
        return self.catalogs[source]

    def get_engine(self, source: str) -> DBEngine:
        return self.databases[source]
