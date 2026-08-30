from dataclasses import dataclass
from datetime import datetime

from data_forge.analyzer.models import AnalyzeVolume
from data_forge.context.context import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder

from data_forge.logging.watermark import Watermark, WatermarkRepository


@dataclass
class AnalyzerFactory:
    pipeline_config: PipelineConfig
    source_name: str
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    watermark_repository: WatermarkRepository

    def analyze_volume(self, table: Table) -> AnalyzeVolume:
        return AnalyzeVolume(
            table=table,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )
