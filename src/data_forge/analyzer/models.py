from dataclasses import dataclass
from typing import Optional
from data_forge.logging.watermark import Watermark

@dataclass
class WatermarkCheck:
    exists: bool
    object: Optional[Watermark]

@dataclass
class IngressVolume:
    table_name: str
    schema_name: str
    egress_volume: int

@dataclass
class LazyAnalysis:
    table_name: str
    ingress_volume: IngressVolume
    watermark_check: WatermarkCheck

