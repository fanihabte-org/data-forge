import yaml
from pathlib import Path
from data_forge.context.models import Catalog, SalesForceConfig, PipelineConfig
from dataclasses import dataclass
from data_forge.db_engine.engine import DBEngine


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
