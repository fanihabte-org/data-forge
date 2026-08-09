from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from data_forge.db_engine.db_super_class import DWInterface
from data_forge.util.query_builder import insert_all_into


@dataclass
class TargetDW(DWInterface):

    def extract_data(self, sql_query: bytes):
        pass

    def extract_after_watermark(self, table_name: str, run_datetime: datetime, watermark):
        pass

    def bulk_export(self, to_folder: Path):
        pass

    def bulk_export_between(self, start_time: datetime, end_time: datetime, to_folder: Path,
                            table_name: str | None = None):
        pass

    def bulk_insert(self):
        pass

    def insert_many(self, batch: list[tuple], table_name: str, source: str):
        with self.db_engine.build_connection() as conn:
            print(f"EDI: built connection for: {self.db_engine.build_uri()}")

            sql_query = insert_all_into(
                table_name=table_name,
                columns=self.context.get_columns(table_name=table_name, source=source),
                source=source,
                format_query=True
            )

            conn.cursor().executemany(sql_query, batch)

            print(f"EDI: Wrote batch successfully")

    def merge_latest_data(self):
        pass
