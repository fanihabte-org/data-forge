from dataclasses import dataclass

from typing import TYPE_CHECKING

from data_forge.db_services.source import SourceDB
from data_forge.analyzer.planner.planner import Planner

if TYPE_CHECKING:
    from data_forge.pipeline.pipeline import Pipeline

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