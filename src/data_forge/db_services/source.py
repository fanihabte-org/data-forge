from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Any

from data_forge.db_engine.db_super_class import DbInterface
from data_forge.logging.watermark import Watermark
from data_forge.util.query_builder import select_all_query, select_all_after_watermark


@dataclass
class SourceDB(DbInterface):
    source: str

    def extract_data(self, sql_query: bytes):
        chunk_size = 20_000
        total_rows = 0

        print(f"{self.source}: built query: {sql_query.decode()}")

        with self.db_engine.build_connection() as conn:
            print(f"{self.source}: built connection")

            cur = conn.cursor(name="stream_cursor")
            cur.execute(sql_query)

            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break

                yield rows
                total_rows += len(rows)

            print(f"{self.source}: read {total_rows} records")

    def extract_after_watermark(self, table_name: str, run_datetime: datetime, watermark: Watermark):
        sql_query = select_all_after_watermark(
            table_name=table_name,
            highest_mark=watermark.high_watermark,
            columns=self.context.get_columns(table_name=table_name, source=self.source),
            marking_column=watermark.marking_column,
            source=self.source,
            run_datetime=run_datetime,
            format_query=True
        )
        yield from self.extract_data(sql_query=sql_query)

    def extract_full_table(self, table_name: str, run_datetime: datetime):
        sql_query = select_all_query(
            table_name=table_name,
            columns=self.context.get_columns(table_name=table_name, source=self.source),
            source=self.source,
            run_datetime=run_datetime,
            format_query=True
        )
        yield from self.extract_data(sql_query=sql_query)

    def request_data(self, table_name: str, run_datetime: datetime, watermark_response: dict):

        if watermark_response["exists"]:
            watermark_object: Watermark = watermark_response["watermark"]
            yield from self.extract_after_watermark(table_name=table_name, run_datetime=run_datetime,
                                                    watermark=watermark_object)
        else:
            yield from self.extract_full_table(table_name=table_name, run_datetime=run_datetime)

    def bulk_export(self, to_folder: Path):
        pass

    def bulk_export_between(self, start_time: datetime, end_time: datetime, to_folder: Path,
                            table_name: str | None = None):
        pass
