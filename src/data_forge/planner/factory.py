from dataclasses import dataclass
from datetime import datetime

from data_forge.context.models import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import WatermarkRepository
from data_forge.planner.plans import BulkPlan, SkipPlan, IncrementalPlan, ExecutionType


@dataclass
class PlannerFactory:
    pipeline_config: PipelineConfig
    source_db: SourceDB
    target_dw: TargetDW
    run_datetime: datetime
    query_builder: QueryBuilder
    watermark_repository: WatermarkRepository

    @property
    def watermarks(self):
        with self.target_dw.db_engine.build_connection() as conn:
            return self.watermark_repository.fetch_watermarks(conn=conn)

    def build_skip_plan(self, table: Table) -> SkipPlan:
        return SkipPlan(
            run_datetime=self.run_datetime,
            source_db=self.source_db,
            table=table,
            watermark=self.watermarks[table.name],
            target_dw=self.target_dw,
            pipeline_config=self.pipeline_config,
            execution_type=ExecutionType.SKIP,
            query_builder=self.query_builder,
            watermark_repository=self.watermark_repository
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
            query_builder=self.query_builder,
            watermark_repository=self.watermark_repository
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
            query_builder=self.query_builder,
            watermark_repository=self.watermark_repository
        )
