from dataclasses import dataclass

from data_forge.planner.reporter import PipelineReporter
from data_forge.context.context import Catalog
from data_forge.planner.models import Plan
from data_forge.analyzer.analyzer import Analyzer
from data_forge.planner.factory import PipelineStepFactory


@dataclass
class Planner:
    pipline_factory: PipelineStepFactory
    analyzer: Analyzer
    catalog: Catalog

    # Watermark exists — full refresh forced, or incremental?
    def build_plan(self) -> dict[str, Plan]:
        lazy_analyses = self.analyzer.preflight_analysis()
        tables = self.catalog.tables

        plans = {}

        for table_name, table_obj in tables.items():
            table_analysis = lazy_analyses[table_name]
            if table_analysis.ingress_volume.egress_volume == 0:
                plans[table_name] = self.pipline_factory.build_skip_plan(table=table_obj)
            elif table_analysis.ingress_volume.egress_volume > 200_000:
                plans[table_name] = self.pipline_factory.build_bulk_plan(table=table_obj)
            else:
                plans[table_name] = self.pipline_factory.build_incremental_plan(table=table_obj)

        # Report Execution Plan Stage
        PipelineReporter.print_analysis_report(
            pipeline_name=self.catalog.source_name,
            analyses=lazy_analyses
        )

        # Report Execution Plan Stage
        PipelineReporter.print_execution_plan(
            pipeline_name=self.catalog.source_name,
            plans=plans
        )

        return plans



