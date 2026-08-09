from datetime import datetime

from psycopg.sql import SQL, Identifier, Literal


def select_all_query(table_name: str, columns: list[dict],
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


def insert_all_into(table_name: str, columns: list[dict],
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
                               columns: list[dict], marking_column: str,
                               source: str, run_datetime: datetime, format_query: bool = False):
    columns = build_columns(columns)
    if format_query:
        return (
            SQL("select {}, {}::timestamp as dw_run_timestamp from {}.{} where {} > {}")
            .format(
                columns
                , Literal(run_datetime)
                , Identifier(source)
                , Identifier(table_name)
                , Identifier(marking_column)
                , Literal(highest_mark)
            )
        ).as_bytes()

    return (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {} where {} > {}")
        .format(
            columns
            , Literal(run_datetime)
            , Identifier(table_name)
            , Identifier(marking_column)
            , Literal(highest_mark)
        )
    ).as_bytes()


def build_columns(columns: list[dict]):
    column_names = []
    for column in columns:
        column_names.append(column["name"])

    return ", ".join(column_names)
