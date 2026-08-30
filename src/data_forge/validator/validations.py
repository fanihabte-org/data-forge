from abc import ABC
from dataclasses import dataclass

from psycopg import Connection
from psycopg.rows import class_row

from data_forge.context.models import Table, Column
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_engine.engine import DBEngine
from data_forge.logging.watermark import Watermark, WatermarkRepository
from data_forge.validator.models import TableValidationResult, TableInfo, ColumnValidation, WatermarkValidationResult


@dataclass
class Validations(ABC):
    table: Table
    db_engine: DBEngine
    query_builder: QueryBuilder


@dataclass
class TableValidation(Validations):

    def execute(self) -> TableValidationResult:
        """Validates a single table over an existing connection."""
        with self.db_engine.build_connection() as conn:
            tables_info = self._fetch_tables_info(conn)
            table_exists = any(t.table_name == self.table.name for t in tables_info)

            if not table_exists:
                return TableValidationResult(
                    table_name=self.table.name,
                    exists=False,
                    column_validation=ColumnValidation(
                        all_exist=False,
                        missing_columns=[c.name for c in self.table.columns])
                )

            db_columns = self._fetch_table_columns(conn)
            db_col_names = {c.name for c in db_columns}
            needed_col_names = {c.name for c in self.table.columns}
            missing = list(needed_col_names - db_col_names)

            return TableValidationResult(
                table_name=self.table.name,
                exists=True,
                column_validation=ColumnValidation(
                    all_exist=len(missing) == 0,
                    missing_columns=missing,
                )
            )

    def _fetch_tables_info(self, conn: Connection) -> list[TableInfo]:
        with conn.cursor(row_factory=class_row(TableInfo)) as cur:
            return cur.execute(self.query_builder.select_info(table=self.table)).fetchall()

    def _fetch_table_columns(self, conn: Connection) -> list[Column]:
        with conn.cursor(row_factory=class_row(Column)) as cur:
            return cur.execute(self.query_builder.select_columns_info(table=self.table)).fetchall()


@dataclass
class TableWatermarkValidation(Validations):
    watermark_repository: WatermarkRepository

    def execute(self) -> WatermarkValidationResult:
        with self.db_engine.build_connection() as conn:
            return self._fetch_table_watermark(conn)

    def _fetch_table_watermark(self, conn: Connection) -> WatermarkValidationResult:
        watermark = self.watermark_repository.fetch_watermark_for_table(
            conn=conn, table=self.table
        )
        return WatermarkValidationResult(
            exist=type(watermark) == Watermark,
            watermark=watermark,
            resolved=False
        )
