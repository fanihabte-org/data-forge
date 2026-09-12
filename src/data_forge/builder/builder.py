from pathlib import Path

from datetime import datetime
from dataclasses import dataclass, field

from data_forge.analyzer.analyzer import Analyzer
from data_forge.analyzer.factory import AnalyzerFactory
from data_forge.databases.postgres.postgres_target import TargetPostgresDB
from data_forge.databases.query_builder import QueryBuilder
from data_forge.planner.factory import PlannerFactory
from data_forge.resolver.resolver import Resolver
from data_forge.salesforce.auth import Auth

from data_forge.context.context import Context
from data_forge.pipeline.pipeline import Pipeline

from data_forge.databases.postgres.postgres_source import SourcePostgresDB
from data_forge.watermark.pg_wm_repository import PostgresWatermarkRepository

from data_forge.salesforce.salesforce import SalesForce
from data_forge.stroage.file_storage import FileStorage
from data_forge.salesforce.request import SalesForceRequest
from data_forge.planner.service import Planner
from data_forge.validator.factory import ValidatorFactory
from data_forge.validator.service import Validator


@dataclass
class Builder:
    config_folder_path: Path
    run_datetime: datetime = field(default_factory=datetime.now)

    def context(self):
        return Context.load_context(folder_path=self.config_folder_path)

    def auth(self):
        salesforce_config = self.context().salesforce_config
        return Auth(
            client_id=salesforce_config.get_client_id(),
            client_secret=salesforce_config.get_client_secret(),
            grant_type=salesforce_config.get_grant_type(),
            base_url=salesforce_config.get_base_url()
        )

    def target_postgres_db(self, source_name: str, target_db_name: str):
        return TargetPostgresDB(
            db_engine=self.engine(db_name=target_db_name),
            query_builder=self.query_builder(source_name=source_name),
            catalog=self.context().get_catalog(source=source_name),
            chunk_size=self.context().pipeline_config.chunk_size,
            file_storage=self.file_storage(),
            watermark_repository=self.watermark_repository(source_name=source_name)
        )

    def source_postgres_db(self, source_name: str, source_db_name: str):
        return SourcePostgresDB(
            db_engine=self.engine(db_name=source_db_name),
            query_builder=self.query_builder(source_name=source_name),
            catalog=self.context().get_catalog(source=source_name),
            chunk_size=self.context().pipeline_config.chunk_size,
            file_storage=self.file_storage(),
            watermark_repository=self.watermark_repository(source_name=source_name)
        )

    def pipeline(self, source_db_name: str, target_db_name: str, source_name: str):
        return Pipeline(
            source=self.source_postgres_db(source_name=source_name, source_db_name=source_db_name),
            target=self.target_postgres_db(source_name=source_name, target_db_name=target_db_name),
            catalog=self.context().get_catalog(source=source_name),
            planner=self.planner(
                source_name=source_name,
                source_db_name=source_db_name,
                target_db_name=target_db_name
            ),
            validator=self.validator(
                source_name=source_name,
                source_db_name=source_db_name,
                target_db_name=target_db_name
            ),
            resolver=self.resolver(
                source_name=source_name,
                target_db_name=target_db_name
            ),
            analyzer=self.analyzer(
                source_name=source_name,
                target_db_name=target_db_name,
                source_db_name=source_db_name
            )
        )

    def salesforce(self):
        return SalesForce(
            catalog=self.context().get_catalog(source="crm"),
            file_storage=self.file_storage(),
            sf_request=self.sales_force_request()
        )

    def file_storage(self):
        pipeline_config = self.context().pipeline_config
        return FileStorage(
            export_path=pipeline_config.get_export_path(),
            chunk_size=pipeline_config.get_chunk_size()
        )

    def sales_force_request(self):
        return SalesForceRequest(
            auth=self.auth()
        )

    def watermark_repository(self, source_name: str):
        return PostgresWatermarkRepository(
            query_builder=self.query_builder(source_name=source_name),
            run_datetime=self.run_datetime
        )

    def engine(self, db_name):
        return self.context().get_engine(db_name=db_name)

    def planner(self, source_name: str, source_db_name: str, target_db_name: str):
        return Planner(
            source_name=source_name,
            planner_factory=self.planner_factory(
                source_name=source_name,
                source_db_name=source_db_name,
                target_db_name=target_db_name
            )
        )

    def analyzer(self, source_name: str, source_db_name: str, target_db_name: str):
        return Analyzer(
            analyzer_factory=self.analyzer_factory(
                source_name=source_name,
                target_db_name=target_db_name,
                source_db_name=source_db_name
            )
        )

    def planner_factory(self, source_name: str, source_db_name: str, target_db_name: str):
        return PlannerFactory(
            source=self.source_postgres_db(source_name=source_name, source_db_name=source_db_name),
            target=self.target_postgres_db(source_name=source_name, target_db_name=target_db_name),
        )

    def analyzer_factory(self, source_name: str, source_db_name: str, target_db_name: str):
        return AnalyzerFactory(
            source=self.source_postgres_db(source_name=source_name, source_db_name=source_db_name),
            target=self.target_postgres_db(source_name=source_name, target_db_name=target_db_name),
        )

    def validator(self, source_name: str, source_db_name: str, target_db_name: str):
        return Validator(
            validator_factory=self.validator_factory(
                source_name=source_name,
                source_db_name=source_db_name,
                target_db_name=target_db_name
            )
        )

    def validator_factory(self, source_name: str, source_db_name: str, target_db_name: str):
        return ValidatorFactory(
            source=self.source_postgres_db(source_name=source_name, source_db_name=source_db_name),
            target=self.target_postgres_db(source_name=source_name, target_db_name=target_db_name),
        )

    def resolver(self, source_name: str, target_db_name: str):
        return Resolver(
            source_name=source_name,
            target=self.target_postgres_db(source_name=source_name, target_db_name=target_db_name)
        )

    def query_builder(self, source_name: str):
        return QueryBuilder(
            schema_name=source_name,
            pipeline_config=self.context().pipeline_config,
            run_datetime=self.run_datetime
        )
