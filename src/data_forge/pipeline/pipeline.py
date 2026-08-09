from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from data_forge.db_services.target import TargetDW
from data_forge.db_services.source import SourceDB
from src.data_forge.context.context import Context
from data_forge.sales_force.sales_force import SalesForce
from data_forge.logging.watermark import Watermark


@dataclass(frozen=True)
class Pipeline:
    context: Context
    sales_force: SalesForce
    erp: SourceDB
    ops: SourceDB
    edi: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime

    def bulk_export(self, from_table: str, to_folder: Path):
        self.sales_force.request_bulk_export(table_name=from_table, folder_path=to_folder)

    def run_daily_api_el(self):
        source = "crm"
        tables = self.context.get_tables(source)

        for table in tables:
            data_stream = self.sales_force.fetch_data_from_table(table_name=table)
            self.edi.insert_many(batch=data_stream, table_name=table, source=source)

    def run_daily_pipeline(self):
        db_sources = [self.erp, self.ops]

        for db_source in db_sources:
            self._read_write_tables(source_db=db_source)

    def run_erp_pipeline(self):
        self._read_write_tables(source_db=self.erp)

    def run_ops_pipeline(self):
        self._read_write_tables(source_db=self.ops)

    def _read_write_tables(self, source_db: SourceDB):
        tables = self.context.get_tables(source_db.source)

        for table in tables:
            print(f"Started work on table {table}")
            watermark_response = self._check_watermark(table)
            batch_rows = source_db.request_data(table_name=table, run_datetime=self.run_datetime,
                                                 watermark_response=watermark_response)
            self.edi.insert_many(batch=batch_rows, table_name=table, source=source_db.source)
            print(f"Completed work on table <<{table}>>\n")

    def _check_watermark(self, table_name: str) -> dict:
        if watermark := self.watermarks.get(table_name):
            return {"exists": True, "watermark": watermark}

        return {"exists": False}
