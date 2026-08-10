from datetime import datetime

from psycopg.sql import SQL, Identifier, Literal

from data_forge.util.util import build_columns, build_column_cast


def select_all_query(table_name: str, columns: list[str],
                     source: str, run_datetime: datetime, format_query: bool = False) -> bytes:
    columns = build_columns(columns)
    if format_query:
        return (
            SQL("select {}, {}::timestamp as dw_run_timestamp from {}.{}")
            .format(
                columns
                , Literal(run_datetime)
                , Identifier(source)
                , Identifier(table_name)
            )
        ).as_bytes()

    return (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {}")
        .format(
            columns
            , Literal(run_datetime)
            , Identifier(table_name)
        )
    ).as_bytes()


def insert_all_into(table_name: str, columns: list[str],
                    source: str, format_query: bool = False):
    if format_query:
        return (
            SQL("insert into {}.{} (%s) values %s")
            .format(
                Identifier(source)
                , Identifier(table_name)
                , columns
            )
        ).as_bytes()

    return (
        SQL("insert into {} ({}) values (%s)")
        .format(
            Identifier(table_name)
            , columns
        )
    ).as_bytes()


def select_all_after_watermark(table_name: str, highest_mark: datetime,
                               columns: list[str], marking_column: str,
                               source: str, run_datetime: datetime, format_query: bool = False):
    columns = build_columns(columns)
    if format_query:
        return (
            SQL("select {}, {} as dw_run_timestamp from {}.{} where {} > {} order by {} asc")
            .format(
                columns
                , Literal(run_datetime)
                , Identifier(source)
                , Identifier(table_name)
                , Identifier(marking_column)
                , Literal(highest_mark)
                , Identifier(marking_column)
            )
        ).as_bytes()

    return (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {} where {} > {} order by updated_at asc")
        .format(
            columns
            , Literal(run_datetime)
            , Identifier(table_name)
            , Identifier(marking_column)
            , Literal(highest_mark)
        )
    ).as_bytes()


def copy_from_csv(table_name: str, columns: list, columns_cast: dict, source: str, run_datetime: datetime, file_path):
    column_cast = build_column_cast(columns_cast)
    columns = build_columns(columns)
    return f"Insert into pg.{source}.{table_name.lower()} ({columns}, dw_run_timestamp) SELECT {columns}, '{run_datetime}'::timestamp as dw_run_timestamp FROM read_csv('{file_path}', header=True)"

def execution_planner(table_name: str, highest_mark: datetime, marking_column: str):
    return f"select count(*) as records_count from {table_name} where {marking_column} > {highest_mark}"


def check_records(table_name: str):
    return f"select count(*) as records_count from {table_name}"
