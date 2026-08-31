from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.logging.watermark import WatermarkRepository
from data_forge.resolver.models import WatermarkSyncResolution, ResolutionType, Resolution
from data_forge.resolver.reporter import ResolutionReporter


@dataclass
class Resolver:
    source_name: str
    watermark_repository: WatermarkRepository
    query_builder: QueryBuilder

    def sync_watermark(self, conn: Connection, table: Table, report: bool = False) -> WatermarkSyncResolution:
        water_sync_resolution = WatermarkSyncResolution(
            table=table,
            resolution_type=ResolutionType.WATERMARK_SYNC,
            synced_watermark=self.watermark_repository.sync(
                conn=conn, table=table, schema_name=self.source_name
            )
        )

        if report:
            ResolutionReporter.print_water_sync_resolution(
                water_sync_resolution=water_sync_resolution
            )

        return water_sync_resolution

    def create_table(self, conn: Connection, table: Table, report: bool = False) -> Resolution:
        with conn.cursor() as cur:
            cur.execute(self.query_builder.create_table(table=table))

        table_resolution = Resolution(
            table=table,
            resolution_type=ResolutionType.TABLE_CREATION
        )

        if report:
            ResolutionReporter.print_table_creation(
                table_resolution=table_resolution
            )

        return table_resolution