from pathlib import Path

from datetime import datetime
from dataclasses import dataclass
from data_forge.sales_force.auth import Auth

from data_forge.context.context import Context
from data_forge.db_engine.engine import DBEngine
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
            client_id=salesforce_config.client_id,
            client_secret=salesforce_config.client_secret,
            grant_type=salesforce_config.grant_type,
            base_url=salesforce_config.base_url
        )

    def source_db(self, db_name: str, source: str):
        return SourceDB(
            context=self.context(),
            db_engine=self.engine(db_name=db_name),
            source=source
        )

    def target_dw(self, db_name: str, source: str):
        return TargetDW(
            context=self.context(),
            db_engine=self.engine(db_name=db_name),
            source=source
        )

    def pipeline(self):
        return Pipeline(
            context=self.context(),
            edi=self.target_dw(db_name="edi", source="edi"),
            erp=self.source_db(db_name="erp", source="erp"),
            ops=self.source_db(db_name="ops", source="ops"),
            sales_force=self.salesforce(),
            watermarks=self.watermark(),
            run_datetime=datetime.now()
        )

    def salesforce(self):
        return SalesForce(
            context=self.context(),
            source="crm",
            file_storage=self.file_storage(),
            sf_request=self.sales_force_request()
        )

    def file_storage(self):
        return FileStorage(
            context=self.context()
        )

    def sales_force_request(self):
        return SalesForceRequest(
            context=self.context(),
            auth=self.auth()
        )

    def watermark(self):
        return Watermark.load(self.target_dw(db_name="edi", source="edi"))

    def engine(self, db_name):
        return DBEngine.configure(self.context(), db_name)
