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
                           {}, {}:: TIMESTAMP AS dw_run_timestamp
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
                       {}, {}:: TIMESTAMP AS dw_run_timestamp
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
                   SELECT COUNT(*) AS egress_volume, {} AS table_name, {} AS schema_name
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

    def copy_binary_from(self):
        return SQL(
            "COPY {}.{} FROM STDOUT (FORMAT BINARY)"
        ).format(
            Identifier(self.schema_name),
            Identifier(self.table.name)
        )

    def copy_binary_to(self):
        return SQL(
            "COPY {}.{} TO STDOUT (FORMAT BINARY)"
        ).format(
            Identifier(self.schema_name),
            Identifier(self.table.name)
        )

    def table_info(self):
        return SQL(
            """
            SELECT 
                schemaname   AS schema_name 
                , relname    AS table_name 
                , n_live_tup AS estimated_rows 
            FROM pg_stat_user_tables 
            WHERE schemaname = {} and relname = {}
            ORDER BY n_live_tup DESC;
            """
        ).format(
            Literal(self.schema_name),
            Literal(self.table.name)
        ).as_bytes()

    def table_columns(self):
        return SQL(
            """
            SELECT column_name        as name
                 , UPPER(
                    CASE
                        WHEN LOWER(data_type) IN ('character varying', 'varchar')
                            THEN 'VARCHAR(' || character_maximum_length || ')'
                        WHEN LOWER(data_type) IN ('character', 'char', 'bpchar')
                            THEN 'CHAR(' || character_maximum_length || ')'
                        WHEN numeric_precision IS NOT NULL AND numeric_scale IS NOT NULL AND
                             LOWER(data_type) IN ('numeric', 'decimal')
                            THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')'
                        WHEN LOWER(data_type) LIKE 'timestamp%' THEN 'TIMESTAMP'
                        WHEN LOWER(data_type) IN ('integer', 'int', 'int4') THEN 'INTEGER'
                        WHEN LOWER(data_type) IN ('bigint', 'int8') THEN 'BIGINT'
                        ELSE data_type
                        END
                   )                  AS type
                 , LOWER(is_nullable) AS nullability
            FROM information_schema.columns
            WHERE table_schema = {} AND table_name = {}
            ORDER BY ordinal_position;
            """
        ).format(
            Literal(self.schema_name),
            Literal(self.table.name)
        ).as_bytes()

    def create_tale(self):
        ...