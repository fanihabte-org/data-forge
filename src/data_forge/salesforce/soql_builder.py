from dataclasses import dataclass
from datetime import datetime

from data_forge.context.models import Table, PipelineConfig
from data_forge.watermark.models import Watermark


@dataclass
class SoqlBuilder:
    schema_name: str
    run_datetime: datetime
    pipeline_config: PipelineConfig

    @staticmethod
    def build_columns(column_names: list[str]):
        return ", ".join(column_names)

    def select_all_query(self, table: Table) -> str:
        columns = self.build_columns(table.column_names)

        return f"SELECT {columns} FROM {table.name}"

    def select_all_after_watermark(self, table: Table, watermark: Watermark) -> str:
        columns = self.build_columns(table.column_names)

        return f"""
            SELECT 
                {columns} 
            FROM {table.name} 
            WHERE {table.marking_column} > '{watermark.highest_watermark.isoformat()}' 
            ORDER BY {table.marking_column}
        """

    @staticmethod
    def execution_planner(table: Table, watermark: Watermark):
        return f"""
            SELECT 
                COUNT(*) AS records_count 
            FROM {table.name} 
            WHERE {table.marking_column} > {watermark.highest_watermark}
        """

    @staticmethod
    def check_records(self, table: Table):
        return f"SELECT COUNT(*) AS records_count FROM {table.name}"
