from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from datetime import datetime

from psycopg import Cursor
from psycopg.rows import class_row
from data_forge.db_engine.db_sql_builder import upsert_watermark

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_forge.db_services.target import TargetDW


@dataclass
class Watermark:
    source_system: str
    table_name: str
    schema_name: str
    marking_column: str
    highest_watermark: datetime
    dw_run_timestamp: datetime

    @staticmethod
    def load(target_dw: TargetDW) -> dict[str, "Watermark"]:
        sql_query = "select * from meta_data.watermarks"

        with target_dw.db_engine.build_connection().cursor(row_factory=class_row(Watermark)) as cur:
            watermarks: list[Watermark] = cur.execute(sql_query).fetchall()
            watermarks_dict = {}

            for watermark in watermarks:
                watermarks_dict[watermark.table_name] = watermark

            return watermarks_dict

    def upsert(self, target_dw: TargetDW, new_watermark: str) -> "Watermark":
        new_wm_datetime = datetime.fromisoformat(new_watermark)

        if new_wm_datetime < self.highest_watermark:
            print(f"Ignored lower watermark {new_wm_datetime} (current: {self.highest_watermark})")
            return self

        self.highest_watermark = new_wm_datetime

        query = upsert_watermark(columns=self.get_columns(), table_name="watermarks", schema="meta_data", conflict_column = "table_name")
        with target_dw.db_engine.build_connection() as conn:
            with conn.cursor(row_factory=class_row(Watermark)) as cur:
                cur.execute(query, tuple(asdict(self).values()))
        return self
    def get_columns(self):
        return [f.name for f in fields(self)]