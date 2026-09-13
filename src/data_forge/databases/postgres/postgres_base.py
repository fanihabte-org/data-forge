from contextlib import contextmanager
from dataclasses import dataclass

from psycopg import Connection
from psycopg.rows import class_row
from psycopg_pool import ConnectionPool

from data_forge.context.models import Table, Column
from data_forge.databases.engine import DBEngine
from data_forge.databases.query_builder import QueryBuilder
from data_forge.validator.models import TableDetail, TableInfo


@dataclass
class PostgresDB:
    db_engine: DBEngine
    query_builder: QueryBuilder

    def __post_init__(self) -> None:
        self._pool = ConnectionPool(
            conninfo=self.db_engine.build_uri(),
            min_size=1,
            max_size=5,
            open=False
        )
        self.open()

    @contextmanager
    def transaction(self):
        with self._pool.connection() as conn:
            with conn.transaction():
                yield conn

    def open(self) -> None:
        self._pool.open()
        self._pool.wait(timeout=10)

    def close(self) -> None:
        self._pool.close()

    def fetch_table_detail(self, table: Table) -> TableDetail:
        with self.transaction() as conn:
            with conn.cursor(row_factory=class_row(TableInfo)) as cur:
                table_info: TableInfo | None = cur.execute(self.query_builder.select_info(table=table)).fetchone()

            with conn.cursor(row_factory=class_row(Column)) as cur:
                current_cols = cur.execute(self.query_builder.select_columns_info(table=table)).fetchall()

            if table_info is None:
                raise RuntimeError(f"Table {table.name} doesn't have table info")

            if len(current_cols) == 0:
                raise RuntimeError(f"Table {table.name} doesn't have columns")

            return TableDetail(
                table=table,
                info=table_info,
                columns=current_cols
            )
