from abc import ABC
from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.watermark.models import Watermark
from data_forge.analyzer.analysis import VolumeAnalysis

from data_forge.contracts.source_interface import SourceInterface


@dataclass
class Analyze(ABC):
    source: SourceInterface
    table: Table
    watermark: Watermark


@dataclass
class AnalyzeVolume(Analyze):

    # Check data ingress volume
    def execute(self, conn: Connection) -> VolumeAnalysis:
        return self.source.analyze_table(
            conn=conn,
            table=self.table,
            watermark=self.watermark
        )
