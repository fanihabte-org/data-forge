from dataclasses import dataclass

from data_forge.analyzer.models import VolumeAnalysis
from data_forge.analyzer.reporter import AnalysesReporter
from data_forge.context.service import Catalog
from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.watermark.models import Watermark


@dataclass
class Analyzer:
    source: SourceInterface
    target: TargetInterface

    @property
    def watermarks(self):
        with self.target.transaction() as conn:
            return self.target.fetch_watermarks(conn=conn)

    def analyze_catalog(self, catalog: Catalog, report: bool = False) -> dict[str, VolumeAnalysis]:
        volume_analyses = {}

        for table_name, table_obj in catalog.tables.items():
            volume_analyses[table_name] = self.analyze_table_volume(
                table=table_obj,
                watermark=self.watermarks[table_name],
                source_name=catalog.source_name
            )

        if report:
            AnalysesReporter.report_analyses(
                pipeline_name=catalog.source_name,
                volume_analyses=volume_analyses
            )

        return volume_analyses

    def analyze_table_volume(self, source_name: str, table: Table, watermark: Watermark,
                             report: bool = False) -> VolumeAnalysis:

        volume_analysis = self.source.analyze_table(
            table=table,
            watermark=watermark
        )

        if report:
            AnalysesReporter.report_analysis(
                pipeline_name=source_name,
                volume_analysis=volume_analysis
            )

        return volume_analysis
