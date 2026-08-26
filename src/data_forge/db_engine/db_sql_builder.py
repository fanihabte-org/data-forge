from datetime import datetime

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from data_forge.util.util import build_columns


def select_all_query(table_name: str, columns: list[str],
                     source: str, run_datetime: datetime, format_query: bool = False) -> bytes:
    if format_query:
        return (
            SQL("select {}, {}::timestamp as dw_run_timestamp from {}.{}")
            .format(
                SQL(', ').join(map(Identifier, columns))
                , Literal(run_datetime)
                , Identifier(source)
                , Identifier(table_name)
            )
        ).as_bytes()

    return (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {}")
        .format(
            SQL(', ').join(map(Identifier, columns))
            , Literal(run_datetime)
            , Identifier(table_name)
        )
    ).as_bytes()


def insert_all_into(table_name: str, columns: list[str],
                    source: str, format_query: bool = False):
    value_place_holders = [Placeholder() for _ in range(len(columns))]

    if format_query:
        return (
            SQL("insert into {}.{} ({}) values ({})")
            .format(
                Identifier(source)
                , Identifier(table_name)
                , SQL(', ').join(map(Identifier, columns))
                , SQL(', ').join(value_place_holders)
            )
        ).as_bytes()

    return (
        SQL("insert into {} ({}) values ({})")
        .format(
            Identifier(table_name)
            , SQL(', ').join(map(Identifier, columns))
            , SQL(', ').join(value_place_holders)
        )
    ).as_bytes()


def select_all_after_watermark(table_name: str, highest_mark: datetime,
                               columns: list[str], marking_column: str,
                               source: str, run_datetime: datetime, format_query: bool = False):
    if format_query:
        return (
            SQL("select {}, {} as dw_run_timestamp from {}.{} where {} > {} order by {} asc")
            .format(
                SQL(', ').join(map(Identifier, columns))
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
            SQL(', ').join(map(Identifier, columns))
            , Literal(run_datetime)
            , Identifier(table_name)
            , Identifier(marking_column)
            , Literal(highest_mark)
        )
    ).as_bytes()


def copy_from_csv(table_name: str, columns: list, source: str, run_datetime: datetime, file_path):
    columns = build_columns(columns)
    return f"insert into pg.{source}.{table_name.lower()} ({columns}, dw_run_timestamp) SELECT {columns}, '{run_datetime}'::timestamp as dw_run_timestamp FROM read_csv('{file_path}', header=True)"


def execution_planner(table_name: str, highest_mark: datetime, marking_column: str):
    return f"select count(*) as records_count from {table_name} where {marking_column} > {highest_mark}"


def upsert_watermark(columns: list[str], table_name: str, schema: str, conflict_column: str):
    value_place_holders = [Placeholder() for _ in range(len(columns))]

    return SQL(
        "insert into {}.{} ({}) values ({}) "
        "on CONFLICT ({}) "
        "do update set "
        "highest_watermark = GREATEST(pipeline_run.watermark_logs.highest_watermark, EXCLUDED.highest_watermark)"
        "dw_run_timestamp = GREATEST(pipeline_run.watermark_logs.dw_run_timestamp, EXCLUDED.dw_run_timestamp)"
    ).format(
        Identifier(schema)
        , Identifier(table_name)
        , SQL(', ').join(map(Identifier, columns))
        , SQL(', ').join(value_place_holders)
        , Identifier(conflict_column)
    ).as_bytes()


def check_records(table_name: str):
    return f"select count(*) as records_count from {table_name}"
