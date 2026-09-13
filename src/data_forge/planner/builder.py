from dataclasses import dataclass

from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface

from data_forge.planner.plans import BulkPlan, SkipPlan, IncrementalPlan, ExecutionType


@dataclass
class PlanBuilder:
    source: SourceInterface
    target: TargetInterface

    @property
    def watermarks(self):
        with self.target.transaction() as conn:
            return self.target.fetch_watermarks(conn=conn)

    def skip_plan(self, table: Table) -> SkipPlan:
        return SkipPlan(
            source=self.source,
            target=self.target,
            table=table,
            watermark=self.watermarks[table.name],
            execution_type=ExecutionType.SKIP
        )

    def incremental_plan(self, table: Table) -> IncrementalPlan:
        return IncrementalPlan(
            source=self.source,
            target=self.target,
            table=table,
            watermark=self.watermarks[table.name],
            execution_type=ExecutionType.INCREMENTAL
        )

    def bulk_plan(self, table: Table) -> BulkPlan:
        return BulkPlan(
            source=self.source,
            target=self.target,
            table=table,
            watermark=self.watermarks[table.name],
            execution_type=ExecutionType.BULK,
        )
