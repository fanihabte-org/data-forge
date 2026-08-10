from datetime import datetime

from data_forge.db_engine.db_sql_builder import select_all_query, select_all_after_watermark, build_columns
from psycopg.sql import SQL, Identifier, Literal

table_name = "test_table"
columns = [{"name": "column_a"}, {"name": "column_b"}]
source = "test_source"
highest_mark = datetime.now()
marking_column = "test_marking_column"
run_datetime = datetime.now()


def test_select_all_query():
    formatted_query = (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {}.{}")
        .format(
            "column_a, column_b"
            , Literal(run_datetime)
            , Identifier(source)
            , Identifier(table_name)
        )
    ).as_bytes()

    unformatted_query = (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {}")
        .format(
            "column_a, column_b"
            , Literal(run_datetime)
            , Identifier(table_name)
        )
    ).as_bytes()

    assert ((select_all_query(table_name=table_name, columns=columns,
                              source=source, run_datetime=run_datetime))
            == unformatted_query)

    assert ((select_all_query(table_name=table_name, columns=columns,
                              source=source, run_datetime=run_datetime,
                              format_query=True))
            == formatted_query)


def test_select_all_after_watermark():
    formatted_query = (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {}.{} where {} > {}")
        .format(
            "column_a, column_b"
            , Literal(run_datetime)
            , Identifier(source)
            , Identifier(table_name)
            , Identifier(marking_column)
            , Literal(highest_mark)
        )
    ).as_bytes()

    unformatted_query = (
        SQL("select {}, {}::timestamp as dw_run_timestamp from {} where {} > {}")
        .format(
            "column_a, column_b"
            , Literal(run_datetime)
            , Identifier(table_name)
            , Identifier(marking_column)
            , Literal(highest_mark)
        )
    ).as_bytes()

    assert (
            select_all_after_watermark(
                table_name=table_name,
                highest_mark=highest_mark,
                columns=columns,
                source=source,
                marking_column=marking_column,
                run_datetime=run_datetime
            ) == unformatted_query
    )
    assert (
            select_all_after_watermark(
                table_name=table_name,
                highest_mark=highest_mark,
                columns=columns,
                source=source,
                marking_column=marking_column,
                run_datetime=run_datetime,
                format_query=True
            ) == formatted_query
    )


def test_build_columns():
    assert (
            build_columns(columns=columns) == "column_a, column_b"
    )
