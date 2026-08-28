from dataclasses import dataclass
from datetime import datetime

from data_forge.context.context import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark, WatermarkRepository
from data_forge.planner.models import BulkPlan, SkipPlan, IncrementalPlan, ExecutionType
from data_forge.validator.models import TableValidation


@dataclass
class PipelineStepFactory:
    pipeline_config: PipelineConfig
    source_db: SourceDB
    target_dw: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    watermark_repository: WatermarkRepository

    def build_src_table_validation(self, table: Table):
        return TableValidation(
            table=table,
            db_engine=self.source_db.db_engine,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )

    def build_target_table_validation(self, table: Table):
        return TableValidation(
            table=table,
            db_engine=self.target_dw.db_engine,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )

    def build_skip_plan(self, table: Table) -> SkipPlan:
        return SkipPlan(
            run_datetime=self.run_datetime,
            source_db=self.source_db,
            table=table,
            watermark=self.watermarks[table.name],
            target_dw=self.target_dw,
            pipeline_config=self.pipeline_config,
            execution_type=ExecutionType.SKIP,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )

        )

    def build_incremental_plan(self, table: Table) -> IncrementalPlan:
        return IncrementalPlan(
            run_datetime=self.run_datetime,
            source_db=self.source_db,
            table=table,
            watermark=self.watermarks[table.name],
            target_dw=self.target_dw,
            pipeline_config=self.pipeline_config,
            execution_type=ExecutionType.INCREMENTAL,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )

    def build_bulk_plan(self, table: Table) -> BulkPlan:
        return BulkPlan(
            run_datetime=self.run_datetime,
            source_db=self.source_db,
            table=table,
            watermark=self.watermarks[table.name],
            target_dw=self.target_dw,
            pipeline_config=self.pipeline_config,
            execution_type=ExecutionType.BULK,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )
