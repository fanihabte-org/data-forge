from __future__ import annotations

from datetime import datetime
from psycopg import Connection
from psycopg.rows import class_row
from dataclasses import dataclass, asdict
from data_forge.context.models import Table

from data_forge.databases.query_builder import QueryBuilder
from data_forge.watermark.models import Watermark
from data_forge.watermark.repository_interface import WatermarkRepositoryInterface

DEFAULT_EPOCH = datetime(1970, 1, 1, 0, 0, 0)


@dataclass
class PostgresWatermarkRepository(WatermarkRepositoryInterface):
    query_builder: QueryBuilder
    run_datetime: datetime

    def fetch_by_table(self, conn: Connection, table: Table) -> Watermark | None:
        with conn.cursor(row_factory=class_row(Watermark)) as cur:
            query = self.query_builder.select_watermark_query(
                table_name=table.name
            )
            return cur.execute(query).fetchone()

    def fetch_all(self, conn: Connection) -> dict[str, "Watermark"]:
        with conn.cursor(row_factory=class_row(Watermark)) as cur:
            query = self.query_builder.select_watermarks_query()
            watermarks: list["Watermark"] = cur.execute(query).fetchall()

            return {
                watermark.table_name: watermark
                for watermark in watermarks
            }

    def load_from_main_table(self, conn: Connection, table: Table, schema_name: str) -> "Watermark | None":
        with conn.cursor(row_factory=class_row(Watermark)) as cur:
            query = self.query_builder.summarize_watermark_query(table=table, schema_name=schema_name)
            return cur.execute(query).fetchone()

    def set_default(self, conn: Connection, table: Table, schema_name: str) -> Watermark:
        default_watermark = Watermark(
            source_system=schema_name,
            table_name=table.name,
            schema_name=schema_name,
            marking_column=table.marking_column,
            highest_watermark=DEFAULT_EPOCH,
            dw_run_timestamp=self.run_datetime
        )

        return self.upsert(
            conn=conn,
            watermark=default_watermark,
            new_highest_wm=default_watermark.highest_watermark.isoformat(),
        )

    def sync(self, conn: Connection, table: Table, schema_name: str):
        loaded_watermark = self.load_from_main_table(
            conn=conn,
            table=table,
            schema_name=schema_name
        )

        if loaded_watermark:
            return self.upsert(
                conn=conn,
                watermark=loaded_watermark,
                new_highest_wm=loaded_watermark.highest_watermark.isoformat(),
            )

        return self.set_default(
            conn=conn,
            table=table,
            schema_name=schema_name
        )

    def upsert(self, watermark: Watermark, conn: Connection, new_highest_wm: datetime | str) -> Watermark:

        if isinstance(new_highest_wm, str):
            new_wm_datetime = datetime.fromisoformat(new_highest_wm)
        else:
            new_wm_datetime = new_highest_wm

        if new_wm_datetime < watermark.highest_watermark:
            print(f"Ignored lower watermark {new_wm_datetime} (current: {watermark.highest_watermark})")
            return watermark

        watermark.highest_watermark = new_wm_datetime
        watermark.dw_run_timestamp = self.run_datetime

        columns = list(asdict(watermark).keys())
        watermark_values = tuple(asdict(watermark).values())

        with conn.cursor() as cur:
            cur.execute(self.query_builder.upsert_watermark_query(columns), watermark_values)

        return watermark
