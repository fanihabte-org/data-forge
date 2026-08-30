from abc import ABC
from dataclasses import dataclass

from psycopg import Connection
from psycopg.rows import class_row

from data_forge.context.models import Table
from data_forge.db_engine.db_sql_builder import QueryBuilder
from data_forge.analyzer.analysis import VolumeAnalysis
from data_forge.logging.watermark import Watermark


@dataclass
class Analyze(ABC):
    table: Table
    watermark: Watermark
    query_builder: QueryBuilder


@dataclass
class AnalyzeVolume(Analyze):

    # Check data ingress volume
    def execute(self, conn: Connection) -> VolumeAnalysis:
        query = self.query_builder.count_delta_after_watermark(
            table=self.table,
            watermark=self.watermark
        )

        with conn.cursor(row_factory=class_row(VolumeAnalysis)) as cur:
            data: VolumeAnalysis | None = cur.execute(query).fetchone()
            if not data:
                raise RuntimeError(f"Table {self.table.name} returned None for ingress volume analysis")
            return data
