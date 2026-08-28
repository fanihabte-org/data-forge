from dataclasses import dataclass

from data_forge.context.context import Catalog, PipelineConfig
from data_forge.db_engine.db_super_class import SourceInterface
from data_forge.db_engine.engine import DBEngine


@dataclass
class SourceDB(SourceInterface):
    db_engine: DBEngine
    catalog: Catalog

    def extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        chunk_size = pipeline_config.chunk_size
        total_rows = 0

        print(f"{self.catalog.source_name}: built query: {sql_query.decode()}")
        with self.db_engine.build_connection() as conn:
            print(f"{self.catalog.source_name}: built connection")

            cur = conn.cursor(name="stream_cursor")
            cur.execute(sql_query)

            while True:
                rows = cur.fetchmany(chunk_size)

                if not rows:
                    break

                yield rows
                total_rows += len(rows)

            print(f"{self.catalog.source_name}: read {total_rows} records")

    def bulk_extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        with self.db_engine.build_connection() as conn:
            with conn.cursor().copy(sql_query) as copy:
                for chunk in copy:
                    yield chunk

    def bulk_extract_to_csv_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        ...