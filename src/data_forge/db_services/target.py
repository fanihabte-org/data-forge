from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from psycopg import Connection

from data_forge.db_engine.db_super_class import TargetInterface
from data_forge.logging.watermark import Watermark
from data_forge.db_engine.db_sql_builder import insert_all_into, copy_from_csv
import duckdb


@dataclass
class TargetDW(TargetInterface):

    def extract_after_watermark(self, run_datetime: datetime, watermark):
        pass

    def bulk_export_all(self, run_datetime: datetime, table_name: str):
        pass

    def bulk_export_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        pass

    def bulk_insert_csv(self, table_name: str, source: str, download_dir: Path, run_datetime: datetime, columns: list):

        with duckdb.connect() as conn:
            conn.execute("Install postgres;")
            conn.execute("Load postgres;")
            conn.execute(f"Attach '{self.db_engine.build_uri()}' as pg (TYPE postgres);")
            for file in download_dir.iterdir():
                sql_query = copy_from_csv(table_name=table_name,
                                          columns=columns,
                                          source=source,
                                          run_datetime=run_datetime,
                                          file_path=file
                                          )
                print(sql_query)
                conn.execute(sql_query)

    def insert_batches(self, batches: list[tuple], table_name: str, source: str, run_datetime: datetime, watermark: Watermark, columns: list ):
        with self.db_engine.build_connection() as conn:
            print(f"EDI: built connection for: {self.db_engine.build_uri()}")

            columns += ["dw_run_timestamp"]
            sql_query = insert_all_into(
                table_name=table_name,
                columns=columns,
                source=source,
                format_query=True
            )
            print(sql_query)
            cur = conn.cursor()
            total_rows = 0
            for batch in batches:
                cur.executemany(sql_query, batch)
                self.update_watermark(conn=conn, watermark=watermark, batch=batch, columns= columns, run_datetime=run_datetime)
                total_rows += 1

                print(f"Loaded {total_rows} rows and set highest watermark to {watermark.highest_watermark}")

    @staticmethod
    def update_watermark(columns: list, watermark: Watermark, batch: tuple, run_datetime: datetime, conn: Connection):
        mc_index = columns.index(watermark.marking_column)

        batch_highest_watermark = batch[-1][mc_index].isoformat()
        watermark.upsert(conn=conn, new_watermark=batch_highest_watermark, run_datetime=run_datetime)
