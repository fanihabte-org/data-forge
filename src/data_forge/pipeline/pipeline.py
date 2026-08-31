from __future__ import annotations

from dataclasses import dataclass

from data_forge.analyzer.analysis import VolumeAnalysis
from data_forge.analyzer.analyzer import Analyzer
from data_forge.planner.planner import Planner
from data_forge.resolver.resolver import Resolver
from data_forge.validator.validator import Validator
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW


@dataclass
class Pipeline:
    source_db: SourceDB
    target_dw: TargetDW
    planner: Planner
    validator: Validator
    resolver: Resolver
    analyzer: Analyzer

    @property
    def catalog(self):
        return self.source_db.catalog

    @property
    def source_name(self):
        return self.catalog.source_name

    def run(self):
        self.validate_and_resolve()
        for table_name, plan in self.plan().items():
            plan.execute()

    def plan(self):
        return self.planner.build_catalog_plan(
            catalog=self.source_db.catalog,
            volume_analyses=self.analyze(),
            report=True
        )

    def validate_and_resolve(self):
        validation_results = self.validator.validate_catalog(catalog=self.catalog, report=True)

        for table_name, validation in validation_results.items():
            if not validation.source.exists:
                raise RuntimeError(f"Table: {table_name} doesn't exist in the {self.source_name.upper()}")

            with self.target_dw.db_engine.build_connection() as conn:
                if not validation.target.exists:
                    self.resolver.create_table(
                        table=self.catalog.get_table(table_name=table_name),
                        report=True,
                        conn=conn
                    )

                self.resolver.sync_watermark(
                    table=self.catalog.get_table(table_name=table_name),
                    report=True,
                    conn=conn
                )

    def analyze(self) -> dict[str, VolumeAnalysis]:
        with self.source_db.db_engine.build_connection() as conn:
            return self.analyzer.analyze_catalog(
                catalog=self.source_db.catalog,
                conn=conn,
                report=True
            )
