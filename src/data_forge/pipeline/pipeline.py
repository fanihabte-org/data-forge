from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from typing import TYPE_CHECKING

from data_forge.analyzer.validator.validator import Validator
from data_forge.analyzer.planner.planner import Planner
from data_forge.context.context import PipelineConfig

if TYPE_CHECKING:
    from data_forge.db_services.source import SourceDB
    from data_forge.db_services.target import TargetDW
    from data_forge.logging.watermark import Watermark, WatermarkRepository
    from data_forge.sales_force.sales_force import SalesForce


@dataclass
class PlannerFactory:
    pipeline: Pipeline

    def build(self, source_db: SourceDB):
        return Planner(
            source_db=source_db,
            target_dw=self.pipeline.edi,
            watermarks=self.pipeline.watermarks,
            run_datetime=self.pipeline.run_datetime,
            pipeline_config=self.pipeline.pipeline_config,
            watermark_repository=self.pipeline.watermark_repository
        )


@dataclass
class Pipeline:
    sales_force: SalesForce
    erp: SourceDB
    ops: SourceDB
    edi: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    pipeline_config: PipelineConfig
    watermark_repository: WatermarkRepository

    @property
    def planner(self):
        return PlannerFactory(pipeline=self)

    def validate(self):
        validator = Validator(
            source_db=self.ops,
            target_dw=self.edi,
            salesforce=self.sales_force
        )
        print(validator.run_checks())

    def analyze(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        analyses = planner.preflight_analysis()

        print("\n=======================================")
        print(f"{source_db.catalog.source_name.upper()} PIPELINE ANALYSIS")
        print("=======================================\n")
        for table_name, analysis in analyses.items():
            print("\nTable: ", table_name)
            print("Highest Watermark:", analysis.watermark_check.object.highest_watermark)
            print("Ingress Volume:", analysis.ingress_volume.egress_volume)

    def explain_plan(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        execution_plans = planner.build_plan()

        print("\n=======================================")
        print(f"{source_db.catalog.source_name.upper()} PIPELINE EXECUTION PLAN")
        print("=======================================\n")

        for table_name, plan in execution_plans.items():
            print("\n Table: ", table_name)
            print(" Plan type: ", plan.execution_type)

    def execute(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        execution_plans = planner.build_plan()

        print("\n=======================================")
        print(f"{source_db.catalog.source_name.upper()} PIPELINE EXECUTION")
        print("=======================================\n")

        for table_name, plan in execution_plans.items():
            print("\n Table: ", table_name)
            print(" Plan type: ", plan.execution_type)
            plan.execute()
