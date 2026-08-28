from datetime import datetime
from psycopg.sql import SQL, Identifier, Literal, Placeholder
from pydantic.dataclasses import dataclass

from data_forge.context.context import Table, PipelineConfig
from data_forge.logging.watermark import Watermark
from data_forge.util.util import build_columns


@dataclass
class QueryBuilder:
    table: Table
    schema_name: str
    watermark: Watermark
    run_datetime: datetime
    pipeline_config: PipelineConfig

    @staticmethod
    def build_placeholder(number: int) -> list[Placeholder]:
        return [Placeholder() for _ in range(number)]

    def select_table(self) -> bytes:
        return SQL("SELECT * FROM {}.{}").format(
            Identifier(self.schema_name),
            Identifier(self.table.name)
        ).as_bytes()

    def select_with_metadata(self, format_query: bool = False) -> bytes:
        if format_query:
            return SQL("SELECT {}, {}::TIMESTAMP AS dw_run_timestamp FROM {}.{}").format(
                SQL(', ').join(map(Identifier, self.table.column_names)),
                Literal(self.run_datetime),
                Identifier(self.schema_name),
                Identifier(self.table.name)
            ).as_bytes()

        return SQL("SELECT {}, {}::TIMESTAMP AS dw_run_timestamp FROM {}").format(
            SQL(', ').join(map(Identifier, self.table.column_names)),
            Literal(self.run_datetime),
            Identifier(self.table.name)
        ).as_bytes()

    def insert(self, format_query: bool = False) -> bytes:
        value_placeholders = self.build_placeholder(len(self.table.column_names))

        if format_query:
            return SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                Identifier(self.schema_name),
                Identifier(self.table.name),
                SQL(', ').join(map(Identifier, self.table.column_names)),
                SQL(', ').join(value_placeholders)
            ).as_bytes()

        return SQL("INSERT INTO {} ({}) VALUES ({})").format(
            Identifier(self.table.name),
            SQL(', ').join(map(Identifier, self.table.column_names)),
            SQL(', ').join(value_placeholders)
        ).as_bytes()

    def extract_incremental(self, format_query: bool = False) -> bytes:
        if format_query:
            return SQL("""
                SELECT 
                    {}, 
                    {}::TIMESTAMP AS dw_run_timestamp 
                FROM {}.{} 
                WHERE {} > {} 
                ORDER BY {} ASC
            """).format(
                SQL(', ').join(map(Identifier, self.table.column_names)),
                Literal(self.run_datetime),
                Identifier(self.schema_name),
                Identifier(self.table.name),
                Identifier(self.table.marking_column),
                Literal(self.watermark.highest_watermark),
                Identifier(self.table.marking_column)
            ).as_bytes()

        return SQL("""
            SELECT 
                {}, 
                {}::TIMESTAMP AS dw_run_timestamp 
            FROM {} 
            WHERE {} > {} 
            ORDER BY {} ASC
        """).format(
            SQL(', ').join(map(Identifier, self.table.column_names)),
            Literal(self.run_datetime),
            Identifier(self.table.name),
            Identifier(self.table.marking_column),
            Literal(self.watermark.highest_watermark),
            Identifier(self.table.marking_column)
        ).as_bytes()

    def count_delta(self) -> bytes:
        return SQL("""
            SELECT 
                COUNT(*) AS egress_volume, 
                {} AS table_name, 
                {} AS schema_name
            FROM {}.{}
            WHERE {} > {}
        """).format(
            Literal(self.table.name),
            Literal(self.schema_name),
            Identifier(self.schema_name),
            Identifier(self.table.name),
            Identifier(self.table.marking_column),
            Literal(self.watermark.highest_watermark)
        ).as_bytes()

    def import_csv(self, file_path: str) -> str:
        columns_str = build_columns(self.table.column_names)
        return f"""
            INSERT INTO {self.schema_name}.{self.table.name.lower()} ({columns_str}, dw_run_timestamp) 
            SELECT {columns_str}, '{self.run_datetime}'::TIMESTAMP AS dw_run_timestamp 
            FROM read_csv('{file_path}', header=True)
        """

