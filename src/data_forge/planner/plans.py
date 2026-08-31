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
    target_dw: TargetDW
    pipeline_config: PipelineConfig
    query_builder: QueryBuilder
    watermark: Watermark
    watermark_repository: WatermarkRepository

    def execute(self):
        ...


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
        with self.target_dw.db_engine.build_connection() as target_conn:
            self.target_dw.insert_batches(
                batches=self.source_db.extract_after_watermark(
                    sql_query=extract_incremental_query,
                    pipeline_config=self.pipeline_config
                ),
                sql_query=insert_into_query,
            )
            self.watermark_repository.sync(
                conn=target_conn,
                table=self.table,
                schema_name=self.source_db.catalog.source_name
            )


@dataclass
class BulkPlan(Plan):
    execution_type = ExecutionType.BULK

    def execute(self):
        copy_out = self.query_builder.copy_binary_out(table=self.table)  # source
        copy_in = self.query_builder.copy_binary_in(table=self.table)  # target

        with self.source_db.db_engine.build_connection() as source_conn, \
                self.target_dw.db_engine.build_connection() as target_conn:
            with self.source_db.bulk_extract_after_watermark(
                    conn=source_conn,
                    sql_query=copy_out,
                    pipeline_config=self.pipeline_config,
            ) as source_chunks:
                self.target_dw.bulk_insert_batches(
                    conn=target_conn,
                    sql_query=copy_in,
                    chunks=source_chunks,
                )
                self.watermark_repository.sync(
                    conn=target_conn,
                    table=self.table,
                    schema_name=self.source_db.catalog.source_name
                )


@dataclass
class SkipPlan(Plan):
    execution_type = ExecutionType.SKIP

    def execute(self):
        print(f"Skipped execution for table: {self.table.name}")
