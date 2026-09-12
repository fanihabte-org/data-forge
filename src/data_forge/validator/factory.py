from dataclasses import dataclass

from data_forge.context.models import Table
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface

from data_forge.validator.validations import TableValidation, TableWatermarkValidation


@dataclass
class ValidatorFactory:
    source: SourceInterface
    target: TargetInterface

    def build_source_table_validation(self, table: Table):
        return TableValidation(table=table, interface=self.source)

    def build_target_table_validation(self, table: Table):
        return TableValidation(table=table, interface=self.target)

    def build_watermark_validation(self, table: Table):
        return TableWatermarkValidation(table=table, interface=self.target)
