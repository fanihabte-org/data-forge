import yaml
from pathlib import Path
from pydantic import BaseModel
from dataclasses import dataclass
from data_forge.db_engine.engine import DBEngine


class Column(BaseModel):
    name: str
    type: str
    nullability: str


class Table(BaseModel):
    name: str
    marking_column: str
    columns: list[Column]

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
                table_schema = yaml.safe_load(f)
                tables_dict[schema_file.stem] = Table(
                    name=schema_file.stem,
                    columns=table_schema["columns"],
                    marking_column=table_schema["marking_column"]
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

    def get_catalog(self, source: str) -> Catalog:
        return self.catalogs[source]

    def get_engine(self, db_name: str) -> DBEngine:
        return self.databases[db_name]

    def get_salesforce_config(self) -> SalesForceConfig:
        return self.salesforce_config

    def get_pipeline_config(self) -> PipelineConfig:
        return self.pipeline_config

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
