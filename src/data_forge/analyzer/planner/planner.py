from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection
from psycopg.rows import class_row

from abc import ABC
from enum import Enum
from typing import Optional

from data_forge.db_engine.db_sql_builder import count_records_after_watermark
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark


@dataclass
class WatermarkCheck:
    exists: bool
    object: Watermark | None


@dataclass
class IngressVolume:
    table_name: str
    schema_name: str
    egress_volume: int


@dataclass
class LazyAnalysis:
    table_name: str
    ingress_volume: IngressVolume
    watermark_check: WatermarkCheck


class ExecutionCategory(Enum):
    EXPORT = 1
    IMPORT = 2
    CREATE_TABLE = 3


class ExecutionType(Enum):
    BULK = 1
    INCREMENTAL = 2


class Plan(ABC):
    category: str
    type: Optional[str] = None

    def execute(self):
        ...

    def report(self):
        ...


@dataclass
class Planner:
    source_db: SourceDB
    target_dw: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime

    # Watermark exists — full refresh forced, or incremental?
    def build_plan(self):
        ...
    # check if watermark exists
    # check if the table have records

    # if watermark_exists and table_not_empty:
    # if records volume > 1000_000
    # do bulk export and load
    # else
    # do incremental data load
    # elif watermark_not_exits and table_not_empty:
    # get highest records
    # flush watermark
    # re-run assessment process
    # else
    # do bulk export
    # set up first watermark
    # return
    # {
    # table: EXECUTION_TYPE
    # }

    def preflight_analysis(self) -> dict[str, LazyAnalysis]:
        plan_analysis = {}

        for table_name, table_obj in self.source_db.catalog.tables.items():
            with self.target_dw.db_engine.build_connection() as conn:
                watermark_check = self.check_watermark(
                    conn=conn,
                    table_name=table_name,
                    source_name=self.source_db.catalog.source_name,
                    marking_column=table_obj.marking_column
                )

            with self.source_db.db_engine.build_connection() as conn:
                ingress_volume = self.check_ingress_volume(
                    conn=conn,
                    table_name=table_name,
                    source_name=self.source_db.catalog.source_name,
                    marking_column=table_obj.marking_column
                )

            plan_analysis[table_name] = LazyAnalysis(
                table_name=table_name,
                watermark_check=watermark_check,
                ingress_volume=ingress_volume
            )

        return plan_analysis

    # Do I have a watermark for this source yet?
    def check_watermark(self, conn: Connection, table_name: str,
                        source_name: str, marking_column: str) -> WatermarkCheck:

        # if there is no watermark yet try syncing from main table
        if table_name not in self.watermarks.keys():
            print(f"\nTable {table_name} doesn't have a watermark yet")
            return self.try_syncing_watermark(
                conn=conn,
                table_name=table_name,
                source_name=source_name,
                marking_column=marking_column
            )

        # if there is watermark already existing return it
        return WatermarkCheck(exists=True, object=self.watermarks[table_name])

    def try_syncing_watermark(self, conn: Connection, table_name: str, source_name: str, marking_column: str):
        # check target table, returns None if there isn't record in the table
        loaded_watermark = Watermark.sync(
            conn=conn,
            table_name=table_name,
            source_name=source_name,
            marking_column=marking_column,
            run_datetime=self.run_datetime
        )

        # Check if sync return object, print state and return check object
        if not loaded_watermark:
            print(f"Watermark Sync: no record found on {source_name}.{table_name}")
            return WatermarkCheck(exists=False, object=None)
        else:
            print(
                f"Watermark Sync: table {source_name}.{table_name} watermark synced to {loaded_watermark.highest_watermark}")
            return WatermarkCheck(exists=True, object=loaded_watermark)

    # Check data ingress volume
    def check_ingress_volume(self, conn: Connection, table_name: str,
                             marking_column: str, source_name: str) -> IngressVolume:

        with conn.cursor(row_factory=class_row(IngressVolume)) as cur:
            query = count_records_after_watermark(
                table_name=table_name,
                schema_name=source_name,
                marking_column=marking_column,
                highest_watermark=self.watermarks[table_name].highest_watermark
            )

            data: IngressVolume | None = cur.execute(query).fetchone()

            if not data:
                raise RuntimeError(f"Table {table_name} returned None for ingress volume analysis")

            return data

    # match self.source.source:
    #     case "crm":
    #         query = check_records(table_name=table)
    #         self.salesforce.fetch_all_data(query)
    #         return 1
    #     case "erp":
    #         query = check_records(table_name=table)
    #         results = self.source.db_engine.build_connection().execute(query).fetchone()
    #         return results.__dict__["records_count"]
    #     case "ops":
    #         query = check_records(table_name=table)
    #         results = self.source.db_engine.build_connection().execute(query).fetchone()
    #         return results.__dict__["records_count"]
    #     case _:
    #         raise RuntimeError(f"Source {self.source.source} is invalid")

    # Check data ingress volume
    def check_ingress_volume_after_watermark(self):
        pass
