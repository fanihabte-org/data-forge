from __future__ import annotations

from datetime import datetime
from psycopg import Connection
from psycopg.rows import class_row
from dataclasses import dataclass, asdict, fields
from data_forge.context.models import Table, PipelineConfig
from psycopg.sql import Identifier, SQL, Placeholder, Literal

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


@dataclass
class WatermarkRepository:
    pipeline_config: PipelineConfig
    run_datetime: datetime

    def fetch_watermark_for_table(self, conn: Connection, table: Table) -> Watermark | None:
        with conn.cursor(row_factory=class_row(Watermark)) as cur:
            query = self.select_watermark_query(
                pipeline_config=self.pipeline_config,
                table_name=table.name
            )
            return cur.execute(query).fetchone()

    def fetch_watermarks(self, conn: Connection) -> dict[str, "Watermark"]:
        with conn.cursor(row_factory=class_row(Watermark)) as cur:
            query = self.select_watermarks_query(self.pipeline_config)
            watermarks: list["Watermark"] = cur.execute(query).fetchall()

            return {
                watermark.table_name: watermark
                for watermark in watermarks
            }

    def load_from_main_table(self, conn: Connection, table: Table, schema_name: str) -> "Watermark | None":
        with conn.cursor() as cur:
            query = self.summarize_watermark_query(table=table, schema_name=schema_name)
            return cur.execute(query).fetchone()

    def set_default_watermark(self, conn: Connection, table: Table, schema_name: str) -> Watermark:
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

        return self.set_default_watermark(
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
            cur.execute(self.upsert_watermark_query(columns), watermark_values)

        return watermark

    def upsert_watermark_query(self, columns: list[str]) -> bytes:

        return SQL("""
                   INSERT INTO {}.{} ({})
                   VALUES ({})
                   ON CONFLICT ({})
                       DO
                   UPDATE SET
                       highest_watermark = GREATEST({}.{}.highest_watermark, EXCLUDED.highest_watermark),
                       dw_run_timestamp = GREATEST({}.{}.dw_run_timestamp, EXCLUDED.dw_run_timestamp)
                   """).format(
            Identifier(self.pipeline_config.watermark_table_schema),
            Identifier(self.pipeline_config.watermark_table_name),
            SQL(', ').join(map(Identifier, columns)),
            SQL(', ').join(self.build_placeholder(len(columns))),
            Identifier("table_name"),
            Identifier(self.pipeline_config.watermark_table_schema),
            Identifier(self.pipeline_config.watermark_table_name),
            Identifier(self.pipeline_config.watermark_table_schema),
            Identifier(self.pipeline_config.watermark_table_name)
        ).as_bytes()

    @staticmethod
    def summarize_watermark_query(table: Table, schema_name: str) -> bytes:
        return SQL("""
                   SELECT
                       {} AS source_system, {} AS table_name, {} AS schema_name, {} AS marking_column, MAX ({}) AS highest_watermark, MAX (dw_run_timestamp) AS dw_run_timestamp
                   FROM {}.{}
                   GROUP BY 1, 2, 3, 4
                   """).format(
            Literal(schema_name),
            Literal(table.name),
            Literal(schema_name),
            Literal(table.marking_column),
            Identifier(table.marking_column),
            Identifier(schema_name),
            Identifier(table.name)
        ).as_bytes()

    @staticmethod
    def select_watermarks_query(pipeline_config: PipelineConfig) -> bytes:
        return SQL("SELECT * FROM {}.{}").format(
            Identifier(pipeline_config.watermark_table_schema),
            Identifier(pipeline_config.watermark_table_name)
        ).as_bytes()

    @staticmethod
    def select_watermark_query(pipeline_config: PipelineConfig, table_name: str) -> bytes:
        return SQL("SELECT * FROM {}.{} WHERE table_name = {}").format(
            Identifier(pipeline_config.watermark_table_schema),
            Identifier(pipeline_config.watermark_table_name),
            Literal(table_name)
        ).as_bytes()

    @staticmethod
    def build_placeholder(number: int) -> list[Placeholder]:
        return [Placeholder() for _ in range(number)]
