from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import Table, Catalog
from data_forge.contracts.target_interface import TargetInterface
from data_forge.resolver.models import WatermarkSyncResolution, ResolutionType, Resolution
from data_forge.resolver.reporter import ResolutionReporter
from data_forge.validator.models import ValidationResult


@dataclass
class Resolver:
    target: TargetInterface
    source_name: str

    def resolve_catalog(self, validation_results: dict[str, ValidationResult], catalog: Catalog):

        for table_name, validation_result in validation_results.items():
            self.resolve_table(
                validation_result=validation_result,
                table=catalog.get_table(table_name=table_name)
            )

    def resolve_table(self, validation_result: ValidationResult, table: Table):

            if not validation_result.source.exists:
                raise RuntimeError(f"Table: {table.name} doesn't exist in the {self.source_name.upper()}")

            with self.target.transaction() as conn:
                if not validation_result.target.exists:
                    self.create_table(
                        table=table,
                        report=True,
                        conn=conn
                    )

                if not validation_result.watermark.exist:
                    self.sync_watermark(
                        table=table,
                        report=True,
                        conn=conn
                    )

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
