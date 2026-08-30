from abc import ABC
from datetime import datetime
from enum import Enum

from data_forge.context.models import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark, WatermarkRepository

from dataclasses import dataclass


class ExecutionType(Enum):
    SYNC_WATERMARK = 1
    INCREMENTAL = 2
    BULK = 3
    SKIP = 4


@dataclass
class Plan(ABC):
    execution_type: ExecutionType
    run_datetime: datetime
    source_db: SourceDB
    table: Table
    watermark: Watermark
    target_dw: TargetDW
    pipeline_config: PipelineConfig
    query_builder: QueryBuilder

    def execute(self):
        ...


@dataclass
class WatermarkSyncPlan(Plan):
    watermark_repository: WatermarkRepository
    execution_type = ExecutionType.SYNC_WATERMARK

    def execute(self):
        with self.target_dw.db_engine.build_connection() as conn:
            self.watermark_repository.sync(
                conn=conn,
                table=self.table,
                schema_name=self.source_db.catalog.source_name
            )


@dataclass
class IncrementalPlan(Plan):
    execution_type = ExecutionType.INCREMENTAL

    def execute(self):
        extract_incremental_query: bytes = self.query_builder.select_all_with_metadata_after_watermark(
            format_query=True,
            watermark=self.watermark,
            table=self.table
        )
        insert_into_query: bytes = self.query_builder.insert_into(
            format_query=True,
            table=self.table
        )

        self.target_dw.insert_batches(
            batches=self.source_db.extract_after_watermark(
                sql_query=extract_incremental_query,
                pipeline_config=self.pipeline_config
            ),
            insert_into_query=insert_into_query,
            table=self.table,
            watermark=self.watermark,
            run_datetime=self.run_datetime
        )


@dataclass
class BulkPlan(Plan):
    execution_type = ExecutionType.BULK

    def execute(self):
        copy_from: bytes = self.query_builder.copy_binary_from(
            table=self.table
        )
        copy_to: bytes = self.query_builder.copy_binary_to(
            table=self.table
        )

        self.target_dw.bulk_insert_batches(
            sql_query=copy_to,
            batches=self.source_db.bulk_extract_after_watermark(
                sql_query=copy_from,
                pipeline_config=self.pipeline_config
            )
        )


@dataclass
class SkipPlan(Plan):
    execution_type = ExecutionType.SKIP

    def execute(self):
        print(f"Skipped execution {self.table.name}")
