from __future__ import annotations

from dataclasses import dataclass

from data_forge.context.models import Catalog
from data_forge.contracts.source_interface import SourceInterface
from data_forge.contracts.target_interface import TargetInterface
from data_forge.planner.plans import Plan
from data_forge.planner.service import Planner
from data_forge.analyzer.service import Analyzer
from data_forge.resolver.resolver import Resolver
from data_forge.validator.models import ValidationResult
from data_forge.validator.service import Validator
from data_forge.analyzer.models import VolumeAnalysis


@dataclass
class Pipeline:
    source: SourceInterface
    target: TargetInterface
    catalog: Catalog
    planner: Planner
    validator: Validator
    resolver: Resolver
    analyzer: Analyzer

    @property
    def source_name(self):
        return self.catalog.source_name

    def validate(self) -> dict[str, ValidationResult]:
        return self.validator.validate_catalog(catalog=self.catalog, report=True)

    def resolve(self, validation_results: dict[str, ValidationResult]) -> None:
        return self.resolver.resolve_catalog(
            validation_results=validation_results,
            catalog=self.catalog
        )

    def analyze(self) -> dict[str, VolumeAnalysis]:
        return self.analyzer.analyze_catalog(catalog=self.catalog, report=True)

    def plan(self, volume_analyses: dict[str, VolumeAnalysis]) -> dict[str, Plan]:
        return self.planner.build_catalog_plan(
            catalog=self.catalog,
            volume_analyses=volume_analyses,
            report=True
        )

    def run(self):
        self.resolve(validation_results=self.validate())
        plans = self.plan(volume_analyses=self.analyze())

        for table_name, plan in plans.items():
            plan.execute()
