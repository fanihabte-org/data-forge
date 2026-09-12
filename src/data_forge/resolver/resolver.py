from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.contracts.target_interface import TargetInterface
from data_forge.resolver.models import WatermarkSyncResolution, ResolutionType, Resolution
from data_forge.resolver.reporter import ResolutionReporter


@dataclass
class Resolver:
    target: TargetInterface
    source_name: str

    def sync_watermark(self, conn: Connection, table: Table, report: bool = False) -> WatermarkSyncResolution:
        water_sync_resolution = WatermarkSyncResolution(
            table=table,
            resolution_type=ResolutionType.WATERMARK_SYNC,
            synced_watermark=self.target.sync_watermark(conn=conn, table=table)
        )


        if report:
            ResolutionReporter.print_water_sync_resolution(
                water_sync_resolution=water_sync_resolution
            )

        return water_sync_resolution

    def create_table(self, conn: Connection, table: Table, report: bool = False) -> Resolution:
        self.target.create_table(table=table, conn=conn)

        table_resolution = Resolution(
            table=table,
            resolution_type=ResolutionType.TABLE_CREATION
        )

        if report:
            ResolutionReporter.print_table_creation(
                table_resolution=table_resolution
            )

        return table_resolution