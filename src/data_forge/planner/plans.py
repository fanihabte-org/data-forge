from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from data_forge.context.models import Table
from data_forge.watermark.models import Watermark
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface


class ExecutionType(Enum):
    SYNC_WATERMARK = 1
    INCREMENTAL = 2
    BULK = 3
    SKIP = 4


@dataclass
class Plan(ABC):
    execution_type: ExecutionType
    source: SourceInterface
    target: TargetInterface
    table: Table
    watermark: Watermark

    @abstractmethod
    def execute(self):
        pass


@dataclass
class IncrementalPlan(Plan):
    execution_type = ExecutionType.INCREMENTAL

    def execute(self):
        with self.target.transaction() as target_conn:
            self.target.insert_batches(
                batches=self.source.extract_after_watermark(
                    table=self.table,
                    watermark=self.watermark
                ),
                table=self.table,
                conn=target_conn
            )
            self.target.sync_watermark(
                conn=target_conn, table=self.table
            )


@dataclass
class BulkPlan(Plan):
    execution_type = ExecutionType.BULK

    def execute(self):
        with self.target.transaction() as target_conn:
            with self.source.bulk_extract_after_watermark(
                table=self.table,
                watermark=self.watermark
            ) as source_chunks:
                self.target.bulk_insert_batches(
                    table=self.table,
                    batches=source_chunks,
                    conn=target_conn
                )
                self.target.sync_watermark(
                    conn=target_conn, table=self.table
                )


@dataclass
class SkipPlan(Plan):
    execution_type = ExecutionType.SKIP

    def execute(self):
        print(f"Skipped execution for table: {self.table.name}")
