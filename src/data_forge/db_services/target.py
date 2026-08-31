from dataclasses import dataclass

from psycopg import Connection

from data_forge.context.models import PipelineConfig
from data_forge.db_engine.db_super_class import TargetInterface
from data_forge.logging.watermark import WatermarkRepository
import duckdb


@dataclass
class TargetDW(TargetInterface):
    watermark_repository: WatermarkRepository

    def extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_extract_after_watermark(self, conn: Connection, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_extract_to_csv_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_insert_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_insert_from_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        with duckdb.connect() as conn:
            conn.execute("Install postgres;")
            conn.execute("Load postgres;")
            conn.execute(f"Attach '{self.db_engine.build_uri()}' as pg (TYPE postgres);")

    def bulk_insert_batches(self, conn, sql_query, chunks):
        total = 0
        with conn.cursor().copy(sql_query) as copy:
            for chunk in chunks:
                copy.write(chunk)
                total += len(chunk)
                print(f"\r  {total / 1024 / 1024:,.1f} MB", end="", flush=True)
        print()

    def insert_batches(self, batches: list[tuple], sql_query: bytes):
        with self.db_engine.build_connection() as conn:
            with conn.cursor() as cur:
                for batch in batches:
                    cur.executemany(sql_query, batch)
