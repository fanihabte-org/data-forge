from abc import ABC
from datetime import datetime
from enum import Enum

from data_forge.context.context import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark

from dataclasses import dataclass


class ExecutionType(Enum):
    INCREMENTAL = 1
    BULK = 2
    SKIP = 3


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
class IncrementalPlan(Plan):

    def execute(self):
        extract_incremental_query: bytes = self.query_builder.extract_incremental(format_query=True)
        insert_into_query: bytes = self.query_builder.insert(format_query=True)

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

    def execute(self):
        copy_from: bytes = self.query_builder.copy_binary_from()
        copy_to: bytes = self.query_builder.copy_binary_to()

        self.target_dw.bulk_insert_batches(
            sql_query=copy_to,
            batches=self.source_db.bulk_extract_after_watermark(
                sql_query=copy_from,
                pipeline_config=self.pipeline_config
            )
        )


@dataclass
class SkipPlan(Plan):

    def execute(self):
        print(f"Skipped execution {self.table.name}")
