from abc import ABC
from dataclasses import dataclass

from pydantic import BaseModel

from data_forge.context.context import Context
from data_forge.db_engine.db_super_class import SourceInterface
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW
from enum import Enum

from data_forge.errors.errors import WatermarkNotAvailable
from data_forge.logging.watermark import Watermark
from data_forge.sales_force.sales_force import SalesForce
from data_forge.sales_force.sf_soql_builder import check_records, execution_planner





@dataclass
class Planner:
    context: Context
    salesforce: SalesForce
    sources: list[SourceInterface]
    target: TargetDW
    watermarks: dict[str, Watermark]

    # Watermark exists — full refresh forced, or incremental?
    def build_plan(self):
        pass
        # check if watermark exists
        # check if the table have records

        # if watermark_exists and table_not_empty:
            # if records volume > 1000_000
                # do bulk export and load
            # else
                # do incremental data load
        # elif watermark_not_exits and table_not_empty:
            # get highest records
            # flush watermark
            # re-run assessment process
        # else
            # do bulk export
            # set up first watermark
        # return
            # {
                # table: EXECUTION_TYPE
            # }

    def execute(self):
        pass


    # Do I have a watermark for this source yet?
    def check_watermark(self, table):
        if watermark := self.watermarks.get(table):
            return watermark

        raise WatermarkNotAvailable(table=table)


    # Any data I downloaded last run but never loaded?
    def check_downloads(self):
        pass

    # Check data ingress volume
    def check_ingress_volume(self, table):
        pass
        # match self.source.source:
        #     case "crm":
        #         query = check_records(table_name=table)
        #         self.salesforce.fetch_all_data(query)
        #         return 1
        #     case "erp":
        #         query = check_records(table_name=table)
        #         results = self.source.db_engine.build_connection().execute(query).fetchone()
        #         return results.__dict__["records_count"]
        #     case "ops":
        #         query = check_records(table_name=table)
        #         results = self.source.db_engine.build_connection().execute(query).fetchone()
        #         return results.__dict__["records_count"]
        #     case _:
        #         raise RuntimeError(f"Source {self.source.source} is invalid")


    # Check data ingress volume
    def check_ingress_volume_after_watermark(self):
        pass