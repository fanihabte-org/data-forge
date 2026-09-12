from dataclasses import dataclass

from psycopg import Connection
from psycopg.rows import class_row

from data_forge.analyzer.analysis import VolumeAnalysis
from data_forge.context.context import Catalog
from data_forge.context.models import Table, Column

from data_forge.watermark.models import Watermark
from data_forge.stroage.file_storage import FileStorage
from data_forge.databases.query_builder import QueryBuilder
from data_forge.validator.models import TableInfo, TableDetail
from data_forge.contracts.source_interface import SourceInterface
from data_forge.databases.postgres.postgres_base import PostgresDB
from data_forge.watermark.repository_interface import WatermarkRepositoryInterface


@dataclass
class SourcePostgresDB(PostgresDB, SourceInterface):
    query_builder: QueryBuilder
    catalog: Catalog
    chunk_size: int
    file_storage: FileStorage
    watermark_repository: WatermarkRepositoryInterface

    def extract_after_watermark(self, conn: Connection, table: Table, watermark: Watermark):
        total_rows = 0
        sql_query = self.query_builder.select_all_with_metadata_after_watermark(
            table=table, watermark=watermark
        )

        with conn.cursor(name="stream_cursor") as cur:
            cur.execute(sql_query)
            while True:
                rows = cur.fetchmany(self.chunk_size)
                if not rows:
                    break
                yield rows
                total_rows += len(rows)

            print(f"{self.catalog.source_name}: read {total_rows} records")

    def bulk_extract_after_watermark(self, conn: Connection, table: Table, watermark: Watermark):
        sql_query = self.query_builder.copy_binary_out_after_watermark(
            table=table, watermark=watermark
        )
        with conn.cursor().copy(sql_query) as copy:
            yield copy

    def bulk_extract_to_csv_after_watermark(self, conn: Connection, table: Table, watermark: Watermark) -> None:
        ...

    def fetch_table_detail(self, conn: Connection, table: Table) -> TableDetail:
        with conn.cursor(row_factory=class_row(TableInfo)) as cur:
            table_info: TableInfo = cur.execute(self.query_builder.select_info(table=table)).fetchone()

        with conn.cursor(row_factory=class_row(Column)) as cur:
            current_cols = cur.execute(self.query_builder.select_columns_info(table=table)).fetchall()

        return TableDetail(
            table=table,
            info=table_info,
            columns=current_cols
        )

    def analyze_table(self, conn: Connection, table: Table, watermark: Watermark):
        query = self.query_builder.count_delta_after_watermark(
            table=table,
            watermark=watermark
        )

        with conn.cursor(row_factory=class_row(VolumeAnalysis)) as cur:
            data: VolumeAnalysis | None = cur.execute(query).fetchone()
            if not data:
                raise RuntimeError(f"Table {table.name} returned None for ingress volume analysis")
            return data
