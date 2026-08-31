from dataclasses import dataclass

from data_forge.context.models import Table, Catalog
from data_forge.validator.factory import ValidatorFactory
from data_forge.validator.models import WatermarkValidationResult, TableValidationResult, ValidationResult
from data_forge.validator.reporter import ValidationReporter


@dataclass
class Validator:
    validator_factory: ValidatorFactory

    def validate_catalog(self, catalog: Catalog, report: bool = False) -> dict[str, ValidationResult]:
        validation_results = {
            table_name: self.validate_table(table=table_obj)
            for table_name, table_obj in catalog.tables.items()
        }

        if report:
            ValidationReporter.print_results(results=validation_results)

        return  validation_results

    def validate_table(self, table: Table, report: bool = False) -> ValidationResult:
        validation_result = ValidationResult(
            source=self.check_in_src(table=table),
            target=self.check_in_target(table=table),
            watermark=self.check_watermark(table=table)
        )

        if report:
            ValidationReporter.print_result(results=validation_result)

        return validation_result

    def check_in_src(self, table: Table) -> TableValidationResult:
        return self.validator_factory.build_src_table_validation(table=table).execute()

    def check_in_target(self, table: Table) -> TableValidationResult:
        return self.validator_factory.build_target_table_validation(table=table).execute()

    def check_watermark(self, table: Table) -> WatermarkValidationResult:
        return self.validator_factory.build_watermark_validation(table=table).execute()
