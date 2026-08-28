from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection
from psycopg.rows import class_row

from data_forge.analyzer.models import LazyAnalysis, WatermarkCheck, IngressVolume
from data_forge.context.context import PipelineConfig, Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW
from data_forge.logging.watermark import Watermark, WatermarkRepository

@dataclass
class Analyzer:
    target_dw: TargetDW
    source_db: SourceDB
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    pipeline_config: PipelineConfig
    watermark_repository: WatermarkRepository

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
