from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from typing import TYPE_CHECKING

from data_forge.analyzer.analyzer import Analyzer
from data_forge.validator.validator import Validator
from data_forge.planner.planner import Planner
from data_forge.context.context import PipelineConfig

if TYPE_CHECKING:
    from data_forge.db_services.source import SourceDB
    from data_forge.db_services.target import TargetDW
    from data_forge.logging.watermark import Watermark, WatermarkRepository
    from data_forge.sales_force.sales_force import SalesForce


# @dataclass
# class PlannerFactory:
#     pipeline: Pipeline
#
#     def build(self, source_db: SourceDB):
#         return Planner(
#             analyzer=Analyzer(
#                 target_dw=self.
#             )
#         )


@dataclass
class Pipeline:
    # sales_force: SalesForce
    # erp: SourceDB
    # ops: SourceDB
    # edi: TargetDW
    # watermarks: dict[str, Watermark]
    # run_datetime: datetime
    # pipeline_config: PipelineConfig
    # watermark_repository: WatermarkRepository
    planner: Planner
    analyzer: Analyzer
    validator: Validator

    @property
    def planner(self):
        return PlannerFactory(pipeline=self)

    def validate(self, source_db: SourceDB):
        validator = Validator(
            source_db=source_db,
            target_dw=self.edi,
            salesforce=self.sales_force
        )
        validator.validate_and_report()

    def analyze(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        planner.preflight_analysis()

    def explain_plan(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        planner.build_plan()

    def execute(self, source_db: SourceDB):
        planner = self.planner.build(source_db=source_db)
        execution_plans = planner.build_plan()

        for table_name, plan in execution_plans.items():
            print("\n Table: ", table_name)
            print(" Plan type: ", plan.execution_type)
            plan.execute()

    def run(self):

        for source_db in [self.ops, self.erp]:
            self.validate(source_db=source_db)
            self.analyze(source_db=source_db)
            self.explain_plan(source_db=source_db)
            self.execute(source_db=source_db)
