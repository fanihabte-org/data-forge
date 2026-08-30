from dataclasses import dataclass


@dataclass
class VolumeAnalysis:
    table_name: str
    schema_name: str
    egress_volume: int
