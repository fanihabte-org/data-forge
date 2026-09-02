import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

from data_forge.context.models import Catalog, SalesForceConfig, PipelineConfig
from data_forge.db_engine.engine import DBEngine

load_dotenv()


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
            databases=cls._load_databases(folder_path / "db_secrets.yaml"),
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
    def _read_and_expand_yaml(path: Path) -> dict:
        """Reads a YAML file and expands environment variables (e.g., ${VAR_NAME})."""
        with path.open() as file:
            expanded_content = os.path.expandvars(file.read())
            return yaml.safe_load(expanded_content)

    @classmethod
    def _load_pipeline_config(cls, secrets_path: Path):
        data = cls._read_and_expand_yaml(secrets_path)
        return PipelineConfig(**data)

    @classmethod
    def _load_databases(cls, secrets_path: Path):
        data = cls._read_and_expand_yaml(secrets_path)["databases"]
        return {
            db_name: DBEngine(**db_secrets)
            for db_name, db_secrets in data.items()
        }

    @classmethod
    def _load_salesforce_config(cls, config_path: Path):
        data = cls._read_and_expand_yaml(config_path)
        return SalesForceConfig(**data)

    @classmethod
    def _load_catalogs(cls, table_schema_folder: Path):
        return {
            source_folder.stem: Catalog.load_catalog(source_folder=source_folder)
            for source_folder in filter(Path.is_dir, table_schema_folder.iterdir())
        }