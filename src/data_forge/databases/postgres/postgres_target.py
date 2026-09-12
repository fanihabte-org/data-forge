from dataclasses import dataclass

from duckdb import connect as duckdb_connection
from psycopg import Connection
from psycopg.rows import class_row

from data_forge.context.context import Catalog
from data_forge.context.models import Table, Column

from data_forge.contracts.target_interface import TargetInterface
from data_forge.databases.postgres.postgres_base import PostgresDB
from data_forge.stroage.file_storage import FileStorage
from data_forge.databases.query_builder import QueryBuilder
from data_forge.validator.models import TableInfo, TableDetail
from data_forge.watermark.models import Watermark
from data_forge.watermark.repository_interface import WatermarkRepositoryInterface


@dataclass
class TargetPostgresDB(PostgresDB, TargetInterface):
    query_builder: QueryBuilder
    catalog: Catalog
    chunk_size: int
    file_storage: FileStorage
    watermark_repository: WatermarkRepositoryInterface

    def bulk_insert_from_csv(self, conn: Connection, table: Table) -> None:
        with duckdb_connection() as conn:
            conn.execute("Install postgres;")
            conn.execute("Load postgres;")
            conn.execute(f"Attach '{self.db_engine.build_uri()}' as pg (TYPE postgres);")

    def bulk_insert_batches(self, conn: Connection, table: Table, batches: list[bytes]) -> None:
        total = 0
        sql_query = self.query_builder.copy_binary_in(table=table)

        with conn.cursor().copy(sql_query) as copy:
            for chunk in batches:
                copy.write(chunk)
                total += len(chunk)
                print(f"\r  {total / 1024 / 1024:,.1f} MB", end="", flush=True)
                print()

    def insert_batches(self, conn: Connection, table: Table, batches: list[tuple]) -> None:
        sql_query = self.query_builder.insert_into(table=table)
        with conn.cursor() as cur:
            for batch in batches:
                cur.executemany(sql_query, batch)

    def create_table(self, conn: Connection, table: Table):
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

    def fetch_watermark(self, conn: Connection, table: Table) -> Watermark | None:
        return self.watermark_repository.fetch_by_table(table=table, conn=conn)

    def fetch_watermarks(self, conn: Connection) -> dict[str, Watermark]:
        return self.watermark_repository.fetch_all(conn=conn)

    def set_default_watermark(self, conn: Connection, table: Table) -> Watermark:
        return self.watermark_repository.set_default(
            conn=conn, table=table, schema_name=self.catalog.source_name
        )

    def sync_watermark(self, conn: Connection, table: Table) -> Watermark:
        return self.watermark_repository.sync(
            conn=conn, table=table, schema_name=self.catalog.source_name
        )
