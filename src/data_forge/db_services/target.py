from dataclasses import dataclass
from datetime import datetime

from data_forge.context.context import PipelineConfig, Table
from data_forge.db_engine.db_super_class import TargetInterface
from data_forge.logging.watermark import Watermark
import duckdb


@dataclass
class TargetDW(TargetInterface):

    def extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_extract_to_csv_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def bulk_insert_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        with duckdb.connect() as conn:
            conn.execute("Install postgres;")
            conn.execute("Load postgres;")
            conn.execute(f"Attach '{self.db_engine.build_uri()}' as pg (TYPE postgres);")

    def bulk_insert_from_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    def insert_batches(self,
                       batches: list[tuple],
                       insert_into_query: bytes,
                       table: Table,
                       watermark: Watermark,
                       run_datetime: datetime
                       ):
        with self.db_engine.build_connection() as conn:
            print(f"EDI: built connection for: {self.db_engine.build_uri()}")

            print(insert_into_query)
            cur = conn.cursor()
            total_rows = 0
            for batch in batches:
                cur.executemany(insert_into_query, batch)
                batch_highest_watermark = batch[-1][table.mc_index].isoformat()
                watermark.upsert(
                    conn=conn,
                    new_watermark=batch_highest_watermark,
                    run_datetime=run_datetime
                )
                total_rows += 1
                print(f"Loaded {total_rows} rows and set highest watermark to {watermark.highest_watermark}")

        # mc_index = columns.index(watermark.marking_column)

        # columns += ["dw_run_timestamp"]
        # sql_query = insert_all_into(
        #     table_name=table_name,
        #     columns=columns,
        #     source=source,
        #     format_query=True
        # )

        # for file in Path(pipeline_config.export_path).iterdir():
        #     # sql_query = copy_from_csv(table_name=table_name,
        #     #                           columns=columns,
        #     #                           source=source,
        #     #                           run_datetime=run_datetime,
        #     #                           file_path=file
        #     #                           )
        #     print(sql_query)
        #     conn.execute(sql_query)
