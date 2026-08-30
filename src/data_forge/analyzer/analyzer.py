from dataclasses import dataclass

from data_forge.analyzer.analyzes import VolumeAnalysis
from data_forge.analyzer.reporter import AnalysesReporter
from data_forge.context.context import Catalog
from data_forge.db_services.source import SourceDB
from data_forge.analyzer.factory import AnalyzerFactory
from data_forge.db_services.target import TargetDW


@dataclass
class Analyzer:
    analyzer_factory: AnalyzerFactory
    source_db: SourceDB
    target_dw: TargetDW
    catalog: Catalog

    def analyze_volume(self) -> dict[str, VolumeAnalysis]:
        tables = self.catalog.tables
        volume_analyses = {}
        with self.source_db.db_engine.build_connection() as conn:
            for table_name, table_obj in tables.items():
                volume_analyses[table_name] = self.analyzer_factory.analyze_volume(
                    table=table_obj
                ).execute(conn)

        return volume_analyses

    def explain(self) -> None:
        AnalysesReporter.print_report(
            pipeline_name=self.catalog.source_name,
            analyses=self.analyze_volume()
        )
