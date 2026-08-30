from dataclasses import dataclass

from data_forge.context.context import Catalog
from data_forge.validator.factory import ValidatorFactory
from data_forge.validator.models import WatermarkValidationResult, TableValidationResult
from data_forge.validator.reporter import ValidationReporter


@dataclass
class Validator:
    validator_factory: ValidatorFactory
    catalog: Catalog

    def run_checks(self) -> dict[str, dict[str, TableValidationResult]]:
        results = {
            "source": self.check_catalog_in_src(),
            "target": self.check_catalog_in_target()
        }

        ValidationReporter.print_result(results=results)
        return results

    def check_catalog_in_src(self) -> dict[str, TableValidationResult]:
        return {
            table_name: self.validator_factory.build_src_table_validation(table=table_obj).execute()
            for table_name, table_obj in self.catalog.tables
        }

    def check_catalog_in_target(self) -> dict[str, TableValidationResult]:
        return {
            table_name: self.validator_factory.build_target_table_validation(table=table_obj).execute()
            for table_name, table_obj in self.catalog.tables
        }

    def run_watermark_checks(self) -> dict[str, WatermarkValidationResult]:
        results = {
            table_name: self.validator_factory.build_watermark_validation(table=table_obj).execute()
            for table_name, table_obj in self.catalog.tables.items()
        }

        ValidationReporter.print_watermark_result(results=results)
        return results
