from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, fields


@dataclass
class Watermark:
    source_system: str
    table_name: str
    schema_name: str
    marking_column: str
    highest_watermark: datetime
    dw_run_timestamp: datetime

    @classmethod
    def get_columns(cls) -> list[str]:
        return list(f.name for f in fields(cls))