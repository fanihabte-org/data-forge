from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from data_forge.planner.planner import Planner

if TYPE_CHECKING:
    from data_forge.db_services.source import SourceDB
    from data_forge.db_services.target import TargetDW


@dataclass
class Pipeline:
    source_db: SourceDB
    target_dw: TargetDW
    planner: Planner

    def run(self):
        plans = self.planner.build_plan()

        for table_name, plan in plans.items():
            print("\n Table: ", table_name)
            print(" Plan type: ", plan.execution_type)
            plan.execute()
