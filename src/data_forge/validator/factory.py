from dataclasses import dataclass
from datetime import datetime

from data_forge.context.models import Table, PipelineConfig
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW

from data_forge.logging.watermark import Watermark, WatermarkRepository
from data_forge.validator.validations import TableValidation, TableWatermarkValidation


@dataclass
class ValidatorFactory:
    pipeline_config: PipelineConfig
    source_db: SourceDB
    target_dw: TargetDW
    watermarks: dict[str, Watermark]
    run_datetime: datetime
    watermark_repository: WatermarkRepository

    def build_src_table_validation(self, table: Table):
        return TableValidation(
            table=table,
            db_engine=self.source_db.db_engine,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config)
        )

    def build_target_table_validation(self, table: Table):
        return TableValidation(
            table=table,
            db_engine=self.target_dw.db_engine,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            )
        )

    def build_watermark_validation(self, table: Table):
        return TableWatermarkValidation(
            table=table,
            db_engine=self.target_dw.db_engine,
            query_builder=QueryBuilder(
                table=table,
                schema_name=self.source_db.catalog.source_name,
                watermark=self.watermarks[table.name],
                run_datetime=self.run_datetime,
                pipeline_config=self.pipeline_config
            ),
            watermark_repository=self.watermark_repository
        )
