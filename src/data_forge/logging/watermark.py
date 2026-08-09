from dataclasses import dataclass
from datetime import datetime

from data_forge.db_services.target import TargetDW
from psycopg.rows import class_row


@dataclass
class Watermark:
    source_system: str
    table_name: str
    schema_name: str
    marking_column: str
    high_watermark: datetime
    dw_run_timestamp: datetime

    @staticmethod
    def load(target_dw: TargetDW) -> dict[str, "Watermark"]:
        sql_query = "select * from meta_data.watermarks"

        with target_dw.db_engine.build_connection().cursor(row_factory=class_row(Watermark)) as cur:
            watermarks: list[Watermark] = cur.execute(sql_query).fetchall()
            watermarks_dict = {}

            for watermark in watermarks:
                watermarks_dict[watermark.table_name] = watermark

            return watermarks_dict
