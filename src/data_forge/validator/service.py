from dataclasses import dataclass

from data_forge.context.models import Table, Catalog
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.validator.models import ValidationResult
from data_forge.validator.reporter import ValidationReporter
from data_forge.validator.validations import TableValidation


@dataclass
class Validator:
    source: SourceInterface
    target: TargetInterface
    table_validation: TableValidation

    def validate_catalog(self, catalog: Catalog, report: bool = False) -> dict[str, ValidationResult]:
        validation_results = {
            table_name: self.validate_table(table=table_obj)
            for table_name, table_obj in catalog.tables.items()
        }

        if report:
            ValidationReporter.print_results(results=validation_results)

        return validation_results

    def validate_table(self, table: Table, report: bool = False) -> ValidationResult:
        validation_result = ValidationResult(
            source=self.table_validation.validate_in_target(table=table),
            target=self.table_validation.validate_in_src(table=table),
            watermark=self.table_validation.validate_watermark(table=table)
        )

        if report:
            ValidationReporter.print_result(results=validation_result)

        return validation_result
