from dataclasses import dataclass
from datetime import datetime

from data_forge.context.context import Catalog
from data_forge.db_engine.db_super_class import SourceInterface
from data_forge.db_engine.engine import DBEngine
from data_forge.logging.watermark import Watermark
from data_forge.db_engine.db_sql_builder import select_all_after_watermark


@dataclass
class SourceDB(SourceInterface):
    db_engine: DBEngine
    catalog: Catalog

    def extract_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        chunk_size = 20_000
        total_rows = 0
        sql_query = select_all_after_watermark(
            table_name=watermark.table_name,
            highest_mark=watermark.highest_watermark,
            columns=self.catalog.tables[watermark.table_name].column_names,
            marking_column=watermark.marking_column,
            source=self.catalog.source_name,
            run_datetime=run_datetime,
            format_query=True
        )

        print(f"{self.catalog.source_name}: built query: {sql_query.decode()}")

        with self.db_engine.build_connection() as conn:
            print(f"{self.catalog.source_name}: built connection")

            cur = conn.cursor(name="stream_cursor")
            cur.execute(sql_query)

            while True:
                rows = cur.fetchmany(chunk_size)

                if not rows:
                    break

                yield rows
                total_rows += len(rows)

            print(f"{self.catalog.source_name}: read {total_rows} records")

    def bulk_export_all(self, run_datetime: datetime, table_name: str):
        sql_query = select_all_after_watermark(
            table_name=table_name,
            columns=self.catalog.tables[table_name].columns,
            source=self.catalog.source_name,
            run_datetime=run_datetime,
            format_query=True
        )

        yield from self.copy_from(sql_query)

    def bulk_export_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        sql_query = select_all_after_watermark(
            table_name=watermark.table_name,
            highest_mark=watermark.highest_watermark,
            columns=self.catalog.tables[watermark.table_name].column_names,
            marking_column=watermark.marking_column,
            source=self.catalog.source_name,
            run_datetime=run_datetime,
            format_query=True
        )

        yield from self.copy_from(sql_query)

    def copy_from(self, sql_query):
        with self.db_engine.build_connection() as conn:
            cur = conn.cursor()

            with cur.copy(sql_query) as copy:
                for chunk in copy:
                    yield chunk
