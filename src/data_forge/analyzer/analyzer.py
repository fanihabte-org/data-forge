from dataclasses import dataclass

from psycopg import Connection

from data_forge.analyzer.analyzes import VolumeAnalysis
from data_forge.analyzer.reporter import AnalysesReporter
from data_forge.context.context import Catalog
from data_forge.context.models import Table
from data_forge.analyzer.factory import AnalyzerFactory


@dataclass
class Analyzer:
    analyzer_factory: AnalyzerFactory

    def analyze_catalog(self, conn: Connection, catalog: Catalog, report: bool = False) -> dict[str, VolumeAnalysis]:
        volume_analyses = {}

        for table_name, table_obj in catalog.tables.items():
            volume_analyses[table_name] = self.analyzer_factory.analyze_volume(
                table=table_obj
            ).execute(conn)

        if report:
            AnalysesReporter.report_analyses(
                pipeline_name=catalog.source_name,
                volume_analyses=volume_analyses
            )

        return volume_analyses

    def analyze_table(self, source_name: str, conn: Connection, table: Table, report: bool = False) -> VolumeAnalysis:
        volume_analysis = self.analyzer_factory.analyze_volume(table=table).execute(conn)

        if report:
            AnalysesReporter.report_analysis(
                pipeline_name=source_name,
                volume_analysis=volume_analysis
            )

        return volume_analysis
