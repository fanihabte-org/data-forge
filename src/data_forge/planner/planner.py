from dataclasses import dataclass

from data_forge.analyzer.reporter import AnalysesReporter
from data_forge.planner.reporter import ExecutionReporter
from data_forge.context.context import Catalog
from data_forge.planner.plans import Plan
from data_forge.analyzer.analyzer import Analyzer
from data_forge.planner.factory import PlannerFactory
from data_forge.validator.validator import Validator


@dataclass
class Planner:
    planner_factory: PlannerFactory
    analyzer: Analyzer
    validator: Validator
    catalog: Catalog

    def build_plan(self) -> dict[str, Plan]:
        self.validator.run_checks()
        tables_wm_validations = self.validator.run_watermark_checks()
        volume_analyses = self.analyzer.analyze_volume()

        tables = self.catalog.tables

        plans = {}

        for table_name, table_obj in tables.items():
            watermark_validation = tables_wm_validations[table_name]
            volume_analysis = volume_analyses[table_name]

            if not watermark_validation.exist:
                plans[table_name] = self.planner_factory.build_watermark_sync_plan(table=table_obj)
            elif volume_analysis.egress_volume == 0:
                plans[table_name] = self.planner_factory.build_skip_plan(table=table_obj)
            elif volume_analysis.egress_volume > 200_000:
                plans[table_name] = self.planner_factory.build_bulk_plan(table=table_obj)
            else:
                plans[table_name] = self.planner_factory.build_incremental_plan(table=table_obj)

        # 1. Report Volume Analysis Stage
        AnalysesReporter.print_report(
            pipeline_name=self.catalog.source_name,
            analyses=volume_analyses
        )

        # 2. Report Execution Plan Stage
        ExecutionReporter.print_report(
            pipeline_name=self.catalog.source_name,
            plans=plans
        )

        return plans
