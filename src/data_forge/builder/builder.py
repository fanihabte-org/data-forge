from pathlib import Path

from datetime import datetime
from dataclasses import dataclass, field

from data_forge.analyzer.analyzer import Analyzer
from data_forge.analyzer.factory import AnalyzerFactory
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.planner.factory import PlannerFactory
from data_forge.resolver.resolver import Resolver
from data_forge.sales_force.auth import Auth

from data_forge.context.context import Context
from data_forge.pipeline.pipeline import Pipeline

from data_forge.db_services.target import TargetDW
from data_forge.db_services.source import SourceDB
from data_forge.logging.watermark import WatermarkRepository

from data_forge.sales_force.sales_force import SalesForce
from data_forge.FileStorage.FileStorage import FileStorage
from data_forge.sales_force.sf_request import SalesForceRequest
from data_forge.planner.planner import Planner
from data_forge.validator.factory import ValidatorFactory
from data_forge.validator.validator import Validator


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

    def source_db(self, db_name: str, source: str):
        return SourceDB(
            catalog=self.context().get_catalog(source=source),
            db_engine=self.engine(db_name=db_name)
        )

    def target_dw(self, db_name: str):
        return TargetDW(
            db_engine=self.engine(db_name=db_name),
            watermark_repository=self.watermark_repository()
        )

    def pipeline(self, source_db_name: str, target_dw_name: str, source_name: str):
        return Pipeline(
            source_db=self.source_db(source=source_name, db_name=source_db_name),
            target_dw=self.target_dw(db_name=target_dw_name),
            planner=self.planner(
                source_name=source_name,
                source_db_name=source_db_name,
                target_dw_name=target_dw_name
            ),
            validator=self.validator(
                source_name=source_name,
                source_db_name=source_db_name,
                target_dw_name=target_dw_name
            ),
            resolver=self.resolver(
                source_name=source_name,
            ),
            analyzer=self.analyzer(
                source_name=source_name,
                target_dw_name=target_dw_name
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

    def watermark_repository(self):
        pipeline_config = self.context().pipeline_config
        return WatermarkRepository(
            pipeline_config=pipeline_config,
            run_datetime=self.run_datetime
        )

    def engine(self, db_name):
        return self.context().get_engine(db_name=db_name)

    def planner(self, source_name: str, source_db_name: str, target_dw_name: str):
        return Planner(
            planner_factory=self.planner_factory(
                source_name=source_name,
                source_db_name=source_db_name,
                target_dw_name=target_dw_name
            ),
            source_name=source_name
        )

    def analyzer(self, source_name: str, target_dw_name: str):
        return Analyzer(
            analyzer_factory=self.analyzer_factory(
                source_name=source_name,
                target_dw_name=target_dw_name
            )
        )

    def planner_factory(self, source_name: str, source_db_name: str, target_dw_name: str):
        return PlannerFactory(
            pipeline_config=self.context().pipeline_config,
            source_db=self.source_db(source=source_name, db_name=source_db_name),
            target_dw=self.target_dw(db_name=target_dw_name),
            watermark_repository=self.watermark_repository(),
            run_datetime=self.run_datetime,
            query_builder=self.query_builder(source_name=source_name)
        )

    def analyzer_factory(self, source_name: str, target_dw_name: str):
        return AnalyzerFactory(
            target_dw=self.target_dw(db_name=target_dw_name),
            query_builder=self.query_builder(source_name=source_name),
            watermark_repository=self.watermark_repository()
        )

    def validator(self, source_name: str, source_db_name: str, target_dw_name: str):
        return Validator(
            validator_factory=self.validator_factory(
                source_name=source_name,
                source_db_name=source_db_name,
                target_dw_name=target_dw_name
            )
        )

    def validator_factory(self, source_name: str, source_db_name: str, target_dw_name: str):
        return ValidatorFactory(
            pipeline_config=self.context().pipeline_config,
            source_db=self.source_db(source=source_name, db_name=source_db_name),
            target_dw=self.target_dw(db_name=target_dw_name),
            run_datetime=self.run_datetime,
            watermark_repository=self.watermark_repository(),
            query_builder=self.query_builder(source_name=source_name)
        )

    def resolver(self, source_name: str):
        return Resolver(
            source_name=source_name,
            query_builder=self.query_builder(source_name=source_name),
            watermark_repository=self.watermark_repository()
        )

    def query_builder(self, source_name: str):
        return QueryBuilder(
            schema_name=source_name,
            pipeline_config=self.context().pipeline_config,
            run_datetime=self.run_datetime
        )
