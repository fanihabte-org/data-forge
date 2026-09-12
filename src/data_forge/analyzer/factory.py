from dataclasses import dataclass

from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.analyzer.analyzes import AnalyzeVolume
from data_forge.context.models import Table


@dataclass
class AnalyzerFactory:
    source: SourceInterface
    target: TargetInterface

    @property
    def watermarks(self):
        with self.target.transaction() as conn:
            return self.target.fetch_watermarks(conn=conn)

    def analyze_volume(self, table: Table) -> AnalyzeVolume:
        return AnalyzeVolume(
            source=self.source,
            table=table,
            watermark=self.watermarks[table.name]
        )
