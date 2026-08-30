from dataclasses import dataclass

from data_forge.context.models import Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.target import TargetDW
from data_forge.logging.watermark import WatermarkRepository


@dataclass
class Resolver:
    schema_name: str
    target_dw: TargetDW
    table: Table
    watermark_repository: WatermarkRepository
    query_builder: QueryBuilder

    def sync_watermark(self, table: Table):
        with self.target_dw.db_engine.build_connection() as conn:
            self.watermark_repository.sync(
                conn=conn, table=table, schema_name=self.schema_name
            )

    def create_table(self, table: Table):
        with self.target_dw.db_engine.build_connection() as conn:
            self.query_builder.create_table(
                table= table
            )
