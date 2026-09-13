from dataclasses import dataclass

from duckdb import connect as duckdb_connection
from psycopg import Connection

from data_forge.context.service import Catalog
from data_forge.context.models import Table

from data_forge.contracts.target_interface import TargetInterface
from data_forge.databases.postgres.postgres_base import PostgresDB
from data_forge.stroage.file_storage import FileStorage
from data_forge.watermark.models import Watermark
from data_forge.watermark.repository_interface import WatermarkRepositoryInterface


@dataclass
class TargetPostgresDB(PostgresDB, TargetInterface):
    catalog: Catalog
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
