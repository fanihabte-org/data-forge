from dataclasses import dataclass

from data_forge.context.context import Catalog
from data_forge.resolver.resolver import Resolver
from data_forge.validator.factory import ValidatorFactory
from data_forge.validator.models import WatermarkValidationResult, TableValidationResult, \
    WatermarkValidationResultResolved
from data_forge.validator.reporter import ValidationReporter


@dataclass
class Validator:
    validator_factory: ValidatorFactory
    catalog: Catalog
    resolver: Resolver

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
            for table_name, table_obj in self.catalog.tables.items()
        }

    def check_catalog_in_target(self) -> dict[str, TableValidationResult]:
        return {
            table_name: self.validator_factory.build_target_table_validation(table=table_obj).execute()
            for table_name, table_obj in self.catalog.tables.items()
        }


    def run_watermark_checks(self) -> dict[str, WatermarkValidationResult]:
        wm_validation_results = {}

        for table_name, table_obj in self.catalog.tables.items():
            watermark_validation_result = self.validator_factory.build_watermark_validation(table=table_obj).execute()
            if not watermark_validation_result.exist:
                watermark_resolution = self.resolver.sync_watermark(table=table_obj)
                wm_validation_results[table_name] = WatermarkValidationResultResolved(
                    exist=False,
                    watermark=None,
                    resolved=True,
                    table=table_obj,
                    resolution_type=watermark_resolution.resolution_type,
                    synced_watermark=watermark_resolution.synced_watermark
                )
            else:
                wm_validation_results[table_name] = watermark_validation_result

        ValidationReporter.print_watermark_result(results=wm_validation_results)
        return wm_validation_results
