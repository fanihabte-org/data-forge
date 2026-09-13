from dataclasses import dataclass

from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.watermark.models import Watermark
from data_forge.validator.models import TableValidationResult, ColumnValidation, WatermarkValidationResult, TableDetail


@dataclass
class TableValidation:
    target: TargetInterface
    source: SourceInterface

    def validate_in_src(self, table: Table):
        return self._validate_table(
            table_detail=self.source.fetch_table_detail(table=table),
            table=table
        )

    def validate_in_target(self, table: Table):
        with self.target.transaction() as conn:
            return self._validate_table(
                table=table,
                table_detail=self.target.fetch_table_detail(table=table)
            )

    def validate_watermark(self, table: Table) -> WatermarkValidationResult:
        with self.target.transaction() as conn:
            watermark = self.target.fetch_watermark(
                conn=conn, table= table
            )

            return WatermarkValidationResult(
                exist=type(watermark) == Watermark,
                watermark=watermark,
                resolved=False
            )

    @staticmethod
    def _validate_table(table: Table, table_detail: TableDetail):
        table_exists = table_detail.info.table_name == table.name

        if not table_exists:
            return TableValidationResult(
                table_name=table.name,
                exists=False,
                column_validation=ColumnValidation(
                    all_exist=False,
                    missing_columns=[c.name for c in table.columns])
            )

        db_col_names = {c.name for c in table_detail.columns}
        needed_col_names = {c.name for c in table.columns}
        missing = list(needed_col_names - db_col_names)

        return TableValidationResult(
            table_name=table.name,
            exists=True,
            column_validation=ColumnValidation(
                all_exist=len(missing) == 0,
                missing_columns=missing,
            )
        )
