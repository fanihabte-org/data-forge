from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from datetime import datetime

from psycopg import Connection
from psycopg.rows import class_row
from data_forge.db_engine.db_sql_builder import upsert_watermark, select_watermark_details, build_select_query_dwt

from data_forge.db_engine.engine import DBEngine

DEFAULT_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


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

    @classmethod
    def fetch_watermarks(cls, db_engine: DBEngine, wm_table_name: str, wm_table_schema: str) -> dict[str, "Watermark"]:
        sql_query = build_select_query_dwt(table_name=wm_table_name, schema_name=wm_table_schema)

        with db_engine.build_connection() as conn:
            with conn.cursor(row_factory=class_row(cls)) as cur:
                watermarks: list[cls] = cur.execute(sql_query).fetchall()
                return {
                    watermark.table_name: watermark
                    for watermark in watermarks
                }

    @classmethod
    def load_from_main_table(cls, conn: Connection, table_name: str, schema: str,
                             marking_column: str) -> "Watermark | None":
        sql_query = select_watermark_details(
            table_name=table_name,
            schema=schema,
            marking_column=marking_column
        )

        with conn.cursor(row_factory=class_row(cls)) as cur:
            return cur.execute(sql_query).fetchone()

    @classmethod
    def sync(cls, conn: Connection, table_name: str, source_name: str, marking_column: str, run_datetime: datetime):
        loaded_watermark = cls.load_from_main_table(
            conn=conn,
            table_name=table_name,
            schema=source_name,
            marking_column=marking_column
        )

        if loaded_watermark:
            return loaded_watermark.upsert(
                conn=conn,
                new_watermark=loaded_watermark.highest_watermark.isoformat(),
                run_datetime=run_datetime
            )

        return cls.set_default_watermark(
            conn=conn,
            source=source_name,
            table_name=table_name,
            marking_column=marking_column,
            run_datetime=run_datetime
        )

    def upsert(self, conn: Connection, new_watermark: datetime | str, run_datetime: datetime) -> "Watermark":
        if isinstance(new_watermark, str):
            new_wm_datetime = datetime.fromisoformat(new_watermark)
        else:
            new_wm_datetime = new_watermark

        if new_wm_datetime < self.highest_watermark:
            print(f"Ignored lower watermark {new_wm_datetime} (current: {self.highest_watermark})")
            return self

        self.highest_watermark = new_wm_datetime
        self.dw_run_timestamp = run_datetime

        query = upsert_watermark(
            columns=self.get_columns(),
            table_name="watermark_logs",
            schema="pipeline_run",
            conflict_column="table_name"
        )

        with conn.cursor() as cur:
            cur.execute(query, tuple(asdict(self).values()))

        return self

    @staticmethod
    def set_default_watermark(conn: Connection, source: str,
                              table_name: str, marking_column: str,
                              run_datetime: datetime):
        default_watermark = Watermark(
            source_system=source,
            table_name=table_name,
            schema_name=source,
            marking_column=marking_column,
            highest_watermark=DEFAULT_EPOCH,
            dw_run_timestamp=run_datetime
        )

        return default_watermark.upsert(
            conn=conn,
            new_watermark=default_watermark.highest_watermark.isoformat(),
            run_datetime=run_datetime
        )
