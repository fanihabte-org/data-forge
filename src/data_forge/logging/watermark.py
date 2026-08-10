from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from datetime import datetime

from psycopg import Cursor
from psycopg.rows import class_row
from psycopg.sql import SQL

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
        query = SQL(
            "insert into meta_data.watermarks "
            "(source_system, table_name, schema_name, marking_column, highest_watermark, dw_run_timestamp) "
            "values (%(source_system)s, %(table_name)s, %(schema_name)s, %(marking_column)s, %(highest_watermark)s, %(dw_run_timestamp)s) "
            "on CONFLICT (table_name) do update set "
            "highest_watermark = GREATEST(meta_data.watermarks.highest_watermark, EXCLUDED.highest_watermark)"
        )

        with (target_dw.db_engine
                      .build_connection()
                      .cursor(row_factory=class_row(Watermark)) as cur):
            cur.execute(query, asdict(self))
        return self
