from dataclasses import dataclass

from data_forge.context.models import Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.target import TargetDW
from data_forge.logging.watermark import WatermarkRepository
from data_forge.resolver.models import WatermarkSyncResolution, ResolutionType


@dataclass
class Resolver:
    schema_name: str
    target_dw: TargetDW
    watermark_repository: WatermarkRepository
    query_builder: QueryBuilder

    def sync_watermark(self, table: Table) -> WatermarkSyncResolution:
        with self.target_dw.db_engine.build_connection() as conn:
            return WatermarkSyncResolution(
                table=table,
                resolution_type=ResolutionType.WATERMARK_SYNC,
                synced_watermark=self.watermark_repository.sync(
                    conn=conn, table=table, schema_name=self.schema_name
                )
            )

    def create_table(self, table: Table):
        with self.target_dw.db_engine.build_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(self.query_builder.create_table(table=table))
