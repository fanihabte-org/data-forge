from dataclasses import dataclass

from data_forge.analyzer.analyzes import AnalyzeVolume
from data_forge.context.models import Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import WatermarkRepository


@dataclass
class AnalyzerFactory:
    target_dw: TargetDW
    query_builder: QueryBuilder
    watermark_repository: WatermarkRepository

    @property
    def watermarks(self):
        with self.target_dw.db_engine.build_connection() as conn:
            return self.watermark_repository.fetch_watermarks(conn=conn)

    def analyze_volume(self, table: Table) -> AnalyzeVolume:
        return AnalyzeVolume(
            table=table,
            query_builder=self.query_builder,
            watermark=self.watermarks[table.name]
        )
