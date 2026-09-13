from dataclasses import dataclass

from psycopg.rows import class_row

from data_forge.analyzer.models import VolumeAnalysis
from data_forge.context.service import Catalog
from data_forge.context.models import Table

from data_forge.watermark.models import Watermark
from data_forge.stroage.file_storage import FileStorage
from data_forge.contracts.source_interface import SourceInterface
from data_forge.databases.postgres.postgres_base import PostgresDB
from data_forge.watermark.repository_interface import WatermarkRepositoryInterface


@dataclass
class SourcePostgresDB(PostgresDB, SourceInterface):
    catalog: Catalog
    chunk_size: int
    file_storage: FileStorage
    watermark_repository: WatermarkRepositoryInterface

    def extract_after_watermark(self, table: Table, watermark: Watermark):
        total_rows = 0
        sql_query = self.query_builder.select_all_with_metadata_after_watermark(
            table=table, watermark=watermark
        )

        with self.transaction() as conn:
            with conn.cursor(name="stream_cursor") as cur:
                cur.execute(sql_query)
                while True:
                    rows = cur.fetchmany(self.chunk_size)
                    if not rows:
                        break
                    yield rows
                    total_rows += len(rows)

            print(f"{self.catalog.source_name}: read {total_rows} records")

    def bulk_extract_after_watermark(self, table: Table, watermark: Watermark):
        sql_query = self.query_builder.copy_binary_out_after_watermark(
            table=table, watermark=watermark
        )
        with self.transaction() as conn:
            with conn.cursor().copy(sql_query) as copy:
                yield copy

    def bulk_extract_to_csv_after_watermark(self, table: Table, watermark: Watermark) -> None:
        ...

    def analyze_table(self, table: Table, watermark: Watermark):
        query = self.query_builder.count_delta_after_watermark(
            table=table,
            watermark=watermark
        )

        with self.transaction() as conn:
            with conn.cursor(row_factory=class_row(VolumeAnalysis)) as cur:
                data: VolumeAnalysis | None = cur.execute(query).fetchone()
                if not data:
                    raise RuntimeError(f"Table {table.name} returned None for ingress volume analysis")
                return data
