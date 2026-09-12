from dataclasses import dataclass

from data_forge.analyzer.analysis import VolumeAnalysis
from data_forge.context.models import Table, Catalog
from data_forge.planner.reporter import PlanReporter
from data_forge.planner.plans import Plan
from data_forge.planner.factory import PlannerFactory


@dataclass
class Planner:
    planner_factory: PlannerFactory
    source_name: str

    def build_catalog_plan(
            self,
            catalog: Catalog,
            volume_analyses: dict[str, VolumeAnalysis],
            report: bool = False,
    ) -> dict[str, Plan]:

        plans = {
            table_name: self.build_table_plan(
                table=table_obj,
                volume_analysis=volume_analyses[table_name],
                report=False,  # Prevent individual reports when building catalog plans
            )
            for table_name, table_obj in catalog.tables.items()
        }

        if report:
            PlanReporter.print_plans(plans=plans, pipeline_name=self.source_name)

        return plans

    def build_table_plan(
            self,
            table: Table,
            volume_analysis: VolumeAnalysis,
            report: bool = False,
    ) -> Plan:
        if volume_analysis.egress_volume == 0:
            plan = self.planner_factory.build_skip_plan(table=table)
        elif volume_analysis.egress_volume > 200_000:
            plan = self.planner_factory.build_bulk_plan(table=table)
        else:
            plan = self.planner_factory.build_incremental_plan(table=table)

        if report:
            PlanReporter.print_plan(plan=plan, pipeline_name=self.source_name)

        return plan
