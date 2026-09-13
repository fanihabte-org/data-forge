from dataclasses import dataclass

from pydantic import BaseModel

from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.watermark.models import Watermark


class VolumeAnalysis(BaseModel):
    table_name: str
    schema_name: str
    egress_volume: int

@dataclass
class AnalyzeVolume:
    source: SourceInterface

    # Check data ingress volume
    def execute(self, table: Table, watermark: Watermark) -> VolumeAnalysis:
        return self.source.analyze_table(
            table=table,
            watermark=watermark
        )