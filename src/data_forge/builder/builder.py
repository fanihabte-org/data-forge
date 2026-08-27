from pathlib import Path

from datetime import datetime
from dataclasses import dataclass

from data_forge.sales_force.auth import Auth

from data_forge.context.context import Context
from data_forge.pipeline.pipeline import Pipeline

from data_forge.db_services.target import TargetDW
from data_forge.db_services.source import SourceDB
from data_forge.logging.watermark import Watermark

from data_forge.sales_force.sales_force import SalesForce
from data_forge.FileStorage.FileStorage import FileStorage
from data_forge.sales_force.sf_request import SalesForceRequest


@dataclass
class Builder:
    config_folder_path: Path

    def context(self):
        return Context.load_context(folder_path=self.config_folder_path)

    def auth(self):
        salesforce_config = self.context().salesforce_config
        return Auth(
            client_id=salesforce_config.get_client_id(),
            client_secret=salesforce_config.get_client_secret(),
            grant_type=salesforce_config.get_grant_type(),
            base_url=salesforce_config.get_base_url()
        )

    def source_db(self, db_name: str, source: str):
        return SourceDB(
            catalog=self.context().get_catalog(source=source),
            db_engine=self.engine(db_name=db_name)
        )

    def target_dw(self, db_name: str):
        return TargetDW(
            db_engine=self.engine(db_name=db_name)
        )

    def pipeline(self):
        return Pipeline(
            edi=self.target_dw(db_name="erae"),
            erp=self.source_db(db_name="erp", source="erp"),
            ops=self.source_db(db_name="ops", source="ops"),
            sales_force=self.salesforce(),
            watermarks=self.watermark(),
            run_datetime=datetime.now()
        )

    def salesforce(self):
        return SalesForce(
            catalog=self.context().get_catalog(source="crm"),
            file_storage=self.file_storage(),
            sf_request=self.sales_force_request()
        )

    def file_storage(self):
        pipeline_config = self.context().pipeline_config
        return FileStorage(
            export_path=pipeline_config.get_export_path(),
            chunk_size=pipeline_config.get_chunk_size()
        )

    def sales_force_request(self):
        return SalesForceRequest(
            auth=self.auth()
        )

    def watermark(self):
        pipeline_config = self.context().pipeline_config
        return Watermark.fetch_watermarks(
                self.target_dw(db_name="erae").db_engine,
                wm_table_schema=pipeline_config.watermark_table_schema,
                wm_table_name=pipeline_config.watermark_table_name
        )

    def engine(self, db_name):
        return self.context().get_engine(db_name=db_name)
