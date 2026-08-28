from dataclasses import dataclass

from data_forge.context.context import Catalog
from data_forge.db_engine.engine import DBEngine
from data_forge.planner.factory import PipelineStepFactory
from data_forge.validator.models import TableValidation
from data_forge.validator.reporter import ValidationReporter


@dataclass
class Validator:
    pipline_factory: PipelineStepFactory
    db_engine: DBEngine
    catalog: Catalog

    def run_src_table_checks(self) -> dict[str, TableValidation]:
        result = {
            table_name: self.pipline_factory.build_src_table_validation(table=table_obj)
            for table_name, table_obj in self.catalog.tables
        }
        ValidationReporter.print_result(result=result)

        return result

    def run_target_table_checks(self) -> dict[str, TableValidation]:
        result = {
            table_name: self.pipline_factory.build_target_table_validation(table=table_obj)
            for table_name, table_obj in self.catalog.tables
        }
        ValidationReporter.print_result(result=result)
        return result
