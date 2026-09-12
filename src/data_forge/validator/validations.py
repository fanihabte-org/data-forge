from abc import ABC
from contextlib import contextmanager
from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.watermark.models import Watermark
from data_forge.validator.models import TableValidationResult, ColumnValidation, WatermarkValidationResult


@dataclass
class Validations(ABC):
    table: Table
    interface: TargetInterface | SourceInterface


@dataclass
class TableValidation(Validations):


    def execute(self) -> TableValidationResult:
        """Validates a single table over an existing connection."""
        with self.interface.transaction() as conn:
            table_detail = self.interface.fetch_table_detail(conn=conn, table=self.table)
            table_exists = table_detail.info.table_name == self.table.name

            if not table_exists:
                return TableValidationResult(
                    table_name=self.table.name,
                    exists=False,
                    column_validation=ColumnValidation(
                        all_exist=False,
                        missing_columns=[c.name for c in self.table.columns])
                )

            db_col_names = {c.name for c in table_detail.columns}
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


@dataclass
class TableWatermarkValidation(Validations):

    def execute(self) -> WatermarkValidationResult:
        with self.interface.transaction() as conn:
            return self._fetch_table_watermark(conn)

    def _fetch_table_watermark(self, conn: Connection) -> WatermarkValidationResult:
        watermark = self.interface.fetch_watermark(
            conn=conn, table=self.table
        )
        return WatermarkValidationResult(
            exist=type(watermark) == Watermark,
            watermark=watermark,
            resolved=False
        )
