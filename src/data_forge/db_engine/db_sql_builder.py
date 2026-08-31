from datetime import datetime
from psycopg.sql import SQL, Identifier, Literal, Placeholder
from pydantic.dataclasses import dataclass

from data_forge.context.models import Table, PipelineConfig, Column
from data_forge.logging.watermark import Watermark
from data_forge.util.util import build_columns


@dataclass
class QueryBuilder:
    schema_name: str
    run_datetime: datetime
    pipeline_config: PipelineConfig

    @staticmethod
    def build_placeholder(number: int) -> list[Placeholder]:
        return [Placeholder() for _ in range(number)]

    def select_all(self, table: Table) -> bytes:
        return SQL("SELECT * FROM {}.{}").format(
            Identifier(self.schema_name),
            Identifier(table.name)
        ).as_bytes()

    def select_all_from_with_metadata(self, table: Table, format_query: bool = False) -> bytes:
        if format_query:
            return SQL("SELECT {}, {}::TIMESTAMP AS dw_run_timestamp FROM {}.{}").format(
                SQL(', ').join(map(Identifier, table.column_names)),
                Literal(self.run_datetime),
                Identifier(self.schema_name),
                Identifier(table.name)
            ).as_bytes()

        return SQL("SELECT {}, {}::TIMESTAMP AS dw_run_timestamp FROM {}").format(
            SQL(', ').join(map(Identifier, table.column_names)),
            Literal(self.run_datetime),
            Identifier(table.name)
        ).as_bytes()

    def insert_into(self, table: Table, format_query: bool = False) -> bytes:
        value_placeholders = self.build_placeholder(len(table.target_column_names))

        if format_query:
            return SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                Identifier(self.schema_name),
                Identifier(table.name),
                SQL(', ').join(map(Identifier, table.target_column_names)),
                SQL(', ').join(value_placeholders)
            ).as_bytes()

        return SQL("INSERT INTO {} ({}) VALUES ({})").format(
            Identifier(table.name),
            SQL(', ').join(map(Identifier, table.target_column_names)),
            SQL(', ').join(value_placeholders)
        ).as_bytes()

    def select_all_with_metadata_after_watermark(self, table: Table, watermark: Watermark, format_query: bool = False) -> bytes:
        if format_query:
            return SQL("""
                       SELECT
                           {}, {}:: TIMESTAMP AS dw_run_timestamp
                       FROM {}.{}
                       WHERE {} > {}
                       ORDER BY {} ASC
                       """).format(
                SQL(', ').join(map(Identifier, table.column_names)),
                Literal(self.run_datetime),
                Identifier(self.schema_name),
                Identifier(table.name),
                Identifier(table.marking_column),
                Literal(watermark.highest_watermark),
                Identifier(table.marking_column)
            ).as_bytes()

        return SQL("""
                   SELECT
                       {}, {}:: TIMESTAMP AS dw_run_timestamp
                   FROM {}
                   WHERE {} > {}
                   ORDER BY {} ASC
                   """).format(
            SQL(', ').join(map(Identifier, table.column_names)),
            Literal(self.run_datetime),
            Identifier(table.name),
            Identifier(table.marking_column),
            Literal(watermark.highest_watermark),
            Identifier(table.marking_column)
        ).as_bytes()

    def count_delta_after_watermark(self, table: Table, watermark: Watermark) -> bytes:
        return SQL("""
                   SELECT COUNT(*) AS egress_volume, {} AS table_name, {} AS schema_name
                   FROM {}.{}
                   WHERE {} > {}
                   """).format(
            Literal(table.name),
            Literal(self.schema_name),
            Identifier(self.schema_name),
            Identifier(table.name),
            Identifier(table.marking_column),
            Literal(watermark.highest_watermark)
        ).as_bytes()

    def import_csv(self, table: Table, file_path: str) -> str:
        columns_str = build_columns(table.column_names)
        return f"""
            INSERT INTO {self.schema_name}.{table.name.lower()} ({columns_str}, dw_run_timestamp) 
            SELECT {columns_str}, '{self.run_datetime}'::TIMESTAMP AS dw_run_timestamp 
            FROM read_csv('{file_path}', header=True)
        """

    def copy_binary_in(self, table: Table):
        return SQL(
            "COPY {}.{} ({}) FROM STDIN (FORMAT BINARY)"
        ).format(
            Identifier(self.schema_name),
            Identifier(table.name),
            SQL(', ').join(map(Identifier, table.target_column_names)),
        )

    def copy_binary_out(self, table: Table):
        return SQL(
            """
            COPY (
                SELECT 
                    {}
                    , {}::TIMESTAMP AS dw_run_timestamp 
                FROM {}.{})
            TO STDOUT (FORMAT BINARY)
            """
        ).format(
            SQL(', ').join(map(Identifier, table.column_names)),
            Literal(self.run_datetime),
            Identifier(self.schema_name), Identifier(table.name)
        )

    def select_info(self, table: Table):
        return SQL(
            """
            SELECT schemaname AS schema_name
                 , relname    AS table_name
                 , n_live_tup AS estimated_rows
            FROM pg_stat_user_tables
            WHERE schemaname = {} and relname = {}
            ORDER BY n_live_tup DESC;
            """
        ).format(
            Literal(self.schema_name),
            Literal(table.name)
        ).as_bytes()

    def select_columns_info(self, table: Table):
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
            Literal(table.name)
        ).as_bytes()

    def create_table(self, table: Table) -> bytes:
        formatted_columns = []
        for col in table.target_columns:
            col_sql = SQL("{} {}").format(
                Identifier(col.name),
                SQL(col.type)
            )
            if getattr(col, "nullability", "").lower() in ("no", "false"):
                col_sql += SQL(" NOT NULL")

            formatted_columns.append(col_sql)

        pk_clause = SQL("")
        if table.primary_keys:
            formatted_pks = [Identifier(pk) for pk in table.primary_keys]
            pk_clause = SQL(",\n    PRIMARY KEY ({})").format(
                SQL(", ").join(formatted_pks)
            )

        return SQL(
            """
            CREATE TABLE {}.{} (
                {}
                {}
            )
            """
        ).format(
            Identifier(self.schema_name),
            Identifier(table.name),
            SQL(",\n    ").join(formatted_columns),
            pk_clause
        ).as_bytes()
