from datetime import datetime

from data_forge.logging.watermark import Watermark
from data_forge.util.util import build_columns


def select_all_query(table_name: str, columns: list[str]) -> str:
    columns = build_columns(columns)

    return f"select {columns} from {table_name.title()}"


def select_all_after_watermark(watermark: Watermark, columns: list[str]) -> str:
    columns = build_columns(columns)
    return f"select {columns} from {watermark.table_name.title()} where LastModifiedDate > '{watermark.highest_watermark.isoformat()}' order by LastModifiedDate"


def execution_planner(table_name: str, highest_mark: datetime, marking_column: str):
    return f"select count(*) as records_count from {table_name.title()} where {marking_column} > {highest_mark}"


def check_records(table_name: str):
    return f"select count(*) as records_count from {table_name.title()}"
