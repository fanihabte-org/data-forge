from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection
from psycopg.rows import class_row

from abc import ABC
from enum import Enum

from data_forge.context.context import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark, WatermarkRepository


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


@dataclass
class ExecutionType(Enum):
    INCREMENTAL = 1
    BULK = 2
    SKIP = 3


@dataclass
class Plan(ABC):
    execution_type: ExecutionType
    run_datetime: datetime
    source_db: SourceDB
    table: Table
    watermark: Watermark
    target_dw: TargetDW
    pipeline_config: PipelineConfig
    query_builder: QueryBuilder

    def execute(self):
        ...

    def report(self):
        ...


@dataclass
class IncrementalPlan(Plan):

    def execute(self):
        extract_incremental_query: bytes = self.query_builder.extract_incremental(format_query=True)
        insert_into_query: bytes = self.query_builder.insert(format_query=True)

        self.target_dw.insert_batches(
            batches=self.source_db.extract_after_watermark(
                sql_query=extract_incremental_query,
                pipeline_config=self.pipeline_config
            ),
            insert_into_query=insert_into_query,
            table=self.table,
            watermark=self.watermark,
            run_datetime=self.run_datetime
        )

    def report(self):
        print()


@dataclass
class BulkPlan(Plan):
    ...


@dataclass
class SkipPlan(Plan):

    def execute(self):
        self.report()

    def report(self):
        ...


@dataclass
class Planner:
    pipeline_config: PipelineConfig
    source_db: SourceDB
    target_dw: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    watermark_repository: WatermarkRepository

    # Watermark exists — full refresh forced, or incremental?
    def build_plan(self) -> dict[str, Plan]:
        lazy_analyses = self.preflight_analysis()
        tables = self.source_db.catalog.tables
        factory = PlanFactory(planner=self)
        plans = {}

        for table_name, table_obj in tables.items():
            table_analysis = lazy_analyses[table_name]
            if table_analysis.ingress_volume.egress_volume == 0:
                plans[table_name] = factory.build_skip_plan(table=table_obj)
            elif table_analysis.ingress_volume.egress_volume > 200_000:
                plans[table_name] = factory.build_bulk_plan(table=table_obj)
            else:
                plans[table_name] = factory.build_incremental_plan(table=table_obj)

        return plans

    def preflight_analysis(self) -> dict[str, LazyAnalysis]:
        plan_analysis = {}

        for table_name, table_obj in self.source_db.catalog.tables.items():
            query_builder = QueryBuilder(
                table=table_obj,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table_name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )

            with self.target_dw.db_engine.build_connection() as conn:
                watermark_check = self.check_watermark(
                    conn=conn,
                    table=table_obj,
                    source_name=self.source_db.catalog.source_name
                )

            with self.source_db.db_engine.build_connection() as conn:
                ingress_volume = self.check_ingress_volume(
                    conn=conn,
                    table_name=table_name,
                    query=query_builder.count_delta()
                )

            plan_analysis[table_name] = LazyAnalysis(
                table_name=table_name,
                watermark_check=watermark_check,
                ingress_volume=ingress_volume
            )

        return plan_analysis

    # Do I have a watermark for this source yet?
    def check_watermark(self, conn: Connection, table: Table, source_name: str) -> WatermarkCheck:

        # if there is no watermark yet try syncing from main table
        if table.name not in self.watermarks.keys():
            print(f"\nTable {table.name} doesn't have a watermark yet")
            return self.try_syncing_watermark(
                conn=conn,
                table=table,
                source_name=source_name
            )

        # if there is watermark already existing return it
        return WatermarkCheck(exists=True, object=self.watermarks[table.name])

    def try_syncing_watermark(self, conn: Connection, table: Table, source_name: str):
        # check target table, returns None if there isn't record in the table
        self.watermark_repository.sync(
            conn=conn,
            table=table,
            schema_name=source_name,
        )

        loaded_watermark = self.watermark_repository.load_from_main_table(conn, table=table, schema_name=source_name)

        self.watermark_repository.set_default_watermark(
            conn=conn,
            table=table,
            schema_name=source_name,
        )

        # Check if sync return object, print state and return check object
        if not loaded_watermark:
            print(f"Watermark Sync: no record found on {source_name}.{table.name}")
            return WatermarkCheck(exists=False, object=None)
        else:
            print(
                f"Watermark Sync: table {source_name}.{table.name} watermark synced to {loaded_watermark.highest_watermark}")
            return WatermarkCheck(exists=True, object=loaded_watermark)

    # Check data ingress volume
    @staticmethod
    def check_ingress_volume(conn: Connection, table_name: str, query: bytes) -> IngressVolume:
        with conn.cursor(row_factory=class_row(IngressVolume)) as cur:
            data: IngressVolume | None = cur.execute(query).fetchone()

            if not data:
                raise RuntimeError(f"Table {table_name} returned None for ingress volume analysis")

            return data


@dataclass
class PlanFactory:
    planner: Planner

    def build_skip_plan(self, table: Table) -> SkipPlan:
        return SkipPlan(
            run_datetime=self.planner.run_datetime,
            source_db=self.planner.source_db,
            table=table,
            watermark=self.planner.watermarks[table.name],
            target_dw=self.planner.target_dw,
            pipeline_config=self.planner.pipeline_config,
            execution_type=ExecutionType.SKIP,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.planner.source_db.catalog.source_name,
                watermark=self.planner.watermarks[table.name],
                run_datetime=self.planner.run_datetime,
                pipeline_config=self.planner.pipeline_config
            )

        )

    def build_incremental_plan(self, table: Table) -> IncrementalPlan:
        return IncrementalPlan(
            run_datetime=self.planner.run_datetime,
            source_db=self.planner.source_db,
            table=table,
            watermark=self.planner.watermarks[table.name],
            target_dw=self.planner.target_dw,
            pipeline_config=self.planner.pipeline_config,
            execution_type=ExecutionType.INCREMENTAL,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.planner.source_db.catalog.source_name,
                watermark=self.planner.watermarks[table.name],
                run_datetime=self.planner.run_datetime,
                pipeline_config=self.planner.pipeline_config
            )
        )

    def build_bulk_plan(self, table: Table) -> BulkPlan:
        return BulkPlan(
            run_datetime=self.planner.run_datetime,
            source_db=self.planner.source_db,
            table=table,
            watermark=self.planner.watermarks[table.name],
            target_dw=self.planner.target_dw,
            pipeline_config=self.planner.pipeline_config,
            execution_type=ExecutionType.BULK,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.planner.source_db.catalog.source_name,
                watermark=self.planner.watermarks[table.name],
                run_datetime=self.planner.run_datetime,
                pipeline_config=self.planner.pipeline_config
            )
        )
