from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from typing import TYPE_CHECKING

from data_forge.pipeline.validator import Validator

if TYPE_CHECKING:
    from data_forge.db_services.source import SourceDB
    from data_forge.db_services.target import TargetDW
    from data_forge.errors.errors import WatermarkNotAvailable
    from data_forge.logging.watermark import Watermark
    from data_forge.sales_force.sales_force import SalesForce


@dataclass(frozen=True)
class Pipeline:
    sales_force: SalesForce
    erp: SourceDB
    ops: SourceDB
    edi: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime

    def run_bulk_salesforce_export(self):
        tables = self.sales_force.catalog.tables

        for table in tables.values():
            print(f"Started work on table {table}")
            self.sales_force.bulk_export_all(table_name=table.name, run_datetime=self.run_datetime)
            print(f"Completed work on table <<{table}>>\n")

    def run_incremental_salesforce_pipeline(self):
        tables = self.sales_force.catalog.tables

        for table in tables.values():
            print(f"Started work on table {table}")
            watermark_response = self._check_watermark(table.name)
            data_stream = self.sales_force.extract_after_watermark(watermark=watermark_response,
                                                                   run_datetime=self.run_datetime)
            print(f"Completed work on table <<{table}>>\n")
            # self.edi.insert_many(batch=data_stream, table_name=table, source=source)

    # def load_export_data_to_dw(self, table_name: str, download_dir: Path):
    #     self.edi.bulk_insert_csv(table_name=table_name,
    #                              source="crm",
    #                              download_dir=download_dir,
    #                              run_datetime=self.run_datetime,
    #                              columns=)

    def run_incremental_daily_pipeline(self):
        db_sources = [self.erp, self.ops]

        for db_source in db_sources:
            self._read_write_tables(source_db=db_source)

    def run_incremental_erp_pipeline(self):
        self._read_write_tables(source_db=self.erp)

    def run_incremental_ops_pipeline(self):
        self._read_write_tables(source_db=self.ops)

    def _read_write_tables(self, source_db: SourceDB):
        tables = source_db.catalog.tables

        for table in tables.values():
            print(f"Started work on table {table}")
            watermark_response = self._check_watermark(table.name)
            batches = source_db.extract_after_watermark(
                run_datetime=self.run_datetime,
                watermark=watermark_response
            )

            self.edi.insert_batches(
                batches=batches,
                table_name=table.name,
                source=source_db.catalog.source_name,
                watermark=watermark_response,
                columns=table.column_names,
                run_datetime=self.run_datetime
            )

            print(f"Completed work on table <<{table}>>\n")

    def _check_watermark(self, table_name: str) -> Watermark:
        if watermark := self.watermarks.get(table_name):
            return watermark

        raise WatermarkNotAvailable(table=table_name)

    def validate_pipeline(self):
        validator = Validator(
            source_db=self.ops,
            target_dw=self.edi,
            salesforce=self.sales_force
        )
        print(validator.run_checks())