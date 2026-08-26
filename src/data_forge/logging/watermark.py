from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from datetime import datetime
from psycopg.rows import class_row
from psycopg.sql import SQL, Identifier
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

    @classmethod
    def load(cls, target_dw: TargetDW, wm_table_name: str, wm_table_schema: str) -> dict[str, "Watermark"]:
        sql_query = cls.build_select_query(table_name=wm_table_name, schema_name=wm_table_schema)

        with target_dw.db_engine.build_connection().cursor(row_factory=class_row(cls)) as cur:
            watermarks: list[cls] = cur.execute(sql_query).fetchall()
            return {
                watermark.table_name: watermark
                for watermark in watermarks
            }

    def upsert(self, target_dw: TargetDW, new_watermark: str, run_datetime: datetime) -> "Watermark":
        new_wm_datetime = datetime.fromisoformat(new_watermark)

        if new_wm_datetime < self.highest_watermark:
            print(f"Ignored lower watermark {new_wm_datetime} (current: {self.highest_watermark})")
            return self

        self.highest_watermark = new_wm_datetime
        self.dw_run_timestamp = run_datetime

        query = upsert_watermark(columns=self.get_columns(), table_name="watermark_logs", schema="pipeline_run",
                                 conflict_column="table_name")
        with target_dw.db_engine.build_connection() as conn:
            with conn.cursor(row_factory=class_row(Watermark)) as cur:
                cur.execute(query, tuple(asdict(self).values()))

        return self

    def get_columns(self):
        return [f.name for f in fields(self)]

    @staticmethod
    def build_select_query(table_name: str, schema_name: str):
        return SQL("select * from {}.{}").format(
            Identifier(schema_name)
            , Identifier(table_name)
        ).as_bytes()

